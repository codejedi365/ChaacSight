# ==================================== #
# Docker build for Insight API server  #
# ==================================== #
# @codejedi365
# -----------------------------------


# =================== #
# ***** STAGE 1 ***** #
# =================== #
FROM python:3.5-alpine as build-stage
WORKDIR /usr/src/chaac-api

## Developer Tools
RUN pip install pipenv
# needs ldd (musl libc), objdump, objcopy
RUN apk add binutils
RUN pip install pyinstaller

# RUN apk add UnZip
# RUN apk add cURL

# pull production code from git repository
RUN curl -L https://github.com/codejedi365/ChaacSight/archive/master.zip -o /tmp/archive.zip
# unzip code
RUN unzip /tmp/archive.zip /tmp/archive
RUN cp -r /tmp/archive/src/insight/server/* .
RUN rm -r /tmp/*

## Install Dependencies
RUN pipenv install --ignore-pipfile

## Compile application code
# RUN pyinstaller <file>
# RUN pyinstaller <file>.spec


# =================== #
# ***** STAGE 2 ***** #
# =================== #
FROM alpine:latest as production-stage
WORKDIR /opt/chaac-api
# RUN apk add glibc
COPY --from=build-stage /usr/src/chaac-api/dist/* .
## Lock root account
RUN passwd --delete --lock root
# Load log monitor?

# # Enable script to execute & add entry into /usr/bin for app start
# RUN chmod +x ./main.py

# ## Build System Daemon (no-user-group, system daemon, set $HOME)
RUN useradd --system --no-user-group --gid daemon chaacapid

# ## Create output log location
RUN mkdir -p "/var/log/chaac-api" \
	&& chown chaacapid "/var/log/chaac-api"

# ## Run as daemon user
USER chaacapid
CMD [ ./run.py ]

