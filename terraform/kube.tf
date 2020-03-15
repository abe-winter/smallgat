resource google_container_cluster smallgat {
  provider = google-beta
  name = "smallgat"
  initial_node_count = 1
  network = google_compute_network.smallgat.self_link

  release_channel {
    channel = "REGULAR"
  }

  ip_allocation_policy {} # yes, blank -- this makes it vpc-native so it can cx to cloud sql

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
  }

  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }
}
