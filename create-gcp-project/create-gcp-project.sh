#!/usr/bin/env bash

# Exit on errors and log commands
set -xe

# TODO to be removed when the container is available in Docker Hub.
docker build --tag create-gcp-project . >/dev/null

PROJECT_CONTAINER=$(echo $1 | tr A-Z a-z | sed -r 's/[^a-z0-9]+/-/g') # crude slug

docker run --volumes-from gcloud-config --name $PROJECT_CONTAINER create-gcp-project "$@"
