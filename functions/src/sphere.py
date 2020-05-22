# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 22:15:10 2020

@author: sbamford
"""

#%% generate voxels

import numpy as np

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

#%% See the result in a plot

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

with open(join(dirname(dirname(abspath(__file__))), \
               join('example','sphere.mcfunction')), 'w') as file:
    
    for x, y, z in voxelsArray:
        x = str(x)
        y = str(y)
        z = str(z)
        string = 'fill ~'+x+' '+y+' ~'+z+' ~'+x+' '+y+' ~'+z+' glass\n'
        file.write(string)
    
    
    


