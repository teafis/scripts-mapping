"""
HGT Reader Test

Tests reading in SRTM3 data files

Ian O'Rourke
March 7, 2019
"""

import numpy as np
import matplotlib.pyplot as plt

import terrain_library as terralib

if __name__ == '__main__':
    m44_110 = terralib.get_elevation_data(44, -110)
    m44_111 = terralib.get_elevation_data(44, -111)
    m44_112 = terralib.get_elevation_data(44, -112)
    m45_110 = terralib.get_elevation_data(45, -110)
    m45_111 = terralib.get_elevation_data(45, -111)
    m45_112 = terralib.get_elevation_data(45, -112)
    m46_110 = terralib.get_elevation_data(46, -110)
    m46_111 = terralib.get_elevation_data(46, -111)
    m46_112 = terralib.get_elevation_data(46, -112)

    total_map_1 = m44_112
    total_map_1 = np.append(total_map_1, m44_111, axis=1)
    total_map_1 = np.append(total_map_1, m44_110, axis=1)

    total_map_2 = m45_112
    total_map_2 = np.append(total_map_2, m45_111, axis=1)
    total_map_2 = np.append(total_map_2, m45_110, axis=1)

    total_map_3 = m46_112
    total_map_3 = np.append(total_map_3, m46_111, axis=1)
    total_map_3 = np.append(total_map_3, m46_110, axis=1)

    total_map = total_map_3
    total_map = np.append(total_map, total_map_2, axis=0)
    total_map = np.append(total_map, total_map_1, axis=0)

    plt.figure(1)
    plt.imshow(total_map)

    plt.show()
