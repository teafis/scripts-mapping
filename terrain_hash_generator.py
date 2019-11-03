"""
MD5 Generator

Generates and MD5 for all HGT files in the target directory

Ian O'Rourke
"""

import glob
import terrain_library as terralib

if __name__ == '__main__':
	files = glob.glob('{:s}*.hgt'.format(terralib.target_dir))

	for file in files:
		with open('{:s}.md5'.format(file), 'wb') as f:
			f.write(terralib.get_md5_for_file(file))
