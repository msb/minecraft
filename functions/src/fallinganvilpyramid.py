# -*- coding: utf-8 -*-
"""
Created on Fri May  1 04:14:01 2020

@author: sbamford
"""

#%% Observe what the result will be in a plot

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

rng = 10

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
x = []
y = []
z = []
for i in range(rng):
    xmin = -i
    xmax = i
    ymin = -rng+i
    ymax = rng-i
    zval = 255-i
    for xval in range(xmin, xmax + 1):
        for yval in range(ymin, ymax + 1):
            x.append(xval)
            y.append(yval)
            z.append(zval)
ax.scatter(x, y, z, marker='s')
    
#%% Generate the script

from os.path import join, abspath, dirname

rng = 10

with open(join(dirname(dirname(abspath(__file__))), \
               join('example','fallinganvilpyramid.mcfunction')), 'w') as file:
    for i in range(rng):
        xmin = str(-i)
        xmax = str(i)
        ymin = str(-rng+i)
        ymax = str(rng-i)
        z = str(255-i)
        string = 'fill ~'+xmin+' '+z+' ~'+ymin+' ~'+xmax+' '+z+' ~'+ymax+' anvil\n'
        file.write(string)
        