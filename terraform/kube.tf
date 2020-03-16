resource google_container_cluster smallgat {
  provider = google-beta
  name = "smallgat"
  network = google_compute_network.smallgat.self_link
  release_channel {
    channel = "REGULAR"
  }
  ip_allocation_policy {} # yes, blank -- this makes it vpc-native so it can cx to cloud sql

  # TF docs recommend this for ext node pool, which I think I need to set GCR storage perms
  remove_default_node_pool = true
  initial_node_count = 1

  # todo: can this be moved to the node_pool below so it doesn't create a 2nd pool?
  cluster_autoscaling {
    enabled = true
    resource_limits {
      resource_type = "cpu"
      maximum = 4
    }
    resource_limits {
      resource_type = "memory"
      # note: this is gigabytes per https://cloud.google.com/kubernetes-engine/docs/how-to/node-auto-provisioning
      maximum = 6
    }
    auto_provisioning_defaults {
      oauth_scopes = [
        "https://www.googleapis.com/auth/logging.write",
        "https://www.googleapis.com/auth/monitoring",
        "https://www.googleapis.com/auth/devstorage.read_only",
      ]
    }
  }
}

resource google_container_node_pool smallgat {
  name = "primary-pool"
  cluster = google_container_cluster.smallgat.name
  node_count = 1

  node_config {
    preemptible  = true
    machine_type = "n1-standard-1"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only",
    ]
  }
}

data google_compute_default_service_account default {}

variable gcr_storage_bucket {}

# I don't know why this is necessary -- something got broken by my TF destroy
resource "google_storage_bucket_iam_member" "editor" {
  bucket = var.gcr_storage_bucket
  role = "roles/storage.objectViewer"
  # note: service_account here is the string "default", grr
  # member = "serviceAccount:${google_container_cluster.smallgat.node_config[0].service_account}"
  member = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}
