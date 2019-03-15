"""
Softmax reduction (numpy)
=========================
"""

###############################################################################
# The following operation is implemented:
# 
# * inputs: 
#     
#     - :math:`x` array of size :math:`M\times 3` representing :math:`M` vectors in :math:`\mathbb R^3`
#     - :math:`y` array of size :math:`N\times 3` representing :math:`N` vectors in :math:`\mathbb R^3`
#     - :math:`b` array of size :math:`N\times 2` representing :math:`N` vectors in :math:`\mathbb R^2`
# 
# * output:
#     
#     - :math:`z` array of size :math:`M\times 2` representing :math:`M` vectors in :math:`\mathbb R^2` where
#       .. math::
#         
#           z_i = \sum_j \exp(K(x_i,y_j))b_j / \sum_j \exp(K(x_i,y_j))
#       
#       with :math:`K(x_i,y_j) = |x_i-y_j|^2`.
#
# This example uses the Numpy bindings

###############################################################################
# Standard imports
# ----------------

import time
import numpy as np
from pykeops.numpy import Genred

###############################################################################
# Define our dataset
# ------------------

M = 500
N = 400
D = 3
Dv = 2

x = 2*np.random.randn(M,D)
y = 2*np.random.randn(N,D)
b = np.random.rand(N,Dv)

###############################################################################
# Kernel
# ------

formula = 'SqDist(x,y)'
formula_weights = 'b'
aliases = ['x = Vx('+str(D)+')',  # First arg   : i-variable, of size D
             'y = Vy('+str(D)+')',  # Second arg  : j-variable, of size D
             'b = Vy('+str(Dv)+')'] # third arg : j-variable, of size Dv

softmax_op = Genred(formula, aliases, reduction_op='SoftMax', axis=1, formula2=formula_weights)

start = time.time()
c = softmax_op(x, y, b)
print("Time to compute the softmax operation (KeOps implementation): ",round(time.time()-start,5),"s")

# compare with direct implementation
start = time.time()
cc = np.sum((x[:,None,:]-y[None,:,:])**2,axis=2)
cc -= np.max(cc,axis=1)[:,None] # subtract the max for robustness
cc = np.exp(cc)@b/np.sum(np.exp(cc),axis=1)[:,None]
print("Time to compute the softmax operation (direct implementation): ",round(time.time()-start,5),"s")

print("relative error : ", (np.linalg.norm(c-cc)/np.linalg.norm(c)).item())
