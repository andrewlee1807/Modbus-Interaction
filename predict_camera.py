import cv2
from officialCodeCrop import *

import jetson.inference
import jetson.utils

import argparse
import sys
import os

import time

##run command: python predict_time.py --model=resnet-exp1/resnet18.onnx --input_blob=input_0 --output_blob=output_0 --labels=labels.txt
# parse the command line
parser = argparse.ArgumentParser(description="Classify a live camera stream using an image recognition DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.imageNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())
# Load network
parser.add_argument("--network", type=str, default="googlenet", help="pre-trained model to load (see below for options)")


def classify(numpy_img, jeston_model):
	"""
	input: numpy_img = image in numpy array fomart
	       jeston_model = jetson nano deep learning model (loar from jetson.Imagenet)
	output:
			class_id = defective = 0/ positive = 1
			confidence = probability of deep learning model
	"""
	
	# open_cv_image = numpy_img[:, :, ::-1].copy() #convert to opencv image 
	open_cv_image = numpy_img #use original numpy_img

	t = time.time()

	"""preprocessing"""
	c = apple_detect(open_cv_image) #detect apple in image
	if (c.size != 0):
		c = cv2.cvtColor(c, cv2.COLOR_BGR2RGB) #convert to RGB order
		img = jetson.utils.cudaFromNumpy(c) #convert image from numpy
	else:
		print('Apple is not detected!')
		return -1, 0.0
	#finish preprocessing

	print("Time to load image (+preprocessing) from local to JETSON.CUDA: ", time.time()-t)
	
	# classify the image
	t = time.time()
	class_id, confidence = jeston_model.Classify(img) 
	print("Time to Classify: ", time.time()-t)
	return class_id, confidence 


try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)
# load the recognition network
print(sys.argv)
net = jetson.inference.imageNet("", sys.argv)
font = jetson.utils.cudaFont()

print(sys.argv)

# Old dataset

#  New Dataset
root_dir = 'data/'
input_dir = ['defective', 'ok']
output_dir = ['defective_out', 'ok_out']

true_positive = 0
true_negative = 0
false_positive = 0
false_negative = 0
f = open("output_result.txt", "a")

total_time_of_whole_process = 0


from pypylon import pylon
import platform
import time
t = time.time()
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
converter.OutputPixelFormat = pylon.PixelType_RGB8packed
cam_on_off = True
file_num = 0
while camera.IsGrabbing() and cam_on_off:
    start_an_img_work = time.time()
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    img_tiff = None
    if grabResult.GrabSucceeded():
        image = converter.Convert(grabResult)
        img = image.GetArray()
        
        I = img
        class_id, confidence = classify(numpy_img=I, jeston_model=net)

        # find the object description
        t = time.time()
        class_desc = net.GetClassDesc(class_id)
        print("Time to find the object description: ", time.time()- t)

        string_write = str(class_id) +"  " + class_desc+ "  " +str("{:.2f}".format(confidence * 100))
        # f.write(string_write + "\r\n")	
        print(string_write)

        # overlay the result on the image
        t= time.time()	
        # font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 5, 5, font.White, font.Gray40)
        print("Time to overlay the result on the image: ", time.time()- t)
        # Save output image
        # t = time.time()
        # jetson.utils.saveImage(net_output_dir,img)
        # print("Time to Save output image: ", time.time()- t)    

        # print out performance info
        net.PrintProfilerTimes()
        total_time_of_a_process = time.time()-start_an_img_work
        total_time_of_whole_process += total_time_of_a_process
        print("Total time to process an image: ", total_time_of_a_process)
        print('Network name: '+ net.GetNetworkName())
        print('Network speed: '+ str(net.GetNetworkFPS()))
        print("\n\n")
f.close()
print("       ----------------------------------------        ")
print("                    FINAL RESULTS")
print("       ----------------------------------------        ")
print("       True positive images  : " + str(true_positive))
print("       False negative images : " + str(false_negative))
print("       True negative images  : " + str(true_negative))
print("       False positive images : " + str(false_positive))

final_accuracy = float(true_positive + true_negative)*100/(true_negative + false_positive + true_positive + false_negative + 0.001)

final_precision = float(true_positive)*100/(false_positive + true_positive + 0.001)

final_recall = float(true_positive)*100/(true_positive + false_negative)
print("       Accuracy              :" + "{:.2f}".format(final_accuracy) + " %") 
print("       Precision             :" + "{:.2f}".format(final_precision) + " %") 
print("       Recall                :" + "{:.2f}".format(final_recall) + " %") 
print("       ----------------------------------------        ")
print("AVG time to process an image: ", total_time_of_a_process/len(input_dir))



	


