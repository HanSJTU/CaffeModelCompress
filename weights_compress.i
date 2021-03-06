%module weights_quantization
%{
    #include <Python.h>
    #include "numpy/arrayobject.h"
    void compress_layer_weights(PyObject *pComprsLabel, PyObject *pCodeBook, PyObject *pWeights, int nWeight, int nBit);
    void decompress_layer_weights(PyObject *pWeights, PyObject *pComprsLabel, PyObject *pCodeBook, int nWeight, int nBit);
    void quantize_layer_weights(PyObject *pWeights, int nWeight, int nBit);
    void quantize_buffer(PyObject *pWeights, PyObject * newWeights, int nWeight, PyObject * scale);
    void dequantize_buffer(PyObject *pWeights, PyObject * newWeights, int nWeight, PyObject * scale);
    void quantize_buffer_maxmin(PyObject *pWeights, PyObject * newWeights, int nWeight, int nSeg, PyObject * maxmin);
    void dequantize_buffer_maxmin(PyObject *pWeights, PyObject * newWeights, int nWeight, int nSeg,PyObject * maxmin);
%}
    #include <Python.h>
    #include "numpy/arrayobject.h"
    void compress_layer_weights(PyObject *pComprsLabel, PyObject *pCodeBook, PyObject *pWeights, int nWeight, int nBit);
    void decompress_layer_weights(PyObject *pWeights, PyObject *pComprsLabel, PyObject *pCodeBook, int nWeight, int nBit);
    void quantize_layer_weights(PyObject *pWeights, int nWeight, int nBit);
    void quantize_buffer(PyObject *pWeights, PyObject * newWeights, int nWeight, PyObject * scale);
    void dequantize_buffer(PyObject *pWeights, PyObject * newWeights, int nWeight, PyObject * scale);
    void quantize_buffer_maxmin(PyObject *pWeights, PyObject * newWeights, int nWeight, int nSeg, PyObject * maxmin);
    void dequantize_buffer_maxmin(PyObject *pWeights, PyObject * newWeights, int nWeight, int nSeg,PyObject * maxmin);
