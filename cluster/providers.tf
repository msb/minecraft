# the google provider with credentials and project context
provider "google" {
  credentials = file("/project/service_account_credentials.json")
  project     = local.project_id
}

# the gitlab provider (for backup process)
provider "gitlab" {
  token = local.gitlab_token
}
