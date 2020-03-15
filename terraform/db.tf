resource google_compute_global_address db-private-ip {
  name = "db-private-ip"
  purpose = "VPC_PEERING"
  address_type = "INTERNAL"
  prefix_length = 16
  network = google_compute_network.smallgat.self_link
}

resource google_service_networking_connection cx {
  network = google_compute_network.smallgat.self_link
  service = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.db-private-ip.name]
}

resource google_sql_database_instance smallgat {
  name = "smallgat"
  database_version = "POSTGRES_11"
  depends_on = [google_service_networking_connection.cx]
  settings {
    # note: no SLA on this size. https://cloud.google.com/sql/docs/mysql/upgrade-2nd-gen
    tier = "db-g1-small"
    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.smallgat.self_link
    }
  }
}

output sql_ip { value = google_sql_database_instance.smallgat.private_ip_address }

variable sql_readwrite_password {}

resource google_sql_user readwrite {
  name = "readwrite-2020-03"
  instance = google_sql_database_instance.smallgat.name
  password = var.sql_readwrite_password
}

output sql_user { value = google_sql_user.readwrite.name }
