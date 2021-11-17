import jetson.inference
import jetson.utils
import socket
import time
import os.path
import argparse
import sys
import os

# parse the command line
parser = argparse.ArgumentParser(description="Classify a live camera stream using an image recognition DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.imageNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())
# Load network
parser.add_argument("--network", type=str, default="googlenet", help="pre-trained model to load (see below for options)")

try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)
# load the recognition network
net = jetson.inference.imageNet(opt.network, sys.argv)
font = jetson.utils.cudaFont()

AI_FUNCTION_CODE_NONE = '00'
AI_FUNCTION_CODE_START = '51'
AI_FUNCTION_CODE_RESUME = '52'
AI_FUNCTION_CODE_SUSPEND = '53'
AI_FUNCTION_CODE_STOP = '54'
AI_FUNCTION_CODE_CANCEL = '55'
AI_FUNCTION_CODE_EMERGENCY_STOP = '56'
AI_FUNCTION_CODE_REQUEST_INFORMATION = '57'
AI_FUNCTION_CODE_ENVIRONMENT_REQUEST = '58'
AI_FUNCTION_CODE_ENVIRONMENT_SET = '59'
AI_FUNCTION_CODE_CONFIRM_FILE_TRANSFER = '5a'
AI_FUNCTION_CODE_ERROR_REPORT = '5b'
AI_FUNCTION_CODE_SYNC_CHECK = '5c'

#######################  Main Processing steps ######################################
# This code made by IEDSP Lab Chonnam National University
# /Address Code - 1/ Function code - 1/ data -n / CRC - 2/
# 1. Network sync check - 0x5C
# 	- Response to client about network state (0x5C)
#	- Send error or no error message
# 2. Receive request from client and processing request.
# a) Normal request: 0x51->0x55. Responding with structure:
#	- Responding message	(2 - 0x5...)
#	- Send error or no error message (2 - 0xD...)
# b) Request 0x57 about classify result. Responding:
#	- Responding: 0x57 to client from server: Send classify result
#	- Receive message: 0x57 - Received data is ok
# 	- Error (2 - 0xD7) 
# 3) Request 0x58: Environment set (request)
#	- Responding environent is ready (2 - 0x58)
#	- Responding about environment error (2 - 0xD8)
# 4) Request 0x59: Environment set (set)
#	- Responding environment is ready (2 - 0x59)
#	- Responding enfironment error (2 - 0xD9)
#	* If environment ready: 
#		+ Decode file name and file size
#		+ Receive file and save
#		+ Response receive data ok
#		+ Request 0x5A: Confirm file transfer
#			- Response receive ok (2 - 0x5A)
#			- Response receive error (2 - 0xDA )
# 5) Request report error if any error occur
#	- Response error message with error code
#########################################################################

def processFunction(receive_data):
	print('----Received data: ' + str(receive_data))
	address_code = receive_data[0:3] # 0x01
	function_code = receive_data[4:7] # 
	crc_high = receive_data[8]
	crc_low = receive_data[9]
	print('Function code: ' + str(function_code))

def AI_classification():	
	# Load Image
	measure
	img = jetson.utils.loadImage('0039.jpg')
	CHECK TYPE(IMG) 
	measure
	# classify the image
	class_id, confidence = net.Classify(img)
	# find the object description
	class_desc = net.GetClassDesc(class_id)
	# overlay the result on the image	
	font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 5, 5, font.White, font.Gray40)
	# Save output image
	jetson.utils.saveImage('0039_out.jpg',img)
	print('Network name: '+ net.GetNetworkName())
	print('Network speed: '+ str(net.GetNetworkFPS()))
	net.PrintProfilerTimes()
	return class_id

# hex: .decode('hex'); .encode('hex') ; string: .decode('utf-8') .encode()
def main():
	HOST = '192.168.1.78'
	#HOST = '192.168.1.82'
	PORT = 8083
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# Setting socket
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print('Socket created')
	s.bind((HOST, PORT))
	print('Socket bind complete')
	s.listen(1)
	print('Socket now listening')
	# check network sync
	conn, addr = s.accept()
	print("connect from: ", addr)

	# Receive request from client 
	while True:		
		# Receive data from client
		receive_data = conn.recv(4096) 
		print('Receive data from Client: ', receive_data)		
		receive_data_1 = receive_data
		receive_data_2 = receive_data
		# encode hex data
		receive_data = receive_data_1.encode('hex')
		
		address_code = receive_data[0:2]
		function_code = receive_data[2:4] # 
		length_data = receive_data[4:6]
		# data info only use when request file from PLC
		data_info = receive_data_2[3:-2]
		crc_high = receive_data[-4:-2]
		crc_low = receive_data[-2:]
		i=1
		print('Function code: '+function_code)
		if i==1:
			# Check network sync
			if (function_code == AI_FUNCTION_CODE_SYNC_CHECK):
				print('Receive ok')
				sendBuf = '01' + function_code + length_data + crc_high + crc_low
				#print(sendBuf)
				conn.send(sendBuf.decode('hex'))
				
			# check start status and classify result		
			if (function_code == AI_FUNCTION_CODE_START or function_code == AI_FUNCTION_CODE_RESUME or function_code == AI_FUNCTION_CODE_SUSPEND or function_code == AI_FUNCTION_CODE_STOP or function_code == AI_FUNCTION_CODE_CANCEL): # 0x51-0x55 start code
				print('Receive data from Client: ', receive_data)
				sendBuf = '01' + function_code + length_data + crc_high + crc_low
				print('Response data to PLC Client: ', sendBuf)
				conn.send(sendBuf.decode('hex'))
				
				length_data = '01'
				# AI prediction in here
				#AI_result = '01'
				AI_result = AI_classification()
				AI_result = '0' + str(AI_result)
				#AI finish
				# request information from AI to PLC
				function_code = AI_FUNCTION_CODE_REQUEST_INFORMATION
				sendBuf = '01' + AI_FUNCTION_CODE_REQUEST_INFORMATION +length_data + AI_result + crc_high + crc_low
				sendBuf.strip()
				#print('----------sendBuf 57: ' + sendBuf)
				
				conn.send(sendBuf.decode('hex')) # 0x57
				
				# read response
				receive_data = conn.recv(4096) 
				receive_data = receive_data.encode('hex')
				print(' ---Receive data from Client: ', receive_data)
				address_code = receive_data[0:2] # 0x01
				function_code = receive_data[2:4] #
				
			# Request environment
			if (function_code == AI_FUNCTION_CODE_ENVIRONMENT_REQUEST): # 0x58.
				# send answer
				model_old_name = 'MODEL001.onnx' # list models name from model folder
				sendBuf = '01' + function_code + length_data + model_old_name +crc_high + crc_low	
				conn.send(sendBuf.decode('hex'))				
			if (function_code == AI_FUNCTION_CODE_ENVIRONMENT_SET): # (0x59) 
				print(' ---Receive data from Client: ', receive_data)
				print(' ---Receive data from Client - data name and size: ', data_info)
				data_name_1 = data_info.split(":")
				print('data name: ' + data_name_1[0])
				print('data size: ' + data_name_1[1])
				dataSize = data_name_1[1]
				dataName = data_name_1[0]
				#crc_high = receive_data[10]
				#crc_low = receive_data[11]
				sendBuf = '01' + function_code + length_data + crc_high + crc_low
				# send response: Environment is ready
				conn.send(sendBuf.decode('hex'))
	
				# Receive data file
				print('--------Data size: ', dataSize)
				base_name = dataName
				myfile = open(base_name, 'wb')
				e = 0
				txt = dataSize
				if not txt:
					print('Empty string')
				else:
					size_data = int(txt)
					while e < size_data:
						d = conn.recv(4096)
						e += len(d)
		        			#print (len(d))
		      				print ('Receive data: ', e)
						myfile.write(d)
					myfile.close()
					print ('Receive data ok')

				# Confirm receive data message(0x5a)
				function_code = AI_FUNCTION_CODE_CONFIRM_FILE_TRANSFER
				sendBuf = '01' + function_code + length_data + crc_high + crc_low
				# send confirm message: 
				conn.send(sendBuf.decode('hex'))

				
				
if __name__ == '__main__':
	main()
	





	


