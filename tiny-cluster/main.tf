# main.tf contains the top-level resources created by this module.

# Additional services on the project required for cluster.

resource "google_project_service" "compute_api" {
  project            = local.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "container_api" {
  project            = local.project_id
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

locals {
  cluster_name = lookup(local.default, "cluster_name", "tiny-cluster")
  cluster_zone = lookup(local.default, "cluster_zone", "europe-west1-b")
  node_pool_name = lookup(local.default, "node_pool_name", "node-pool-single-small")
}

# The cluster

resource "google_container_cluster" "primary" {
  project  = local.project_id
  name     = local.cluster_name
  location = local.cluster_zone

  remove_default_node_pool = true
  initial_node_count       = 1

  master_auth {
    username = ""
    password = ""

    client_certificate_config {
      issue_client_certificate = false
    }
  }

  depends_on = [
    google_project_service.container_api,
    google_project_service.compute_api,
  ]
}

# The cluster's default node pool

resource "google_container_node_pool" "primary_preemptible_nodes" {
  project    = local.project_id
  name       = local.node_pool_name
  location   = local.cluster_zone
  cluster    = google_container_cluster.primary.name
  node_count = 1

  node_config {
    preemptible  = true
    machine_type = "g1-small"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }
}
