"""
Terrain Downloader

Downloads SRTM3 Data files for Selected Region from OpenTopography

Ian O'Rourke
March 8, 2019
"""

import argparse
import terrain_library as terralib

import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloads SRTM3 data for the provided lat/lon range')
    parser.add_argument('-m', '--multi', default=0, help='Number of processes >= 0 to use for multiprocessing. Default is 0, or off')
    parser_results = parser.parse_args()

    # Obtain the multi factor
    multi = int(parser_results.multi)

    # Create the target directory if it doesn't exist
    terralib.mkdir_p(terralib.target_dir)

    def file_exists(path):
        return os.path.isfile(path)

    def lat_lon_generator():
        for lat in range(terralib.lat_lower, terralib.lat_upper + 1):
            for lon in range(terralib.lon_lower, terralib.lon_upper + 1):
                yield (lat, lon)


    def get_srtm3_position(pos):
        # Obtains the SRTM3 file if either the file or the md5 hash does not exist for the given position
        download_file = terralib.target_dir + terralib.get_srtm3_filename_for_loc(*pos)
        md5_file = download_file + '.md5'

        if not file_exists(download_file) or not file_exists(md5_file):
            return terralib.get_srtm3_file_url(*pos, terralib.target_dir)
        else:
            print('Loc {:d}, {:d} exists'.format(pos[0], pos[1]))
            return True

    if multi > 0:
        from multiprocessing.pool import ThreadPool

        p = ThreadPool(multi)

        for file_path in p.imap_unordered(get_srtm3_position, lat_lon_generator()):
            pass
    else:
        for p in lat_lon_generator():
            get_srtm3_position(p)

    print('finished')
