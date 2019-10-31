#!/bin/bash
#
# FILE: dockerify.sh
#=========================================
# Instructions to build Docker container
#
# Usage:
#	$> ./dockerify.sh [options]
# 
# For Options, see help
#   $> ./dockerify.sh --help
#=========================================

DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
BUILD_DIR="build"
IMAGE_DIR="bin"
AUTHOR="lilfetz22"
REPO=""
[ -z "$NAME" ] && NAME="rainfall-predictor"

usage() {
	echo "Usage: ./$(basename "$0") [-q | --quiet] [--no-rebuild] [--keep-version]" 1>&2;
	echo "       ./$(basename "$0") [-h | --help]" 1>&2;
	exit 1;
}
help() {
    echo ""
    echo " Rainfall Predictor Docker Creation Script "
    echo "-------------------------------------------"
    echo "Docker build script.  Docker packages app files, tags with version and" \
		 "saves Docker container image." \
    	 "Docker image files are saved to the ${DIRNAME%/}/$IMAGE_DIR directory.";
    usage | echo;
	echo "";
    echo "Available Options: "
    echo "  -h | --help   Help"
	echo "  -q | --quiet  Execute quietly except for errors"
	echo "  --no-rebuild  Makes container with current ./build files, fails if empty"
	echo "  --keep-version  Does not increment version number update field 1.1.X"
    echo "";
	echo "DEFAULT VARS:";
	echo "  AUTHOR: $AUTHOR";
	echo "  IMAGE_NAME: $NAME:latest"
	echo "  BUILD_DIR: $(basename "$DIRNAME")/$BUILD_DIR";
	echo "";
    # echo "ENVIRONMENT VARS:"
    # echo "  DIRNAME, BUILD_DIR, VERBOSE"
    # echo ""
    exit 0;
}
print_banner() {
	echo "";
    echo "====================================";
    echo "|   Dockerify Rainfall Predictor   |";
    echo "====================================";
	echo "START: $(date)";
	echo "";
}

check_prereqs() {
	missing_prereqs=0
	command -v ansible >/dev/null 2>&1 || { ((missing_prereqs++)); echo >&2 "MISSING PREREQ: ansible is not installed but is required."; }
	# List additional prereqs here
	return "$missing_prereqs"
}

# timestamp function in ms
timestamp() {
  date +"%s"
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
			--no-rebuild)
				REBUILD=false
				;;
			--keep-version)
				BUMP_VERSION=false
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
	[ -z "$REBUILD" ] && REBUILD=true
	[ -z "$BUMP_VERSION" ] && BUMP_VERSION=true
	[ -z "$MODE_QUIET" ] && MODE_QUIET=false

}

if [ -z "$(command -v sha256sum)" ]; then
    if [ -n "$(command -v shasum)" ]; then      # Mac OSX alternative 
        sha256sum() {
            shasum -a 256 "$@"
        }
    fi
fi

main() {
	[ $MODE_QUIET = true ] && exec 1>/dev/null;
	print_banner 1>&1;

	SCRIPT_STARTS="$(timestamp)";

	if [ $REBUILD = true ]; then
		# ensure build files are up to date
		echo "[DOCKERIFY] Running code build script...";
		BUILD_SCRIPT_STARTS=$(timestamp)
		BUILD_DIR="$BUILD_DIR" "$DIRNAME/scripts/build.sh" &
		pid=$!
		wait $pid || { echo "[DOCKERIFY] build failed. Aborting..." 2>&2 && echo && exit 1; }
		BUILD_SCRIPT_STOPS=$(timestamp)
		echo "[DOCKERIFY] Code Build completed! ($(($BUILD_SCRIPT_STOPS-$BUILD_SCRIPT_STARTS)) seconds)" && echo;

	elif [ -z "$(ls -al "$DIRNAME/$BUILD_DIR" | egrep --invert-match '^(.*[ ]((\.)|(\.\.))$)|(total.*$)')" ]; then
		# build folder is empty
		echo "MISSING FILES: build directory is empty." >&2 && echo && exit 1;
	fi

	if [ ! -d "$DIRNAME/$IMAGE_DIR" ]; then
		echo "[DOCKERIFY] Creating Directory: "
		echo -n "[DOCKERIFY]   " && echo "$DIRNAME/$IMAGE_DIR"	# macosx mkdir -p -v [path] fails, is official bug
		mkdir -p "$DIRNAME/$IMAGE_DIR"

	elif [ -z "$(ls -al "$DIRNAME/$IMAGE_DIR" | egrep --invert-match '^(.*[ ]((\.)|(\.\.))$)|(total.*$)')" ]; then
		rm -rvf "$DIRNAME/$IMAGE_DIR"/*			# clean out image directory
	fi

	if [ $BUMP_VERSION = true ]; then
		"$DIRNAME/scripts/bump-version.py" "update" 
		if [ "$?" != 0 ]; then
			echo "[DOCKERIFY] Error occured. Aborting..." >&2 && echo && exit 1;
		else
			echo && sleep 2s		# Dramatic effect
		fi
	fi

	# VERSION="v$(cat "$DIRNAME/VERSION")"
	# [ -z $VERSION ] && TAG="$NAME:latest" || TAG="$NAME:$VERSION";
	TAG="$NAME:latest";

	IMAGE_NAME="$(echo "$TAG" | awk -F "[:]" 'BEGIN{OFS="_"} {print $1,$2}')"

	echo "[APP_DEPLOY] Deploying application to Google Cloud Compute Instance...";
	# ansible build [ host_ips, deployment YAML ]
	echo "[APP_DEPLOY] " \
		 ". ansible-playbook" \
			--extra-vars "local_project_dir=${DIRNAME%/}" \
			"$DIRNAME/scripts/ansible/deploy-app-vm.yml"
	
	# actual command
	DOCKER_BUILD_STARTS="$(timestamp)"
	ANSIBLE_CONFIG="${DIRNAME}/scripts/ansible/ansible.cfg"
	source ansible-playbook \
		--extra-vars "local_project_dir=${DIRNAME%/}" \
		"$DIRNAME/scripts/ansible/deploy-app-vm.yml"

	# Handle Docker build status 
	if [ "$?" != 0 ]; then
		echo "[DOCKERIFY] Error occured.  Aborting..." >&2 && echo && exit 1;
	fi

	DOCKER_BUILD_STOPS="$(timestamp)"

	IMAGE_SIZE="$(docker images | awk -F "[ ][ ]+" '{print $5}' | awk 'NR==2')"
	echo && echo "[DOCKERIFY] Docker Image ($IMAGE_SIZE) built in $(($DOCKER_BUILD_STOPS-$DOCKER_BUILD_STARTS)) seconds.";

	echo "[DOCKERIFY] compressing image..."
	docker save "$TAG" | gzip > "$DIRNAME/$IMAGE_DIR/$IMAGE_NAME.tar.gz"
	ZIPPED_SIZE="$(ls -lh "$DIRNAME/$IMAGE_DIR/$IMAGE_NAME.tar.gz" | awk -F "[ ]+" '{print $5}')"
	echo "[DOCKERIFY] SUCCESS: Compressed Docker image (${ZIPPED_SIZE}B) saved as $IMAGE_DIR/$IMAGE_NAME.tar.gz";
	echo "$(sha256sum "$DIRNAME/$IMAGE_DIR/$IMAGE_NAME.tar.gz")" > "$DIRNAME/$IMAGE_DIR/sha256.checksum"
	echo "[DOCKERIFY] sha256: $(cat "$DIRNAME/$IMAGE_DIR/sha256.checksum" | awk -F "[ ]+" '{print $1}')"

	SCRIPT_STOPS="$(timestamp)"
	echo "[DOCKERIFY] Total Execution Time: $(($SCRIPT_STOPS-$SCRIPT_STARTS)) seconds" && echo;
	# Instructions
	echo "  NEXT STEPS  "
	echo " ------------ "
	echo "1. Connect to docker server instance.";
	echo "2. Unzip file with gzip.";
	echo "3. Load this docker image with the command: "
	echo "     $ docker load -i <path/to/$IMAGE_NAME.tar>"
	echo "";
	# echo "OR";
	# echo "1. Run Deploy script";
	# echo "     $ ./scripts/deploy.sh <target_environment>"
	# echo "";
}

keep_awake() {
	if [[ "$OSTYPE" == "linux-gnu" ]]; then
		# disable sleep, set TRAP to re-enable sleep capability, execute script
		targets="sleep.target suspend.target hibernate.target hybrid-sleep.target"
		sudo systemctl mask $targets
		trap "sudo systemctl unmask $targets" ERR EXIT
		$1	# run intended script/function
		return "$?"

	elif [[ "$OSTYPE" == "darwin"* ]]; then		# Mac OSX
		$1 &
		pid=$!
		caffeinate -i -w $pid
		wait $pid
		exit_status="$?"
		[ $exit_status != 0 ] && exit $exit_status;
		return 

	# elif [[ "$OSTYPE" == "cygwin" ]]; then		# POSIX compatibility layer and linux env emulation for windows
	# elif [[ "$OSTYPE" == "msys" ]]; then		# lightweight shell and GNU utilities for Windows (part of MinGW)
	# elif [[ "$OSTYPE" == "win32" ]]; then		# maybe windows
	# elif [[ "$OSTYPE" == "freebsd"* ]]; then	# FreeBSD
	# else
		# Unknown
	fi

	# FALL THROUGH default
	$1		# run like normal
}

# ------------------------------
# CODE START - Ingest line args
# ------------------------------
process_args "$@";

check_prereqs || exit 1;

keep_awake main                    # Run Main Loop
exit 0;
