"""
SRTM3 Terrain Library Files

Created March 23, 2019
Ian O'Rourke
"""

import os
import requests
import hashlib
import numpy as np

import enum
import io
import zipfile

import shapefile
import shapely.geometry as spg


# Define the parameters required for the basemap

class BasemapResolutions(enum.Enum):
    LOW = '110m'
    MED = '50m'
    HIGH = '10m'


selected_res = BasemapResolutions.LOW


class BasemapFile:
    def __init__(self, output_fname, url_input):
        self.url = url_input
        self.output_fname = output_fname
        self.zip_data = None

    def _get_file_from_zip(self, fname):
        if self.zip_data is None:
            r = requests.get(self.url)
            zip_bytes = io.BytesIO(r.content)
            self.zip_data = zipfile.ZipFile(zip_bytes)
        
        shpfile = self.zip_data.read(fname)
        return io.BytesIO(shpfile)

    def _replace_file_extention(self, ext_name):
        url_fname_i = self.url.rfind('/')
        url_fname_j = self.url.rfind('.')
        new_fname = '{:s}.{:s}'.format(
            self.url[url_fname_i+1:url_fname_j],
            ext_name)
        return new_fname

    @property
    def shp_file(self):
        return self._get_file_from_zip(self._replace_file_extention('shp'))
    
    @property
    def dbf_file(self):
        return self._get_file_from_zip(self._replace_file_extention('dbf'))


basemap_land = BasemapFile('land.dat', 'https://naciscdn.org/naturalearth/{0:s}/physical/ne_{0:s}_land.zip'.format(selected_res.value))
basemap_boundaries = BasemapFile('boundaries.dat', 'https://naciscdn.org/naturalearth/{0:s}/cultural/ne_{0:s}_admin_1_states_provinces_lakes.zip'.format(selected_res.value))
basemap_lakes = BasemapFile('lakes.dat', 'https://naciscdn.org/naturalearth/{0:s}/physical/ne_{0:s}_lakes.zip'.format(selected_res.value))
basemap_rivers = BasemapFile('rivers.dat', 'https://naciscdn.org/naturalearth/{0:s}/physical/ne_{0:s}_rivers_lake_centerlines.zip'.format(selected_res.value))

# Define the target directory for files
target_dir = 'srtm3/'
land_mass_file = 'maps/ne_110m_land/ne_110m_land.shp'

# Define bounds for North America
lon_lower = -130
lon_upper = -53
lat_lower = 23
lat_upper = 50

region_bounds = (lon_lower, lon_upper, lat_lower, lat_upper)

# Define the SRTM3 Array Size
ARRAY_SIZE = 1201


def mkdir_p(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
        print('Created directory {:s}'.format(dir))
    else:
        print('Directory {:s} already exists'.format(dir))


def file_exists(url):
    """
    Returns true if the remote file exists
    :param url: remote file directory
    :return: true if file exists, false if not
    """
    r = requests.head(url)
    return r.status_code == requests.codes.ok


def get_srtm3_filename_for_loc(lat, lon):
    """
    Provides the filename for the associated SRTM3 file
    :param lat: integer latitude (degrees)
    :param lon: integer longitude (degrees)
    :return: string filename
    """
    # Determine the east-west string
    lon_ew = 'E' if lon >= 0 else 'W'

    # Determine north-south string
    lat_ns = 'S' if lat < 0 else 'N'

    # Combine all parameters to a filename and append
    return '{:s}{:02d}{:s}{:03d}.hgt'.format(lat_ns, abs(lat), lon_ew, abs(lon))


def get_srtm3_file_url(lat, lon, target):
    """
    Obtains the SRTM3 file from OpenTopology for the specified integer lat/lon pair, for the target directory
    Does nothing if the URL does not return an "ok" status
    :param lat: integer latitude
    :param lon: integer longitude
    :param target: file directory to place resulting files into
    """
    # Define the base URL
    base_url = 'https://cloud.sdsc.edu/v1/AUTH_opentopography/Raster/SRTM_GL3/SRTM_GL3_srtm/'

    # Create a list to hold all URL parameters
    url_str_builder = [base_url]

    # Determine if we are in the southern hemisphere
    if lat < 0:
        url_str_builder.append('South/')
        lat_ns = 'S'
    # Otherwise, in the northern
    else:
        url_str_builder.append('North/')
        lat_ns = 'N'

        # Go to new folder for greater or less than 30 degrees northern latitude
        if lat < 30:
            url_str_builder.append('North_0_29/')
        else:
            url_str_builder.append('North_30_60/')

    # Determine the east-west string
    lon_ew = 'E' if lon >= 0 else 'W'

    # Combine all parameters to a filename and append
    file_name = get_srtm3_filename_for_loc(lat, lon)
    url_str_builder.append(file_name)

    # Join list into a url
    url = ''.join(url_str_builder)

    # Obtain and save file if it exists
    if file_exists(url):
        print('Getting {:s}'.format(url))

        r = requests.get(url, allow_redirects=True)

        content = r.content

        m = hashlib.md5()
        m.update(content)

        with open('{:s}{:s}'.format(target, file_name), 'wb') as f:
            f.write(content)

        with open('{:s}{:s}.md5'.format(target, file_name), 'w') as f:
            f.write(m.hexdigest())

        return '{:s}{:s}'.format(target_dir, file_name)

    else:
        print('No file exists for {:s}'.format(url))
        return None


def get_elevation_data(lat, lon):
    """
    Attempts to get the SRTM3 data file associated with the lat/lon provided
    :param lat: integer latitude
    :param lon: integer longitude
    :return: np.array of elevations for tile, None if no file exists
    """
    elevations = None

    filename = target_dir + get_srtm3_filename_for_loc(lat, lon)

    try:
        with open(filename, 'rb') as hgt_data:
            elevations = np.fromfile(hgt_data, np.dtype('>i2'), ARRAY_SIZE * ARRAY_SIZE)
            elevations = elevations.reshape((ARRAY_SIZE, ARRAY_SIZE))
    except FileNotFoundError:
        pass

    return elevations


def get_md5_for_lat_lon(lat, lon):
    """
    Provides the md5 for the (lat, lon) tile provided
    :param lat: integer latitude
    :param lon: integer longitude
    :return: md5 hex if file is found, None otherwise
    """
    filename = target_dir + get_srtm3_filename_for_loc(lat, lon)
    return get_md5_for_file(filename)


def get_md5_for_file(filename):
    """
    Provides the md5 for the filename
    :param filename: string filename/path from current working directory
    :return: md5 hex if file is found, None otherwise
    """
    md5 = None
    try:
        with open(filename, 'rb') as f:
            content = f.read()
        with open('{:s}.md5'.format(filename), 'wb') as f:
            m = hashlib.md5()
            m.update(content)
            md5 = m.hexdigest()
    except FileNotFoundError:
        pass
    return md5


def load_land_polygons():
    """
    Returns shapely polygons for the land mass shapefile
    :return: a list of polygons to use in the terrain basemap construction
    """
    shape = shapefile.Reader(shp=basemap_land.shp_file, dbf=basemap_land.dbf_file)

    shapes = shape.shapeRecords()

    polygons = []

    for s in shapes:
        x_points = []
        y_points = []

        for p in s.shape.points:
            x_points.append(p[0])
            y_points.append(p[1])

        polygons.append(spg.Polygon([(x_points[i], y_points[i]) for i in range(len(x_points))]))

    return polygons
