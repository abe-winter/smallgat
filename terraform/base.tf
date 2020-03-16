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

resource google_project_service registry {
  service = "containerregistry.googleapis.com"
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

# warning: in prod, DNS is managed in domains.google -- the cloud DNS records are an illusion
resource google_dns_record_set naked {
  name = google_dns_managed_zone.smallgat.dns_name
  managed_zone = google_dns_managed_zone.smallgat.name
  type = "A"
  ttl = 300
  rrdatas = [google_compute_global_address.smallgat.address]
}

# note: G recommends `gcloud auth configure-docker`
# but it seems not to work, hence this spaghetti
resource google_service_account image_pusher {
  account_id = "image-pusher"
  description = "push docker images, because cred helper isn't working"
}

resource google_project_iam_member storage_role {
  role = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.image_pusher.email}"
}

output pusher_email { value = google_service_account.image_pusher.email }

# gcloud iam service-accounts keys create keyfile.json --iam-account [NAME]@[PROJECT_ID].iam.gserviceaccount.com
