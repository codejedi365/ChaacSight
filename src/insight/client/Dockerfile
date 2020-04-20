# =================================== #
# Docker build for webserver Insight  #
# =================================== #
# @codejedi365
# Alpine usage for minimal size
# -----------------------------------


# =================== #
# ***** STAGE 1 ***** #
# =================== #
FROM node:current-alpine as build-stage
WORKDIR /usr/src/chaac-insight

## Developer Tools
# install yarn (js package manager)
RUN apk add yarn
# RUN apk add UnZip
# RUN apk add cURL

# pull production code from git repository
RUN curl -L https://github.com/codejedi365/ChaacSight/archive/master.zip -o /tmp/archive.zip
# unzip code
RUN unzip /tmp/archive.zip /tmp/archive
RUN cp -r /tmp/archive/src/insight/client/* .
RUN rm -r /tmp/*
# OR #
# Use Local Code
# COPY package*.json ./
# COPY ./ .

## Install Dependencies
RUN yarn install

## Compile application code
RUN npm run build

ENTRYPOINT [ "npm" ]
CMD [ "run", "serve" ]


# =================== #
# ***** STAGE 2 ***** #
# =================== #
FROM nginx:alpine as production-stage
WORKDIR /opt/chaac-insight
COPY --from=build-stage /usr/src/chaac-insight/dist .
COPY --from=build-stage /usr/src/chaac-insight/nginx.conf /etc/nginx/nginx.conf
## Lock root account
RUN passwd --delete --lock root
# Load log monitor?


