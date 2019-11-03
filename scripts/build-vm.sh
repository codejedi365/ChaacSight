#!/bin/bash
#
# FILE: build-vm.sh
#=========================================
# Google Compute Engine VM build & deploy script.
#
# Usage:
#	$> ./build-vm.sh [options]
# 
# For Options, see help
#   $> ./build-vm.sh --help
#=========================================

DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
BUILD_DIR="build"
IMAGE_DIR="bin"
[ -z "$NAME" ] && NAME="rainfall-predictor"

usage() {
	echo "Usage: ./$(basename "$0") [-q | --quiet] [--no-autostart] [-r <type> | --release=<type>]" 1>&2;
	echo "       ./$(basename "$0") [-q | --quiet] [--no-rebuild] [--keep-version]" 1>&2;
	echo "       ./$(basename "$0") [--destroy]" 1>&2;
	echo "       ./$(basename "$0") [-h | --help]" 1>&2;
	exit 1;
}
help() {
    echo ""
    echo " Rainfall Predictor VM Creation Script "
    echo "---------------------------------------"
    echo "Google Compute Engine VM build & deploy script.  Ansible provisions a GCE instance" \
		 "with a persistent disk, static IP, and Debian OS.  Once created, Ansible installs" \
    	 "the required app dependencies, configures the OS, and installs the app as a service" \
		 "named ${NAME}.service.  Autostart of the service is the default but can be" \
		 "toggled off with the provided option flag.  Login information will be provided after" \
		 "build and deploy succeeds.  Reverse & clean resources by running with the --destroy flag";
    usage | echo;
	echo "";
    echo "Available Options: "
    echo "  -h | --help     Help"
	echo "  -q | --quiet    Execute quietly except for errors"
	echo "  -r <type> | --release=<type>   Type of release either Major, Minor, or Update"
	echo "                     DEFAULT: Minor, update version number only";
	echo "  --destroy       Removes a deployed VM and releases GCE resouces"
	echo "  --no-autostart  Complete ansible build except for autorun of service"
	echo "  --no-rebuild    Makes container with current ./build files, fails if empty"
	echo "  --keep-version  Does not increment version number update field 1.1.X"
    echo "";
	echo "DEFAULT VARS:";
	# echo "  IMAGE_NAME: $NAME:latest"
	echo "  BUILD_DIR: $(basename "$DIRNAME")/$BUILD_DIR";
	echo "";
    # echo "ENVIRONMENT VARS:"
    # echo "  DIRNAME, BUILD_DIR, VERBOSE"
    # echo ""
    exit 0;
}
print_banner() {
	echo "";
    echo "=========================================";
    echo "|   VM Builder for Rainfall Predictor   |";
    echo "=========================================";
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
			-r|--release)
				if [ "$2" ] && [ -n "$(echo "$2" | grep -iE "^(major|minor|update)$")" ]; then
					RELEASE_TYPE="${2}";
					shift
				else
					usage;
				fi
				;;
			"--release"=?*)
				OPTARG=${1#*=} 			# Delete everything up to "=" and keep the remainder.
				if [ -n "$(echo "$OPTARG" | grep -iE "^(major|minor|update)$")" ]; then
					RELEASE_TYPE="${OPTARG}";
					shift
				else
					usage;
				fi
				;;
			"--release"=)						# Handle the case of an empty --release=
				usage;
				;;
			--destroy)
				DESTROY=true
				;;
			--no-autostart)
				AUTOSTART=false
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
	if [ -n "$RELEASE_TYPE" ]; then
		BUMP_VERSION=true;
		BUMP_VER_SIZE="${RELEASE_TYPE}";
	fi

	## // IF-statements to fill all vars with defaults if not already filled // ##
	[ -z "$AUTOSTART" ] && AUTOSTART=true
	[ -z "$DESTROY" ] && DESTROY=false
	[ -z "$REBUILD" ] && REBUILD=true
	[ -z "$BUMP_VERSION" ] && BUMP_VERSION=true
	[ -z "$BUMP_VER_SIZE" ] && BUMP_VER_SIZE="minor"
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

	if [ $DESTROY = true ]; then
		ANSIBLE_CONFIG="${DIRNAME}/scripts/ansible/ansible.cfg"
		ENV_VARS="ANSIBLE_CONFIG=${ANSIBLE_CONFIG}"

		/bin/bash -c "$ENV_VARS ansible-playbook $DIRNAME/scripts/ansible/cleanup.yml" &
		ansiblePID=$!
		trap "ps -p $ansiblePID > /dev/null && kill $ansiblePID" ERR EXIT
		wait $ansiblePID
		exit_status=$?

		# Handle Ansible build status 
		if [ $exit_status != 0 ]; then
			echo "[VM DESTROY] Error occured.  Aborting..." >&2 && echo && exit 1;
		fi

		SCRIPT_STOPS="$(timestamp)"
		echo "[VM DESTROY] Total Execution Time: $(($SCRIPT_STOPS-$SCRIPT_STARTS)) seconds" && echo;
		echo "Google Cloud Resources Summary: "
		echo "------------------------------- "
		echo "   Compute Instance: RELEASED"
		echo "   Static IP: RELEASED"
		echo "   Persistent Data Disk: 1 Resource Allocated ($)" && echo
		return 0
	fi

	if [ $REBUILD = true ]; then
		# ensure build files are up to date
		echo "[VM BUILD] Running code build script...";
		BUILD_SCRIPT_STARTS=$(timestamp)
		BUILD_DIR="$BUILD_DIR" "$DIRNAME/scripts/build.sh" &
		pid=$!
		wait $pid || { echo "[VM BUILD] build failed. Aborting..." 2>&2 && echo && exit 1; }
		BUILD_SCRIPT_STOPS=$(timestamp)
		echo "[VM BUILD] Code Build completed! ($(($BUILD_SCRIPT_STOPS-$BUILD_SCRIPT_STARTS)) seconds)" && echo;

	elif [ -z "$(ls -al "$DIRNAME/$BUILD_DIR" | egrep --invert-match '^(.*[ ]((\.)|(\.\.))$)|(total.*$)')" ]; then
		# build folder is empty
		echo "MISSING FILES: build directory is empty." >&2 && echo && exit 1;
	fi

	if [ $BUMP_VERSION = true ]; then
		"$DIRNAME/scripts/bump-version.py" "$BUMP_VER_SIZE" 
		if [ "$?" != 0 ]; then
			echo "[VM BUILD] Error occured. Aborting..." >&2 && echo && exit 1;
		else
			echo && sleep 2s		# Dramatic effect
		fi
	fi

	echo "[APP_DEPLOY] Deploying application to Google Cloud Compute Instance...";
	# ansible build [ host_ips, deployment YAML ]
	# Parameters
	ANSIBLE_CONFIG="${DIRNAME}/scripts/ansible/ansible.cfg"
	PLAYBOOK_VARS=("local_project_dir=${DIRNAME%/}")
	if [ $AUTOSTART == false ]; then
		PLAYBOOK_VARS+=("app_autostart=false")
	fi

	EXTRA_VARS=""  # combine any vars into ansible variable string
	for iVar in ${PLAYBOOK_VARS[@]}; do
		if [ -n "$iVar" ]; then
			if [ -z "$EXTRA_VARS" ]; then
				EXTRA_VARS="$iVar"
			else
				EXTRA_VARS="${EXTRA_VARS} $iVar"
			fi
		fi
	done
	[ -n "$EXTRA_VARS" ] && EXTRA_VARS="--extra-vars \"${EXTRA_VARS}\""

	# Logging steps
	echo "[APP_DEPLOY] Set ANSIBLE_CONFIG=${ANSIBLE_CONFIG}"
	ENV_VARS="ANSIBLE_CONFIG=${ANSIBLE_CONFIG}"
	echo "[APP_DEPLOY]" \
		 "$> $ENV_VARS ansible-playbook" \
			"${EXTRA_VARS}" \
			"$DIRNAME/scripts/ansible/deploy-app-vm.yml"
	
	# actual command
	ANSIBLE_BUILD_STARTS="$(timestamp)"
	/bin/bash -c "$ENV_VARS ansible-playbook $EXTRA_VARS $DIRNAME/scripts/ansible/deploy-app-vm.yml" &
	ansiblePID=$!
	trap "ps -p $ansiblePID > /dev/null && kill $ansiblePID" ERR EXIT
	wait $ansiblePID
	exit_status=$?

	# Handle Ansible build status 
	if [ $exit_status != 0 ]; then
		echo "[VM BUILD] Error occured.  Aborting..." >&2 && echo && exit 1;
	fi

	ANSIBLE_BUILD_STOPS="$(timestamp)"

	echo && echo "[VM BUILD] GCE VM deployed in $(($ANSIBLE_BUILD_STOPS-$ANSIBLE_BUILD_STARTS)) seconds.";

	SCRIPT_STOPS="$(timestamp)"
	echo "[VM BUILD] Total Execution Time: $(($SCRIPT_STOPS-$SCRIPT_STARTS)) seconds" && echo;
	# Instructions
	echo "  APP STATUS  "
	echo " ------------ "
	echo "SERVICE=${NAME}.service";
	echo "APP=$($AUTOSTART && echo 'RUNNING' || echo 'INSTALLED')";
	echo "TO CONNECT:"
	echo "     $> ssh -i ~/.ssh/srvacct-gce sa_117909082819485756837@ip"
	echo "     --or--";
	echo "     $> open http://ip";
	echo "";
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
		trap "ps -p $pid > /dev/null && kill $pid" ERR EXIT
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
