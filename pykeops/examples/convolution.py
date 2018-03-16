import os.path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + (os.path.sep + '..')*2)

import numpy as np
from pykeops.numpy.convolutions.radial_kernels import radial_kernels_conv

import time, timeit

N = 2000 ; M = 300; D = 3; E = 3

# declare numpy 
x = np.random.randn(N,D).astype('float32')
y = np.random.randn(M,D).astype('float32')
b = np.random.randn(M,E).astype('float32')
s = np.array([2.4]).astype('float32')

def np_kernel(x, y, s, kernel) :
    sq = np.sum( (x[:,np.newaxis,:] - y[np.newaxis,:,:]) **2, axis=2)
    if   kernel == "gaussian"  : return np.exp( -sq / (s*s))
    elif kernel == "laplacian" : return np.exp( -np.sqrt(sq + s*s))
    elif kernel == "energy"    : return 1. / ( s*s + sq ) **.25 

# declare the torch counterpart
try:
    import torch

    xc = torch.from_numpy(x.copy()).cuda()
    yc = torch.from_numpy(y.copy()).cuda()
    bc = torch.from_numpy(b.copy()).cuda()
    sc = torch.from_numpy(s.copy()).cuda()

    def torch_kernel(x, y, s, kernel) :
        sq = torch.sum( (x[:,None]-y[None])**2 , 2 ) 
        if   kernel == "gaussian"  : return torch.exp( -sq / (s*s))
        elif kernel == "laplacian" : return torch.exp( -torch.sqrt(sq + s*s))
        elif kernel == "energy"    : return torch.pow( 1. / ( s*s + sq ), .25 )
except:
    pass

##############################
# Benchmark
##############################

enable_GC = False # Garbage collection?
GC = 'gc.enable();' if enable_GC else 'pass;'
LOOPS = 200
print("Time to compute ", LOOPS, " convolutions of size {}x{}:".format(N,M))
print("\n",end="")

for k in (["gaussian", "laplacian", "energy"]):
    print(k, " kernel:")

    # cuda pytorch
    try:
        g0 = torch.mm(torch_kernel(xc,yc,sc,kernel=k),bc)#.cpu().numpy()
        speed_pytorch = timeit.Timer('g0 = torch.mm(torch_kernel(xc,yc,sc,kernel=k),bc)#.cpu().numpy()', GC, globals = globals(), timer = time.time).timeit(LOOPS)
        print("Time for Pytorch/cuda: {:.4f}s".format(speed_pytorch))
    except:
        pass

    # cuda tiled implementation
    g1 = np.zeros([N,E]).astype('float32') ; radial_kernels_conv(x, y, b, g1, s, kernel=k)
    g1 = np.zeros([N,E]).astype('float32')
    speed_pykeops = timeit.Timer('radial_kernels_conv(x, y, b, g1, s, kernel=k)', GC, globals = globals(), timer = time.time).timeit(LOOPS)
    print("Time for cuda:         {:.4f}s".format(speed_pykeops))


    # pure numpy
    g2 =  np_kernel(x,y,s,kernel=k) @ b
    speed_numpy = timeit.Timer('g2 =  np_kernel(x,y,s,kernel=k) @ b', 
            GC, globals = globals(),
            timer = time.time).timeit(LOOPS)
    print("Time for Python:       {:.4f}s".format(speed_numpy))
    print("Absolute error:       ", np.max(np.abs (g1 - g2)), "\n")
