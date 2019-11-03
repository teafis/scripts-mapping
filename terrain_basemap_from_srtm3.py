"""
Terrain Basemap from SRTM3

Reads in data files for SRTM3 and provides a basemap that can be

Ian O'Rourke
March 23, 2019
"""

# TODO - Add a hash check for each loaded tile?

# TODO - Try loading/numpy/save SRTM3 file and verify MD5 are same

import argparse
import numpy as np
import terrain_library as terralib

import multiprocessing

import pickle


bounds = terralib.region_bounds

output_dir = 'output/'
target_file = output_dir + 'basemap_terrain.hgt'

lon_lower = bounds[0]
lon_upper = bounds[1]
lat_lower = bounds[2]
lat_upper = bounds[3]

base_map_pixels_per_degree = 120

srtm3_px_per_basemap_px = (terralib.ARRAY_SIZE - 1) / base_map_pixels_per_degree
assert abs(srtm3_px_per_basemap_px - int(srtm3_px_per_basemap_px)) < 1e-6
srtm3_px_per_basemap_px = int(srtm3_px_per_basemap_px)

invalid_data = -32768

land_polygons = terralib.load_land_polygons()

tile_i_pre = np.array([k for k in range(srtm3_px_per_basemap_px)])


def load_lat_lon(args_in):
    lat, lon, queue, total_vals = args_in
    comb_i = queue.get()

    if comb_i % 10 == 0:
        print('Currently {:d} of {:d} values done'.format(comb_i, total_vals))

    queue.put(comb_i + 1)
    
    elev = terralib.get_elevation_data(lat, lon)

    if elev is not None:
        elev = np.flipud(elev)

    tile_sel = np.zeros((base_map_pixels_per_degree, base_map_pixels_per_degree))

    for i in range(base_map_pixels_per_degree):
        for j in range(base_map_pixels_per_degree):
            if elev is None:
                tile_sel[j, i] = invalid_data
            else:
                tile_i = tile_i_pre + i * srtm3_px_per_basemap_px
                tile_j = tile_i_pre + j * srtm3_px_per_basemap_px

                max_elev = np.max(elev[tile_j, tile_i])

                lat_curr = lat + j / base_map_pixels_per_degree
                lon_curr = lon + i / base_map_pixels_per_degree
                point_curr = terralib.spg.Point([lon_curr, lat_curr])
                
                point_within_land = False

                for poly in land_polygons:
                    if poly.contains(point_curr):
                        point_within_land = True
                        break

                tile_sel[j, i] = max_elev if point_within_land else invalid_data

    return (lat, lon), tile_sel


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert SRTM3 data to a condensed basemap')
    parser.add_argument('-m', '--multi', default=0,
                        help='Number of processes >= 0 to use for multiprocessing. Default is 0, or off')
    parser_results = parser.parse_args()

    # Obtain the multi factor
    multi = int(parser_results.multi)

    print('Reducing each axis by a factor of {:d}'.format(srtm3_px_per_basemap_px))

    terralib.mkdir_p(output_dir)

    m = multiprocessing.Manager()
    comb_i_queue = m.Queue()
    comb_i_queue.put(0)

    lon_vals = list(range(lon_lower, lon_upper + 1))
    lat_vals = list(range(lat_lower, lat_upper + 1))

    combinations = []
    for lon in lon_vals:
        for lat in lat_vals:
            combinations.append((lat, lon, comb_i_queue, len(lon_vals) * len(lat_vals)))

    print('Total values: {:d}'.format(len(combinations)))

    if multi == 0:
        print('Multithreading Disabled')
        retvals = []
        for c in combinations:
            retvals.append(load_lat_lon(c))
    else:
        print('Multithreading Enabled')
        with multiprocessing.Pool(processes=multi) as pool:
            retvals = pool.map(load_lat_lon, combinations)

    base_map = np.ones(
        ((lat_upper - lat_lower + 1) * base_map_pixels_per_degree,
         (lon_upper - lon_lower + 1) * base_map_pixels_per_degree),
        dtype=np.dtype('>i2'))

    for r in retvals:
        lat, lon = r[0]
        base_map_j = (lat - lat_lower) * base_map_pixels_per_degree
        base_map_i = (lon - lon_lower) * base_map_pixels_per_degree

        base_map[base_map_j:base_map_j+base_map_pixels_per_degree, base_map_i:base_map_i+base_map_pixels_per_degree] = r[1]

    base_map = np.flipud(base_map)

    bm_shape = base_map.shape
    base_map_solo = np.reshape(base_map, bm_shape[0] * bm_shape[1])

    with open(target_file, 'wb') as f:
        f.write(base_map_solo.tobytes())

    with open(target_file + '.md5', 'w') as f:
        f.write(terralib.get_md5_for_file(target_file))
