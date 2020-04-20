#!/usr/bin/env python3
#
# FILE: build.py
#=========================================
# Builds repository into python app
# 
# Usage:
#	$> ./build.py [options]
# 
# For Options, see help
#   $> ./build.py --help
#=========================================
from __future__ import print_function
import sys, os
import shutil
import glob
import re
import platform
import subprocess


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, flush=True, **kwargs)

def usage(printTo=""):
	this_file = os.path.basename(os.path.abspath(__file__))
	printFn = print if printTo == "stdout" else eprint
	printFn("Usage: ./{0} [[-q | --quiet][-v |--verbose]] [-h | --help]".format(this_file))
	exit(1)

def help():
    print("")
    print(" Rainfall Predictor Build Script ")
    print("---------------------------------")
    print("Automated app build script.  Jupyter notebooks are converted to regular python files. " \
         +"Built files are located in the {0} directory.".format(os.path.join(os.path.basename(DIRNAME),BUILD_DIR)))
    print("")
    try: 
        usage(printTo="stdout")
    except SystemExit:
        print("")
    print("Available Options: ")
    print("  -h | --help   Help")
    print("  -q | --quiet  Execute quietly except for errors")
    print("  -v | --verbose   Show more in-depth log output, unless -q is enabled")
    print("")
    print("ENVIRONMENT VARS:")
    print("  DIRNAME, BUILD_DIR, VERBOSE"+'\n')
    exit(0)

def print_banner():
    print('\n'+"================================")
    print(     "|   Rainfall Predictor Build   |")
    print(     "================================"+'\n')

def check_prereqs():
	missing_prereqs = 0
	prereqs = []
	if os_version == 'Windows':
		prereqs = [
			{ 'test' : ["powershell.exe", "Get-Command jupyter 2>&1 | out-null"], 'isshell':False, 'onerror': "jupyter is not installed but is required." }
		]
	elif os_version == 'Linux' or os_version == 'Darwin':
		prereqs = [
			{ 'test' : ["command", "-v", "jupyter"], 'isshell':True, 'onerror': "jupyter is not installed but is required." }
		]
	else:
		eprint("Platform ({}) not supported".format(os_version))
		exit(3)

	for prereq in prereqs:
		try:
			subprocess.check_call(prereq['test'], shell=prereq['isshell'])
		except subprocess.CalledProcessError:
			missing_prereqs += 1
			eprint("MISSING PREREQ: {}".format(prereq['onerror']))
		else:
			continue  # command found, check next prereq
		
	return(missing_prereqs)


# Process line arguments
def process_args( args ):
	global MODE_QUIET, VERBOSE

	# Argument Handlers
	def request_help(i):
		help()
	def set_quiet(i):
		global MODE_QUIET
		MODE_QUIET = True
	def set_verbose(i):
		global VERBOSE
		VERBOSE = True
	def end_args(i):
		return("end_args")
	def unknown(i):
		usage()

	switcher = {
		'-h' :        request_help,
		'--help' :    request_help,
		'-q' :        set_quiet,
		'--quiet' :   set_quiet,
		'-v' : 		  set_verbose,
		'--verbose' : set_verbose,
		'--' : 		  end_args
	}

	for i in range(1,len(args)):
		try:
			func = switcher[args[i]]
			retVal = func(i)
			if retVal == "end_args":
				break
		except KeyError:
			unknown(i)
		except SystemExit as exitrequest:
			raise(exitrequest)
		
	## // If-statements to check if interdependent options are satisfied // ##
	
	## // IF-statements to fill all vars with defaults if not already filled // ##
	MODE_QUIET = MODE_QUIET if MODE_QUIET is not None else False	


def hit_error(error_str=""):
	global error_count
	error_count += 1
	eprint(error_str)


def __build():
	print("building...")

	# does not handle (within src) or maintain (within build) directory structures
	notebooks = glob.glob(os.path.join(DIRNAME,'src','*.ipynb'))
	
	for notebook in notebooks:

		# jupyter nbconvert --to script [YOUR_NOTEBOOK].ipynb
		# jupyter nbconvert $loglevel --to script "$filename"
		ext_cmd = []
		is_shellcmd = True
		loglevel = "" if VERBOSE == True else "--log-level WARN"

		if os_version == 'Windows':
			ext_cmd = [ 
				'powershell.exe',
				'jupyter nbconvert {0} --to script "{1}"'.format(loglevel,notebook)
			]
			is_shellcmd = False
			print('\n'+'PS C:\> '+ext_cmd[1])

		elif os_version == 'Linux' or os_version == 'Darwin':
			ext_cmd = [
				'jupyter nbconvert {0} --to script {1}'.format(loglevel,notebook)
			]
			is_shellcmd = True

		else:
			eprint("Platform ({}) not supported".format(os_version))
			exit(3)

		## RUN external subprocess
		print('Converting {} notebook...'.format(notebook))
		try:
			p = subprocess.Popen(
				ext_cmd,
				shell=is_shellcmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT
			)
			for line in p.stdout.readlines():
				print(line)
			retval = p.wait()
			if retval != 0:  # remove once figured out
				eprint("Jupyter failed to convert .ipynb to .py")
				raise( Exception() )

		except KeyboardInterrupt as usr_canx:
			raise(usr_canx)
		except:
			eprint("Build Failure.")
			exit(2)

		else:
			ext_regex = re.compile(r"(.*).ipynb$")
			pyfile = ext_regex.sub( "\\1.py", os.path.basename(notebook) )
			try:
				shutil.move(
					os.path.join(DIRNAME,'src',pyfile),
					os.path.join(DIRNAME,BUILD_DIR,pyfile)
				)
			except KeyboardInterrupt as usr_canx:
				raise(usr_canx)
			except Exception as err:
				eprint(err)
				hit_error("ERROR: conversion of {} failed.".format(os.path.basename(notebook)))
			else:
				if VERBOSE == True:
					print("BUILD: added {}".format(os.path.join(os.path.basename(DIRNAME),BUILD_DIR,pyfile)))


	## Make copies of any remaining *.py files to build directory
	pyfiles = glob.glob(os.path.join(DIRNAME,'src','*.py'))
	for filename in pyfiles:
		try:
			shutil.copyfile(
				filename,
				os.path.join(DIRNAME,BUILD_DIR,os.path.basename(filename))
			)
		except KeyboardInterrupt as usr_canx:
			raise(usr_canx)
		except Exception as err:
			eprint(err)
			hit_error("ERROR: copy of {} failed.".format(os.path.basename(filename)))
		else:
			if VERBOSE == True:
				print("BUILD: added {}".format(
					os.path.join(os.path.basename(DIRNAME),BUILD_DIR,os.path.basename(filename))
				))

	return error_count


## Main Loop ##
def build():
	global MODE_QUIET
	if MODE_QUIET == True:
		sys.stdout = open(os.devnull, 'w')

	if not os.path.isdir(os.path.join(DIRNAME,BUILD_DIR)):
		if VERBOSE:
			print("Creating Directories: ")
			print("  "+os.path.join(DIRNAME,BUILD_DIR))
		
		os.makedirs(os.path.join(DIRNAME,BUILD_DIR))

	elif len(os.listdir(os.path.join(DIRNAME,BUILD_DIR))) > 0:
		## CLEAN PREVIOUS TEST BUILD
		print("cleaning...")
		folder = os.path.join(DIRNAME,BUILD_DIR)
		for the_file in os.listdir(folder):
			file_path = os.path.join(folder, the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path)
					if VERBOSE: print("DELETED: {}".format(file_path))
			
				elif os.path.isdir(file_path): 
					shutil.rmtree(file_path)
					if VERBOSE: print("DELETE: {}/*".format(file_path))
			
			except Exception as e:
				print(e)

		print("clean complete.")
	
	## BUILD
	__build()

	if error_count > 0:
		print("Python App build completed but with {} error(s).".format(error_count))
		exit(1)
	else:
		print("Python App build complete.")


if __name__ == "__main__":
	# DEFAULT VARS (accepts environment variables)
	DIRNAME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))		# cd ../..
	BUILD_DIR = "build"
	VERBOSE = False
	MODE_QUIET = False
	error_count = 0		# prevent evironment pollution
	os_version = platform.system()

	# ------------------------------
	# CODE START - Ingest line args
	# ------------------------------
	try:
		process_args(sys.argv)

		if check_prereqs() != 0: 
			exit(1)

		if not MODE_QUIET:
			print_banner()

		build()

	except KeyboardInterrupt as usr_canx:
		eprint('\n'+"User interrupted build process.  Exiting...")
		exit(1)	
	else:
		exit(0)
