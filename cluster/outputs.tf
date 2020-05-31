output "project_id" {
  value       = module.tiny_cluster.project_id
  description = "The id of the cluster's project."
}

output "cluster_name" {
  value       = module.tiny_cluster.cluster_name
  description = "The name of the cluster."
}

output "cluster_zone" {
  value       = module.tiny_cluster.cluster_zone
  description = "The zone of the cluster."
}

output "backup_bucket_name" {
  value = google_storage_bucket.backup_bucket.name
  description = "The name of the bucket for world backups."
}
