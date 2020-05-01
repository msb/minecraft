This container wraps a script that facilitates the creation of a minimal
[GCP project](https://cloud.google.com/storage/docs/projects). The script assumes that you will be
using terraform to create project resources and creates configuration/credentials in the volume
`/root/.project` to be used by subsequent terraform projects. The script does the following:

- Create the project and attach it to the billing account.
- Create a service account and retrieve it's credentials.
- Create a bucket to be used to store erraform state.

To bootstrap your local environment ready to create one of more projects:

- [Signup for a GCP account](https://cloud.google.com/gcp), if you don't already have them. There's
  a free trial and at time of writing it's quite generous (credits $300 for 12 months whichever
  finishes 1st).
- Use the `google/cloud-sdk container` to retrieve your account's credentials with the following
  command: `docker run -it --name gcloud-config google/cloud-sdk gcloud auth login` - then follow
  the instructions. As described on 
  [Docker Hub](https://hub.docker.com/r/google/cloud-sdk), the credentials are saved in a volume of
  the container.
- Lookup your [Billing account ID](https://console.cloud.google.com/billing). TODO this should be
  automated.

To create a project:

- [A helper script](https://github.com/msb/minecraft/blob/master/create-gcp-project/create-gcp-project.sh)
  is provided to run the container:
  `source ./create-gcp-project.sh {Project Name} {Billing account ID}`. When completed, the project
  can seen in [the console](https://console.cloud.google.com/cloud-resource-manager). The script
  will also create a `PROJECT_CONTAINER` variable with the name of the container just run. This is
  to be used downstream when running terraform.

Ideally I would like project creation to be performed by terraform. However, to be able to do this,
it seems you need a service account with organisation level "project create" privileges and I
assume there is cost involved in an account with organisations. However, please feel free to
suggest other possible approaches.
