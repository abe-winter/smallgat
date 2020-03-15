# terraform for beta on google cloud
# this relies on some shell vars and probably won't work without a populated .env-secure in your repo root

variable gcloud_project {}
variable domain_name {}

provider google {
  project = var.gcloud_project
  zone = "us-central1-a"
}

provider google-beta {
  project = var.gcloud_project
  zone = "us-central1-a"
}

resource google_project_service geocoding {
  service = "geocoding-backend.googleapis.com"
}

resource google_project_service stackdriver {
  service = "stackdriver.googleapis.com"
}

resource google_compute_network smallgat {
  name = "smallgat"
}

resource google_dns_managed_zone smallgat {
  name = "smallgat"
  dns_name = var.domain_name
}

resource google_compute_global_address smallgat {
  name = "smallgat-ingress"
}

resource google_dns_record_set naked {
  name = google_dns_managed_zone.smallgat.dns_name
  managed_zone = google_dns_managed_zone.smallgat.name
  type = "A"
  ttl = 300
  rrdatas = [google_compute_global_address.smallgat.address]
}
