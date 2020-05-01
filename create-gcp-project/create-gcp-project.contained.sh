#!/usr/bin/env bash
# A script that facilitates the creation of a minimal GCP project. The script assumes that you will
# be using terraform downstream and creates configuration/credentials in the volume 
# `/root/.project` to be used by subsequent terraform projects.

USAGE="Usage: create-project.sh <project-name> <billing-account>"

# Extract arguments
PROJECT_NAME=$1
[ -z "${PROJECT_NAME}" ] && die $USAGE 
BILLING_ACCOUNT=$2
[ -z "${BILLING_ACCOUNT}" ] && die $USAGE

# Derive the PROJECT_ID from the PROJECT_NAME
PROJECT_SLUG=$(echo $PROJECT_NAME | tr A-Z a-z | sed -r 's/[^a-z0-9]+/-/g') # crude slug
# The PROJECT_ID maximum is 30 chars.
PROJECT_ID=${PROJECT_SLUG:0:19}-$(date "+%y%m%d%H%M") 

# Default any undefined variables
[ -z "${SA_NAME}" ] && SA_NAME="terraform"
[ -z "${SA_DISPLAY_NAME}" ] && SA_DISPLAY_NAME="Terraform Service Account"
[ -z "${STATE_BUCKET_REGION}" ] && STATE_BUCKET_REGION="europe-west2"
[ -z "${STATE_BUCKET_NAME}" ] && STATE_BUCKET_NAME="$PROJECT_ID-terraform-state"

# The expected service account email address.
SA_EMAIL=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com

# Exit on errors and log commands
set -xe

# make a copy of the gcloud named $PROJECT_SLUG and point gcloud at that.
export CLOUDSDK_CONFIG=/root/.config/$PROJECT_ID
cp -r /root/.config/gcloud $CLOUDSDK_CONFIG

# Create the project.
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME" --set-as-default

# Link the project to a billing account. TODO if there's only one - use that.
gcloud beta billing projects link $PROJECT_ID --billing-account $BILLING_ACCOUNT

# Create service account for the project to be used by terraform.
gcloud iam service-accounts create $SA_NAME --display-name "$SA_DISPLAY_NAME"

# Create and download a set of keys for the service account.
gcloud iam service-accounts keys create /root/.project/$SA_NAME-credentials.json --iam-account $SA_EMAIL

# Assign the "roles/owner" to the service account.
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$SA_EMAIL \
  --role roles/owner

# From this point, all further gcloud operations are performed by the service account
gcloud config set auth/credential_file_override /root/.project/terraform-credentials.json

# Enable the "Cloud Resource Manager" API to enable terraform deployment.
gcloud services enable cloudresourcemanager.googleapis.com

# Create a bucket to store state created by terraform. Buckets must have a unique name which is why
# the project id is included (although this doesn't guarantee it).
gsutil mb -p $PROJECT_ID -l $STATE_BUCKET_REGION gs://$STATE_BUCKET_NAME
gsutil versioning set on gs://$STATE_BUCKET_NAME

# Create a terrform config file that defines the "gcs" backend and the project_id.
cat <<EOF >/root/.project/$PROJECT_ID.tf
locals {
  project_id = "$PROJECT_ID"
}
terraform {
  backend "gcs" {
    bucket="$STATE_BUCKET_NAME"
  }
}
EOF
