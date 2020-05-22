# -*- coding: utf-8 -*-
"""
Created on Fri May  1 04:14:01 2020

@author: sbamford
"""

# sierpinski solid


#%% Generate points

import numpy as np

points = np.array([[np.sqrt(8/9), 0, 0],
          [-np.sqrt(2/9), np.sqrt(2/3), 0],
          [-np.sqrt(2/9), -np.sqrt(2/3), 0],
          [0,0,4/3]])

points = (points / (4/3) * 255).astype(np.float64)


coordsAll = []
coordsCurrent = np.zeros((3, 1), dtype=np.float64)

for i in range(10000):
    idx = int(np.random.rand()*4)
    target = points[idx, :][:, np.newaxis]
    coordsCurrent = coordsCurrent * 0.5 + target * 0.5
    coordsAll.append(coordsCurrent)
coordsAll = np.concatenate(coordsAll, axis=1)
coordsAll = coordsAll.T.astype(np.int)

#%% See the points in a plot

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(coordsAll[:, 0], coordsAll[:, 1], coordsAll[:, 2], marker='s')
    
#%% Generate script

from os.path import join, abspath, dirname

with open(join(dirname(dirname(abspath(__file__))), \
               join('example','sierpinski.mcfunction')), 'w') as file:
    
    for x, y, z in coordsAll:
        x = str(x)
        y = str(y)
        z = str(z)
        string = 'fill ~'+x+' '+z+' ~'+y+' ~'+x+' '+z+' ~'+y+' diamond_block\n'
        file.write(string)
        