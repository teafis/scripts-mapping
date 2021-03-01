"""

"""

import pathlib
import requests
import zipfile
import sys
import io
import matplotlib.pyplot as plt

import gshhg_lib


# Define file parameters
coastline_dir = pathlib.Path(__file__).parent / 'gshhg'
coastline_zip_file = coastline_dir / 'gshhg-bin.zip'

# Create the coastline directory
if not coastline_dir.exists():
    print('Creating coastline directory GSHHG')
    coastline_dir.mkdir()

# Get the coastline zip file if needed
if not coastline_zip_file.exists():
    coastline_zip_url = 'https://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/latest/gshhg-bin-2.3.7.zip'
    print('Getting the GSHHG coastline file from {:s}'.format(coastline_zip_url))
    r = requests.get(
        coastline_zip_url,
        allow_redirects=True)

    relative_dir = coastline_zip_file.relative_to(coastline_dir)
    print('Writing coastline db file to {:s}'.format(str(pathlib.PurePosixPath(relative_dir))))
    if r.ok:
        with coastline_zip_file.open('wb') as f:
            f.write(r.content)
        print('Finished writing coastline db')
    else:
        print('Error writing coastline db file')
        sys.exit(1)
else:
    print('GSHHG coastline file already exists')

# Read the input zip files
zip_data = io.BytesIO()
with coastline_zip_file.open('rb') as f:
    zip_data.write(f.read())
zip_data.seek(0)

zipf = zipfile.ZipFile(zip_data)

print('Files in {:s}'.format(coastline_zip_file.name))
for f in zipf.filelist:
    print('  {:s}'.format(f.filename))


shapes = list()
for zipfi in zipf.filelist:
    if zipfi.filename[-3:].lower() != 'i.b':
        continue
    if len(shapes) > 0:
        break
    print('Reading {:s}'.format(zipfi.filename))
    file_data = zipf.read(zipfi.filename)
    with io.BytesIO(file_data) as f:
        reader_data = io.BufferedReader(f)
        while reader_data.tell() < len(file_data):
            shapes.append(gshhg_lib.GSHHGShape.read_from_stream(reader_data))

print('Length: {:d}'.format(len(shapes)))

plt.figure()
for sh in shapes:
    if sh.level != sh.LevelType.LAND:
        continue
    x = sh.get_lon()
    y = sh.get_lat()
    plt.plot(x, y)
plt.show()
