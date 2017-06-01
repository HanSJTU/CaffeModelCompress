import os 
import sys

import caffe 
import numpy as np
from math import ceil
#from quantz_kit.weights_quantization import weights_quantization
sys.path.append("./quantz_kit")
import weights_quantization as wqtz
import time

def caffe_model_compress_maxmin(model, weights, storefile, convbit=6, fcbit=2, use_savez_compressed=True):
	net = caffe.Net(model, caffe.TEST);
	net.copy_from(weights);

	xdict = dict()
	#version 1 ; bits of conv layer and bits of full-connected layer
	xdict['compz_info'] = (1, int(convbit), int(fcbit))
	
	for item in net.params.items():
		name, layer = item
		print "compressing layer", name
		
		weights = net.params[name][0].data
		bais    = net.params[name][1].data

		weights_vec = weights.flatten().astype(np.float32)
		vec_length = weights_vec.size
		newweights_vec=np.empty(vec_length,dtype=np.uint8)
		scale=np.empty(2,dtype=np.float32)

		Option = 1
		if Option == 1:
			nSeg=256
		elif Option == 2:
			if "fc" in name:
				nSeg = 4
			elif "conv" in name:
				nSeg = 64

		wqtz.quantize_buffer_maxmin(weights_vec,newweights_vec,vec_length,nSeg,scale)

		print "new weight size:\t",newweights_vec.size

		xdict[name+'_newweights'] = newweights_vec
		xdict[name+'_bias'] = bais
		xdict[name+'_scale']=scale
		#print "python scale",scale

	if (use_savez_compressed):
		np.savez_compressed(storefile, **xdict)
	else:
		np.savez(storefile, **xdict)


def caffe_model_decompress_maxmin(model, weights, loadfile):
	net = caffe.Net(model, caffe.TEST);
	cmpr_model = np.load(loadfile)
	
	print cmpr_model.files
	
	version, convbit, fcbit = cmpr_model['compz_info']
	
	assert(version == 1), "compz version not support"
	
	
	for item in net.params.items():
		name, layer = item
		#newlabels = cmpr_model[name+'_weight_labels']
		#codebook = cmpr_model[name+'_weight_codebook']
		newweights = cmpr_model[name+'_newweights']
		scale=cmpr_model[name+'_scale']
		origin_size = net.params[name][0].data.flatten().size
		calcu_weights=np.empty(origin_size, dtype=np.float32)

		nSeg=1024
		#if "fc" in name:
		#	nSeg = 4
		#elif "conv" in name:
		#	nSeg = 64

		wqtz.dequantize_buffer_maxmin(newweights,calcu_weights,origin_size,nSeg,scale)

		calcu_weights_shape=calcu_weights.reshape(net.params[name][0].data.shape)
		net.params[name][0].data[...] = calcu_weights_shape
		newbias = cmpr_model[name+'_bias']
		net.params[name][1].data[...] = newbias[...]
	net.save(weights)

def caffe_model_compress_int8(model, weights, storefile, convbit=6, fcbit=2, use_savez_compressed=True):
	net = caffe.Net(model, caffe.TEST);
	net.copy_from(weights);

	xdict = dict()
	#version 1 ; bits of conv layer and bits of full-connected layer
	xdict['compz_info'] = (1, int(convbit), int(fcbit))
	
	for item in net.params.items():
		name, layer = item
		print "compressing layer", name
		
		#compress weights
		weights = net.params[name][0].data
		#don't compress bais
		bais    = net.params[name][1].data
		
		#bits for conv and full-connected layer.
		if "fc" in name:
			nbit = int(fcbit)
		elif "conv" in name:
			nbit = int(convbit)

		weights_vec = weights.flatten().astype(np.float32)
		vec_length = weights_vec.size
		print "vec_length",vec_length
		newweights_vec=np.empty(vec_length,dtype=np.int8)
		scale=np.empty(1,dtype=np.int)
		wqtz.quantize_buffer(weights_vec,newweights_vec,vec_length,scale)

		#print "vec_length",vec_length
		#nelem = 32 / nbit
		#newlabel = np.empty(((vec_length+nelem-1)/nelem),dtype=np.int32) 
		#codebook_INT = np.empty((2**nbit),dtype=np.int8)
		#codebook = np.empty((2**nbit),dtype=np.float32)

		#t_start = time.time()
		#wqtz.compress_layer_weights(newlabel, codebook_INT, weights_vec, vec_length, nbit)
		#t_stop = time.time()
		#kmeans_time = kmeans_time + t_stop - t_start
				
		#xdict[name+'_weight_labels'] = newlabel
		#xdict[name+'_weight_codebook'] = codebook
		xdict[name+'_newweights'] = newweights_vec
		xdict[name+'_bias'] = bais
		xdict[name+'_scale']=scale
		print "python scale",scale

	#keep result into output file
	if (use_savez_compressed):
		np.savez_compressed(storefile, **xdict)
	else:
		np.savez(storefile, **xdict)


def caffe_model_decompress_int8(model, weights, loadfile):
	net = caffe.Net(model, caffe.TEST);
	cmpr_model = np.load(loadfile)
	
	print cmpr_model.files
	
	version, convbit, fcbit = cmpr_model['compz_info']
	
	assert(version == 1), "compz version not support"
	
	
	for item in net.params.items():
		name, layer = item
		#newlabels = cmpr_model[name+'_weight_labels']
		#codebook = cmpr_model[name+'_weight_codebook']
		newweights = cmpr_model[name+'_newweights']
		scale=cmpr_model[name+'_scale']
		origin_size = net.params[name][0].data.flatten().size
		calcu_weights=np.empty(origin_size, dtype=np.float32)
		wqtz.dequantize_buffer(newweights,calcu_weights,origin_size,scale)

		#origin_size = net.params[name][0].data.flatten().size
		#weights_vec = np.empty(origin_size, dtype=np.float32)
		#vec_length = weights_vec.size
		
		#need have a way to get bits for fc and conv
		if "fc" in name:
			nbit = fcbit
		elif "conv" in name:
			nbit = convbit

		#wqtz.decompress_layer_weights(weights_vec, newlabels, codebook, vec_length, nbit)
		#newweights = weights_vec.reshape(net.params[name][0].data.shape)
		#net.params[name][0].data[...] = newweights
		calcu_weights_shape=calcu_weights.reshape(net.params[name][0].data.shape)
		net.params[name][0].data[...] = calcu_weights_shape
		newbias = cmpr_model[name+'_bias']
		net.params[name][1].data[...] = newbias[...]
	net.save(weights)

def caffe_model_compress(model, weights, storefile, convbit=6, fcbit=2, use_savez_compressed=True):
	net = caffe.Net(model, caffe.TEST);
	net.copy_from(weights);

	xdict = dict()
	#version 1 ; bits of conv layer and bits of full-connected layer
	xdict['compz_info'] = (1, int(convbit), int(fcbit))
	
	for item in net.params.items():
		name, layer = item
		print "compressing layer", name
		
		#compress weights
		weights = net.params[name][0].data
		#don't compress bais
		bais    = net.params[name][1].data
		
		#bits for conv and full-connected layer.
		if "fc" in name:
			nbit = int(fcbit)
		elif "conv" in name:
			nbit = int(convbit)

		weights_vec = weights.flatten().astype(np.float32)
		vec_length = weights_vec.size
		#print "vec_length",vec_length
		nelem = 32 / nbit
		newlabel = np.empty(((vec_length+nelem-1)/nelem),dtype=np.int32) 
		#codebook_INT = np.empty((2**nbit),dtype=np.int8)
		codebook = np.empty((2**nbit),dtype=np.float32)

		#t_start = time.time()
		wqtz.compress_layer_weights(newlabel, codebook, weights_vec, vec_length, nbit)
		#t_stop = time.time()
		#kmeans_time = kmeans_time + t_stop - t_start
				
		xdict[name+'_weight_labels'] = newlabel
		xdict[name+'_weight_codebook'] = codebook
		xdict[name+'_bias'] = bais

	print "calculation is done."

	#keep result into output file
	if (use_savez_compressed):
		np.savez_compressed(storefile, **xdict)
	else:
		np.savez(storefile, **xdict)
	print "store is done."

	
def caffe_model_decompress(model, weights, loadfile):
	net = caffe.Net(model, caffe.TEST);
	cmpr_model = np.load(loadfile)
	
	print cmpr_model.files
	
	version, convbit, fcbit = cmpr_model['compz_info']
	
	assert(version == 1), "compz version not support"
	
	
	for item in net.params.items():
		name, layer = item
		newlabels = cmpr_model[name+'_weight_labels']
		codebook = cmpr_model[name+'_weight_codebook']

		origin_size = net.params[name][0].data.flatten().size
		weights_vec = np.empty(origin_size, dtype=np.float32)
		vec_length = weights_vec.size
		
		#need have a way to get bits for fc and conv
		if "fc" in name:
			nbit = fcbit
		elif "conv" in name:
			nbit = convbit

		wqtz.decompress_layer_weights(weights_vec, newlabels, codebook, vec_length, nbit)
		newweights = weights_vec.reshape(net.params[name][0].data.shape)
		net.params[name][0].data[...] = newweights

		newbias = cmpr_model[name+'_bias']
		net.params[name][1].data[...] = newbias[...]
	net.save(weights)

def compress_alex():
	LENET_PATH = "/home/intel/Downloads/caffe/models/bvlc_alexnet"

	netmodel   = os.path.join(LENET_PATH, "train_val.prototxt")
	netweights = os.path.join(LENET_PATH, "bvlc_alexnet.caffemodel")
	output = os.path.join(LENET_PATH,"alexnetzip.npz")


	new_weights=os.path.join(LENET_PATH,"alexnet_xx.caffemodel")

	Option = 1
	if Option == 1:
		caffe_model_compress(netmodel, netweights, output, 6, 2)
		#caffe_model_compress(netmodel, netweights, output, 8, 8)
		print "it seems that compress has finished"
		caffe_model_decompress(netmodel, new_weights, output)
	elif Option == 2:
		caffe_model_compress_int8(netmodel, netweights, output, 6, 2)
		caffe_model_decompress_int8(netmodel, new_weights, output)
	elif Option == 3:
		caffe_model_compress_maxmin(netmodel, netweights, output, 6, 2, True)
		caffe_model_decompress_maxmin(netmodel, new_weights, output)
	
	print "Done"


def compress_vgg_16():
	LENET_PATH = "/home/intel/Downloads/caffe/models/default_vgg_16"

	netmodel   = os.path.join(LENET_PATH, "train_val.prototxt")
	netweights = os.path.join(LENET_PATH, "VGG_ILSVRC_16_layers.caffemodel")
	output = os.path.join(LENET_PATH,"vgg16zip.npz")


	new_weights=os.path.join(LENET_PATH,"vgg16_xx.caffemodel")

	Option = 1
	if Option == 1:
		caffe_model_compress(netmodel, netweights, output, 6, 2)
		#caffe_model_compress(netmodel, netweights, output, 8, 8)
		print "it seems that compress has finished"
		caffe_model_decompress(netmodel, new_weights, output)
	elif Option == 2:
		caffe_model_compress_int8(netmodel, netweights, output, 6, 2)
		caffe_model_decompress_int8(netmodel, new_weights, output)
	elif Option == 3:
		caffe_model_compress_maxmin(netmodel, netweights, output, 6, 2, True)
		caffe_model_decompress_maxmin(netmodel, new_weights, output)
	
	print "Done"


def compress_vgg_19():
	LENET_PATH = "/home/intel/Downloads/caffe/models/vgg_19"

	netmodel   = os.path.join(LENET_PATH, "vgg19_real.prototxt")
	netweights = os.path.join(LENET_PATH, "vgg_19.caffemodel")
	output = os.path.join(LENET_PATH,"vgg19zip.npz")


	new_weights=os.path.join(LENET_PATH,"vgg19_xx.caffemodel")

	Option = 1
	if Option == 1:
		caffe_model_compress(netmodel, netweights, output, 6, 2)
		#caffe_model_compress(netmodel, netweights, output, 8, 8)
		print "it seems that compress has finished"
		caffe_model_decompress(netmodel, new_weights, output)
	elif Option == 2:
		caffe_model_compress_int8(netmodel, netweights, output, 6, 2)
		caffe_model_decompress_int8(netmodel, new_weights, output)
	elif Option == 3:
		caffe_model_compress_maxmin(netmodel, netweights, output, 6, 2, True)
		caffe_model_decompress_maxmin(netmodel, new_weights, output)
	
	print "Done"

if __name__ == "__main__":
	
	compress_vgg_19()

#if __name__ == "__main__":
#	
#	LENET_PATH = "/home/intel/Downloads/caffe/examples/mnist"
#
#	netmodel   = os.path.join(LENET_PATH, "lenet_train_test.prototxt")
#	netweights = os.path.join(LENET_PATH, "lenet_iter_10000.caffemodel")
#	output = os.path.join(LENET_PATH,"lenetzip.npz")
#	caffe_model_compress(netmodel, netweights, output, 6, 2)
#
#	new_weights=os.path.join(LENET_PATH,"lenet_xx.caffemodel")
#	caffe_model_decompress(netmodel, new_weights, output)
#	
#	print "Done"
