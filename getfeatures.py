import adaboosting as ada
import weaklearners as weak
import numpy as np
import timeit
# import thread
import threading
from multiprocessing import Process


savepath = "/Users/Shawn/cs276/"


class Combo():
	"""docstring for Combo"""
	def __init__(self,numfaces, numnonfaces, numfeatures, imgwidth=16):
		self.numfaces = numfaces
		self.numnonfaces = numnonfaces
		self.imgwidth = imgwidth
		self.numsamples_per_feature = numfeatures/6
		self.numfeatures = self.numsamples_per_feature*6
		self.lock = threading.Lock()

	def PrepareFeatures(self):
		faces = weak.Images("../newface"+str(self.imgwidth)+"/",isface=True, samplesize=self.numfaces, imgwidth=self.imgwidth)
		nonfaces = weak.Images("../nonface"+str(self.imgwidth)+"/",isface=False, samplesize=self.numnonfaces, imgwidth=self.imgwidth)

		# get the sum table for the images
		self.face_tables = faces.GetTables()
		self.nonface_tables = nonfaces.GetTables()
		
		#Generate the features
		featureGen = weak.Features(self.imgwidth)
		f1 = featureGen.rand_feature1(n=self.numsamples_per_feature, vertical=True)
		f2 = featureGen.rand_feature1(n=self.numsamples_per_feature, vertical=False)
		f3 = featureGen.rand_feature2(n=self.numsamples_per_feature, vertical=True)
		f4 = featureGen.rand_feature2(n=self.numsamples_per_feature,vertical=False)
		f5 = featureGen.rand_feature3(self.numsamples_per_feature)
		f6 = featureGen.rand_feature4(self.numsamples_per_feature)
		self.features = [f1, f2, f3, f4, f5, f6]

		## save all the features
		for i in range(6):
			np.savetxt(savepath+'feature_type_'+str(i+1)+'.csv', self.features[i] , delimiter=',',fmt='%d')

#	# type 0: fill the face table
#	# type 1-4: fill the nonface table part1-4

	def FillTable(self, ftype):
		train_scores = np.empty([self.numfaces+self.numnonfaces, self.numsamples_per_feature], dtype=int)
		self.lock.acquire()
		print "shape,", train_scores.shape
		self.lock.release()
		## fill the score tables
		for i in range(self.numfaces):
			curscore = weak.Scores(self.face_tables[i], features=self.features[ftype-1], ftype=ftype)
			train_scores[i]  = curscore.getScores()
			if i>=50 and i%50==0:
				self.lock.acquire()
				print "type"+str(ftype)+" completed", "{0:.1%}".format(float(i)/(self.numfaces+self.numnonfaces)), " out of", self.numfaces+self.numnonfaces
				self.lock.release()

		for i in range(self.numfaces,self.numfaces+self.numnonfaces):
			curscore = weak.Scores(self.nonface_tables[i-self.numfaces], features=self.features[ftype-1], ftype=ftype)
			train_scores[i]  = curscore.getScores()
			if i%50==0:
				self.lock.acquire()
				print "type"+str(ftype)+" completed", "{0:.1%}".format(float(i)/(self.numfaces+self.numnonfaces)), " out of", self.numfaces+self.numnonfaces
				self.lock.release()
		# save the results
		self.lock.acquire()
		print "\nSaving feature scores: type "+str(ftype)
		self.lock.release()
		np.save(savepath+'scores_feature_type'+str(ftype), train_scores)
		self.lock.acquire()
		print "Save Completed!"
		self.lock.release()



	# ada.adaboosting(np.concatenate((train_faces_scores, train_nonfaces_scores), axis=0),  np.concatenate((np.ones(numfaces), np.zeros(numnonfaces)), T=50)

## all the features are stored locally
## now given an index, return the cooresponding feature
def getFeature(i, numfeatures):
	numfeatures = (numfeatures/6)*6
	numsamples_per_feature = numfeatures/6
	position = i/numsamples_per_feature
	index = i%numsamples_per_feature
	feature_table = np.loadtxt('./data/feature_type_'+str(position)+'.csv', delimiter=',')
	return feature_table[index]



if __name__ == "__main__":
	start = timeit.default_timer()
	comb = Combo(numfaces=11838,numnonfaces=45356,numfeatures=12000, imgwidth=24)
	comb.PrepareFeatures()
	pros = []
	for i in range(1,7):
		p = Process(target=comb.FillTable, args=(i,))
		p.start()
		pros.append(p)
	# Wait for all processes to complete
	for p in pros:
	    p.join()
	# threads = []
	# for i in range(1,7):
	# 	t = threading.Thread(target=comb.FillTable, args=(i,))
	# 	t.start()
	# 	threads.append(t)
	# # Wait for all threads to complete
	# for t in threads:
	#     t.join()
	stop = timeit.default_timer()
	print "Time Used,", round(stop - start, 4)