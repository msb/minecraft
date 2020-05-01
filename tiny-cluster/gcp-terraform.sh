#!/usr/bin/env bash

USAGE="Usage: gcp-terraform.sh <project-container> ..."

# Exit on errors and log commands
set -xe

# TODO to be removed when the container is available in Docker Hub.
docker build --tag gcp-terraform . >/dev/null

PROJECT_CONTAINER=$1
[ -z "${PROJECT_CONTAINER}" ] && die $USAGE 

shift

docker run --interactive --tty --rm \
  --volumes-from $PROJECT_CONTAINER \
  --volume dot-terraform-$PROJECT_CONTAINER:/root/.terraform \
  --volume $PWD:/project gcp-terraform $@
