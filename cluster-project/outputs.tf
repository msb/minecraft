output "project_id" {
  value       = module.cluster_project.project_id
  description = "The GCP project's id."
}

output "state_bucket_name" {
  value = module.cluster_project.state_bucket_name
  description = "The name of the bucket for terraform state."
}

output "service_account_credentials" {
  sensitive = true
  value     = module.cluster_project.service_account_credentials
  description = "The project service account credentials."
}
