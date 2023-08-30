#!/bin/sh
# Shell utility functions for git-hooks
# --------------------------------------
[ -z "$LOG_PREFIX" ] && LOG_PREFIX="[./scripts/.git-hooks/???]"

GIT_LFS_ENABLED=false

# as opposed to echo, interpret C escape sequences properly in all envs
replay() {
    printf '%s\n' "$*"
}

# Print to stdout as messages with a prefix of $LOG_PREFIX
log() {
    replay "$*" | awk -v "PREFIX=$LOG_PREFIX" -F '\\\\n' '{print PREFIX " " $1}'
}

# Print to stderr as messages with a prefix of $LOG_PREFIX
error() {
    replay "$*" | awk >&2 -v "PREFIX=$LOG_PREFIX" -F '\\\\n' '{print PREFIX " " $1}'
}

# Prints and runs command
explicit_run_cmd() {
    cmd="$1"
    log "$> $cmd"
    eval "$cmd"
}

# Function to check for modified pyproject.toml file in merged file list
contains_pyprojecttoml_file() {
    # args: [file [file ...]]
    # list of filenames to match against
    if ! replay "$*" | grep --quiet "pyproject.toml"; then
        return 1 # no change
    fi
    log "CHANGE DETECTED: 'pyproject.toml'"
}

# Function to update Python project dependencies
update_python_deps() {
    PIP_EXE="$VIRTUAL_ENV/bin/pip"

    if ! [ -e "$PIP_EXE" ]; then
        log "PIP not found on \$PATH, however 'pip install' is desired. Please accomplish manually."
        return 1
    fi

    if ! explicit_run_cmd "$PIP_EXE install -U -e .[build,dev,test]"; then
        error "ERROR: Dependency installation failed."
        error "You will need to perform a pip install or fix build issues manually to continue."
        unset -v PIP_EXE
        return 1
    fi
    unset -v PIP_EXE
}

# Function to configure git repository to include project `.gitconfig`
config_git_project_gitconfig() {
    current_includepath="$(git config --local --get include.path || true)"
    project_gitconfig_file="../.gitconfig"
    if [ -f ".git" ]; then # check if repo is a submodule (ie. .git is a file instead of directory)
        if ! output="$(git config --get core.worktree)"; then
            error "ERROR: unable to determine the submodule location path."
            error "ERROR: failed to add project .gitconfig to local git configuration."
            return 1
        fi
        # prepend worktree to the project gitconfig path => large relative path from top level .git/modules/*
        project_gitconfig_file="${output}/${project_gitconfig_file##*/}"
        unset -v output
    fi
    if [ "$current_includepath" = "$project_gitconfig_file" ]; then
        unset -v current_includepath project_gitconfig_file
        return 0 # As desired, return silently
    fi
    unset -v current_includepath
    if [ -f "$(basename "$project_gitconfig_file")" ]; then
        if ! git config --local include.path "$project_gitconfig_file"; then
            error "ERROR: failed to add project .gitconfig to local git configuration."
            unset -v project_gitconfig_file
            return 1
        fi
        log "SUCCESS: Project .gitconfig added to repository configuration."
    fi
    unset -v project_gitconfig_file
}

# Function to configure git repository to enforce GPG signed commits
config_git_commit_signing() {
    # check if configured properly
    if ! output="$(git config --get commit.gpgsign 2>/dev/null)"; then
        error "ERROR: missing commit.gpgsign setting in git config."
        return 1
    elif ! [ "$output" = "true" ]; then
        error "ERROR: commit.gpgsign must be set to true for project."
        return 1
    fi
    if ! git config --get user.signingkey 1>/dev/null 2>&1; then
        log "==============================================================="
        log "                   USER ACTION REQUIRED!"
        log "---------------------------------------------------------------"
        log "GPG commit signing is required for this repository! Please"
        log "configure your repository with the following command:"
        log "" # prefixed-newline
        log "    git config --local user.signingkey <GPG_KEY_ID>"
        log "" # prefixed-newline
        log "==============================================================="
    elif [ "$IS_CLONING" = "true" ]; then
        log "Signature exists: user.signingkey=$(git config --get user.signingkey)"
    fi
}

# POSIX Compliant & portable (X-OS) realpath implementation
realpath() {
    OURPWD="$PWD"
    cd "$(dirname "$1")" || return 1
    LINK=$(readlink "$(basename "$1")") || true
    while [ "$LINK" ]; do
        cd "$(dirname "$LINK")" || return 1
        LINK=$(readlink "$(basename "$1")") || true
    done
    REALPATH="$PWD/$(basename "$1")"
    cd "$OURPWD" || return 1
    echo "$REALPATH"
    unset -v OURPWD LINK REALPATH
    return 0
}

# Resolves project directory
get_project_dir() {
    directory=""
    if ! directory="$(git rev-parse --show-toplevel)"; then
        error "ERROR: Unable to determine project directory."
        exit 1
    fi
    if ! directory="$(realpath "$directory")"; then
        error "ERROR: Unable to determine absolute path of project directory."
        exit 1
    fi
    replay "$directory"
    unset -v directory
    return 0
}

# cross-linux function
make_tmpfile() {
    cmd_name="mktmp"
    if ! command -v "$cmd_name" 1>/dev/null 2>&1; then
        cmd_name="mktemp" # Mac OS
        if ! command -v "$cmd_name" 1>/dev/null 2>&1; then
            error "ERROR: unable to find command to create temporary file."
            unset -v cmd_name
            return 1
        fi
    fi
    replay "$($cmd_name)"
    unset -v cmd_name
}

# Unset all functions/vars this utils file creates
cleanup() {
    unset -v LOG_PREFIX VIRTUAL_ENV GIT_LFS_ENABLED PROJ_DIR
    unset -f cleanup replay log error explicit_run_cmd \
        config_git_project_gitconfig config_git_commit_signing \
        realpath get_project_dir make_tmpfile \
        update_python_deps contains_pyprojecttoml_file
}

# Virtual environment detection
if [ -z "$VIRTUAL_ENV" ]; then
    PROJ_DIR="$(get_project_dir || echo "../..")"

    if [ -e "$PROJ_DIR/.venv/pyvenv.cfg" ]; then
        VIRTUAL_ENV="$PROJ_DIR/.venv"
    elif [ -e "$PROJ_DIR/venv/pyvenv.cfg" ]; then
        VIRTUAL_ENV="$PROJ_DIR/venv"
    fi
fi
