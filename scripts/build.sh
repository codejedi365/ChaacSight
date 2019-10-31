#!/bin/bash
#
# FILE: build.sh
#=========================================
# Builds repository into python app
# 
# Usage:
#	$> ./build.sh [options]
# 
# For Options, see help
#   $> ./build.sh --help
#=========================================

# DEFAULT VARS (accepts environment variables)
[ -z "$DIRNAME" ] && DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
[ -z "$BUILD_DIR" ] && BUILD_DIR="build"
[ -z "$VERBOSE" ] && VERBOSE=false

usage() {
	echo "Usage: ./$(basename "$0") [[-q | --quiet][-v |--verbose]] [-h | --help]" 1>&2; exit 1;
}
help() {
    echo ""
    echo " Rainfall Predictor Build Script "
    echo "---------------------------------"
    echo "Automated app build script.  Jupyter notebooks are converted to regular python files." \
    	 "Built files are located in the ${DIRNAME%/}/$BUILD_DIR directory." \
    echo ""
    usage | echo;
    echo "Available Options: "
    echo "  -h | --help   Help"
	echo "  -q | --quiet  Execute quietly except for errors"
	echo "  -v | --verbose   Show more in-depth log output, unless -q is enabled"
    echo ""
    echo "ENVIRONMENT VARS:"
    echo "  DIRNAME, BUILD_DIR, VERBOSE"
    echo ""
    exit 0;
}
print_banner() {
	echo "";
    echo "================================";
    echo "|   Rainfall Predictor Build   |";
    echo "================================";
	echo "";
}

check_prereqs() {
	missing_prereqs=0
	command -v jupyter >/dev/null 2>&1 || { ((missing_prereqs++)); echo >&2 "MISSING PREREQ: jupyter is not installed but is required."; }
	if [ -f "$DIRNAME/dockerconfig/.admin.secret" ]; then
		if [ -z "$(egrep '^admin:[A-Za-z0-9 @#$%^&*()~.,:;_+=<>?-]+$' "$DIRNAME/dockerconfig/.admin.secret")" ]; then
			((missing_prereqs++)); echo >&2 "PREREQ ERROR: .admin.secret file must match syntax 'admin:password' (no quotes).";
		fi
	else
		((missing_prereqs++)); echo >&2 "MISSING PREREQ: $(basename "$DIRNAME")/dockerconfig/.admin.secret file missing.";
	fi
	
	return "$missing_prereqs"
}

# Process line arguments
process_args() {
	while :; do
		case "$1" in		   # process & check command line options
			-h|--help)
				help
				;;
			-q|--quiet)
				MODE_QUIET=true
				;;
			-v|--verbose)
				VERBOSE=true
				;;
			--)			# End of all options.
				shift
				break
				;;
			-?*)		#Unknown option
				usage;
				;;
			*)			# Default: no more options, break out of loop.
				break
		esac
		
		shift
	done
		
	## // If-statements to check if interdependent options are satisfied // ##
	
	## // IF-statements to fill all vars with defaults if not already filled // ##
	[ -z "$MODE_QUIET" ] && MODE_QUIET=false
	ERROR_COUNT=0		# prevent evironment pollution & reset
}

hit_error() {
	((ERROR_COUNT++))
	echo "$1" >&2
}

build() {
	echo && echo "building...";

	# PRE-BUILD, due to not latest file in SRC, link it instead
	ln -s "$DIRNAME/reports/Data_Story.ipynb" "$DIRNAME/src/Data_Story.ipynb"

	# does not handle (within src) or maintain (within build) directory structures
	for filename in "$DIRNAME"/src/*.ipynb; do
		# jupyter nbconvert --to script [YOUR_NOTEBOOK].ipynb
		[ $VERBOSE == true ] && loglevel="" || loglevel="--log-level WARN"
		jupyter nbconvert $loglevel --to script "$filename"
		local CONV_SUCCESS="$?"
		local file="$(basename "${filename%.ipynb}.py")"

		[ $CONV_SUCCESS == 0 ] && mv "${filename%.ipynb}.py" "$DIRNAME/$BUILD_DIR/$file"

		if [ $CONV_SUCCESS == 0 ] && [ $VERBOSE == true ]; then
			echo "BUILD: added $file." && echo;
		elif [ $CONV_SUCCESS != 0 ]; then
			hit_error "ERROR: conversion of $(basename $filename) failed."
		fi
	done

	for filename in "$DIRNAME"/src/*.py; do
		cp "$filename" "$DIRNAME/$BUILD_DIR/"
		COPY_SUCCESS="$?"
		if [ $COPY_SUCCESS == 0 ] && [ $VERBOSE == true ]; then
			echo "BUILD: added $file." && echo;
		elif [ $COPY_SUCCESS != 0 ]; then
			hit_error "ERROR: copy of $(basename $filename) failed."
		fi
	done

	## POST-BUILD, revert changes
	rm "$DIRNAME/src/Data_Story.ipynb"

	return $ERROR_COUNT
}

## Main Loop ##
main() {
	[ $MODE_QUIET = true ] && exec 1>/dev/null;
	print_banner 1>&1;

	if [ ! -d "$DIRNAME/$BUILD_DIR" ]; then
		if [ $VERBOSE ]; then
			echo "Creating Directories: "
			echo -n "  " && echo "$DIRNAME/$BUILD_DIR"	# macosx mkdir -p -v [path] fails, is official bug
		fi
		mkdir -p "$DIRNAME/$BUILD_DIR"

	elif [ -n "$(ls -al "$DIRNAME/$BUILD_DIR" | egrep --invert-match '^(.*[ ]((\.)|(\.\.))$)|(total.*$)')" ]; then
		## CLEAN PREVIOUS TEST BUILD
		echo "cleaning...";
		if [ $VERBOSE == true ]; then
			rm -vfR "$DIRNAME/$BUILD_DIR"/*
		else
			rm -fR "$DIRNAME/$BUILD_DIR"/*
		fi
		echo "clean complete.";
	fi
	
	## BUILD
	build 1>&1;

	if [[ $ERROR_COUNT > 0 ]]; then
		echo "Python App build completed but with $ERROR_COUNT error(s)." && echo;
		exit 1;
	else 
		echo "Python App build complete." && echo;
	fi
}

# ------------------------------
# CODE START - Ingest line args
# ------------------------------
process_args "$@";

check_prereqs || exit 1;

main                    # Run Main Loop
exit 0;
