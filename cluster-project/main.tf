# The minecraft cluster's GCP project
module "cluster_project" {
  source = "git::https://github.com/msb/tf-gcp-project.git"

  project_name    = "Minecraft"
  additional_apis = [
    "compute.googleapis.com",
    "container.googleapis.com"
  ]
}
