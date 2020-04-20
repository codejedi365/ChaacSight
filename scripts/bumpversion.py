#!/usr/bin/env python
# coding: utf-8

import os
import sys

def bump(update_size="minor"):
	major_upgrade = True if update_size == "major" else False
	update = True if update_size == "update" else False

	curr_dir = os.path.dirname(os.path.abspath(__file__))
	vfilename = os.path.join(curr_dir, os.pardir, 'VERSION')

	try:
		with open(vfilename,'r') as version_file:
			version = version_file.read().rstrip("\r\n")

	except IOError:
		open(vfilename, "w+").close()       # create file on disk
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

	with open(vfilename,'r+') as version_file:
		version_file.seek(0)                           # Go to first line, first column of file
		version_file.write( new_version+'\n' )
		version_file.truncate()                        # end file here, delete anything after the current file position

	print("Version: {0} => {1}".format(version, new_version))


if __name__ == "__main__":
	update_type = "" if len(sys.argv) <= 1 else sys.argv[1]
	bump(update_type)
	exit(0)
