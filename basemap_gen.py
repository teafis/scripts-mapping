"""
Generate Basemap from Natural Earth Shapefile data
"""

import shapefile

import terrain_library as terralib

import time

output_dir = 'output/'

terralib.mkdir_p(output_dir)

    
files = [
    terralib.basemap_land,
    terralib.basemap_boundaries,
    terralib.basemap_lakes,
    terralib.basemap_rivers]


st = time.time()

for file in files:
    shape = shapefile.Reader(shp=file.shp_file, dbf=file.dbf_file)

    shapes = shape.shapeRecords()

    polygons = []
    strbuilder = []
    
    strbuilder.append('{:d}'.format(shape.numRecords))
    strbuilder.append('')
    
    for s in shapes:
        x_points = []
        y_points = []
        
        strbuilder.append('{:d}'.format(len(s.shape.points)))
        
        for p in s.shape.points:
            x_points.append(p[0])
            y_points.append(p[1])
            
            strbuilder.append('{:f} {:f}'.format(p[0], p[1]))
        
        strbuilder.append('')
    
    with open(output_dir + file.output_fname, 'w') as f:
        f.write('\n'.join(strbuilder))

et = time.time()

print('done!')
print('elapsed time: {:.3f} s'.format(et - st))
