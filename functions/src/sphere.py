# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 22:15:10 2020

@author: sbamford

Create a big sphere from the bedrock up to the top of the world, 
centred around where you are
"""

#%% generate voxels

import numpy as np
from os.path import join, dirname, abspath

def generateVoxels():
     voxels = []
     step = 0.1
     for azimuth in np.arange(-np.pi, np.pi, step):
         for elevation in np.arange(-np.pi, np.pi, step):
             x = np.sin(azimuth) * np.cos(elevation)
             y = np.cos(azimuth) * np.cos(elevation)
             z = np.sin(elevation)
             voxels.append([x, y, z])
     voxelsArray = np.array(voxels)
     voxelsArray = voxelsArray * 128
     voxelsArray = voxelsArray.astype(np.int16)
     voxelsArray[:,2] = voxelsArray[:,2] + 128
     return voxelsArray

#%% See the result in a plot

'''
Optional functionality for seeing the result in development;
imports are therefore optional - not part of dependencies

Invoke like this:
     
plot(generateVoxels())
'''

def plot(voxelsArray):
     import matplotlib.pyplot as plt
     from mpl_toolkits.mplot3d import Axes3D
     
     fig = plt.figure()
     ax = fig.add_subplot(111, projection='3d')
     ax.scatter(voxelsArray[:,0], voxelsArray[:,1], voxelsArray[:,2])
     ax.set_xlabel('X Label')
     ax.set_ylabel('Y Label')
     ax.set_zlabel('Z Label')
     plt.show()

#%% generate script

def generateScript(voxelsArray):
     with open(join(dirname(dirname(abspath(__file__))), \
                    join('example','sphere.mcfunction')), 'w') as file:
         
         for x, y, z in voxelsArray:
             x = str(x)
             y = str(y)
             z = str(z)
             string = 'fill ~'+x+' '+y+' ~'+z+' ~'+x+' '+y+' ~'+z+' glass\n'
             file.write(string)
    
if __name__ == "__main__":     
     generateScript(generateVoxels())

