# coding: utf-8

import os
import cv2
import numpy as np
import caffe
from configobj import ConfigObj 
import sys
sys.path.append("..")
from common.utils import BBox, drawLandmark, check_bbox, processImage
from common.get_data import getDataFromTXT, load_celeba_data, get_train_val_test_list, getDataFromTXT_68

class Predict(object):
	def __init__(self, net, model):
		self.net = net
		self.model = model
		self.cnn = caffe.Net(str(net), str(model), caffe.TEST)

	def forward(self, face, layer='fc2'):
		'''
		face has been preprocessed to (1,C,H,W) before feeding to cnn.
		'''
		out = self.cnn.forward_all(data=np.asarray([face]))
		landmark = out[layer][0]
		landmark = landmark.reshape(68,2)

		return landmark

def load_test_img(gray, bbox):
	# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	face = gray[bbox.top:bbox.bottom, bbox.left:bbox.right]
	face = cv2.resize(face, (39,39)).reshape(1,1,39,39)
	face = processImage(np.asarray(face))

	return face

if __name__ == '__main__':
	config = ConfigObj('../config_300w.txt')
	test_file = config['test_file']
	test_dir_out = config['test_dir_out']
	if not os.path.exists(test_dir_out):
		os.mkdir(test_dir_out)

	net = Predict('../deploy_300w.prototxt', sys.argv[1])

	# Test for original dataset 
	if len(sys.argv) == 2:
		test_data = getDataFromTXT_68(test_file, test=True)
		for (img_path, bbox) in test_data:
                        # enlarge the bounding box
                        x_min=bbox.left
                        x_max=bbox.right
                        y_min=bbox.top
                        y_max=bbox.bottom
                        w, h = x_max-x_min, y_max-y_min
                        #w, h = bbox.right-bbox.left, bbox.bottom-bbox.top
                        w = h = min(w, h)
                        ratio = 0.5
                        x_new = x_min - w*ratio
                        y_new = y_min - h*ratio
                        w_new = w*(1 + 2*ratio)
                        h_new = h*(1 + 2*ratio)
                        bbox = map(int, [x_new, x_new+w_new, y_new, y_new+h_new])
                        bbox = BBox(bbox)


			img = cv2.imread(img_path)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                  	if not check_bbox(gray, bbox): 
			        print 'BBox out of range.'
			        continue
			
			print 'predicting %s' % img_path			
			face = load_test_img(gray, bbox)
			landmark = net.forward(face, 'fc2')
			landmark = bbox.reprojectLandmark(landmark)

			img = drawLandmark(img, bbox, landmark)
			fp = os.path.join(test_dir_out, os.path.basename(img_path))
			cv2.imwrite(fp, img)

	# Test for celeba dataset
	elif len(sys.argv) == 3 and sys.argv[2] == 'celeba':
		data = load_celeba_data()
		train, val, test = get_train_val_test_list()
		test_data = [data[i-1] for i in test]

		for (img_path, bbox, landmark_ground) in test_data:
			img = cv2.imread(img_path)
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			print 'predicting %s' % img_path
			if not check_bbox(gray, bbox):
				print 'BBox out of range...'
				continue
			face = load_test_img(gray, bbox)
			landmark = net.forward(face, 'fc2')
			landmark = bbox.reprojectLandmark(landmark)

			img = drawLandmark(img, bbox, landmark)
			fp = os.path.join(test_dir_out, os.path.basename(img_path))
			cv2.imwrite(fp, img)



