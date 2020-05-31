# The minecraft cluster
module "tiny_cluster" {
  source = "git::https://github.com/msb/tf-tiny-cluster.git"

  machine_type   = "n1-standard-1"
  node_pool_name = "node-pool-single-standard"
}

# The name of the world backup bucket
resource "random_id" "backup_bucket" {
  byte_length = 3
  prefix      = "world-backup-"
}

# A storage bucket to store world backups
resource "google_storage_bucket" "backup_bucket" {
  name     = random_id.backup_bucket.hex
  location = "europe-west2"

  versioning {
    enabled = true
  }
}

# The following resources deploy a CI/CD schedule to a GitLab project for performing a daily backup
# of world data (not strictly what it was intended for).

# The backup schedule

resource "gitlab_pipeline_schedule" "backup" {
   project     = local.gitlab_minecraft_backups_project_id
   description = "Performs a daily backup of minecraft"
   ref         = "master"
   cron        = local.backup_cron
}

# variables required by the CI/CD backup script (which follows `backup.sh` very closely)

resource "gitlab_project_variable" "project_id" {
  project           = local.gitlab_minecraft_backups_project_id
  key               = "PROJECT_ID"
  value             = module.tiny_cluster.project_id
  protected         = true
  environment_scope = "*"
}

resource "gitlab_project_variable" "cluster_name" {
  project           = local.gitlab_minecraft_backups_project_id
  key               = "CLUSTER_NAME"
  value             = module.tiny_cluster.cluster_name
  protected         = true
  environment_scope = "*"
}

resource "gitlab_project_variable" "cluster_zone" {
  project           = local.gitlab_minecraft_backups_project_id
  key               = "CLUSTER_ZONE"
  value             = module.tiny_cluster.cluster_zone
  protected         = true
  environment_scope = "*"
}

resource "gitlab_project_variable" "backup_bucket_name" {
  project           = local.gitlab_minecraft_backups_project_id
  key               = "BACKUP_BUCKET_NAME"
  value             = google_storage_bucket.backup_bucket.name
  protected         = true
  environment_scope = "*"
}

resource "gitlab_project_variable" "service_account_credentials" {
  project           = local.gitlab_minecraft_backups_project_id
  key               = "SERVICE_ACCOUNT_CREDENTIALS"
  value             = file("/project/service_account_credentials.json")
  protected         = true
  environment_scope = "*"
  variable_type     = "file"
}
