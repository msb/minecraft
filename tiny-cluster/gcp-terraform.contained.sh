#!/usr/bin/env bash

export GOOGLE_CLOUD_KEYFILE_JSON=/root/.project/terraform-credentials.json
export GOOGLE_BACKEND_CREDENTIALS=$GOOGLE_CLOUD_KEYFILE_JSON
export TF_DATA_DIR=/root/.terraform

cp -r /project/* /staging/
cp /root/.project/*.tf /staging/

terraform $@
