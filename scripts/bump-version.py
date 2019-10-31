#!/usr/bin/env python
# coding: utf-8

import os
import sys

major_upgrade = True if len(sys.argv) > 1 and sys.argv[1] == "major" else False
update = True if len(sys.argv) > 1 and sys.argv[1] == "update" else False

curr_dir = os.path.dirname(os.path.abspath(__file__))
vfilename = os.path.join(curr_dir, os.pardir, 'VERSION')

try:
	version_file = open(vfilename,'r+')
	version = version_file.read().rstrip("\r\n")

except IOError:
	open(vfilename, "w+").close()       # create file on disk
	version_file = open(vfilename,'r+')
	version = "0.0"
	major_upgrade = True

v_parts = version.split('.')

if major_upgrade:									# major upgrade
	v_parts[0] = str( int(v_parts[0])+1 )				# increment major version number
	v_parts[1] = "0"									# reset minor version number
	v_parts = v_parts[:2]								# only take maj.minor elements

elif update:										# maj.minor.X update
	if len(v_parts) == 2:
		v_parts.append('1')
	else:
		v_parts[2] = str( int(v_parts[2])+1 )

else: 												# DEFAULT: minor upgrade
	v_parts[1] = str( int(v_parts[1])+1 )
	v_parts = v_parts[:2]

new_version = ".".join(v_parts)

version_file.seek(0)                           # Go to first line, first column of file
version_file.write( new_version+'\n' )
version_file.truncate()                        # end file here, delete anything after the current file position
version_file.close()

print("Version: {0} => {1}".format(version, new_version))
exit(0)
