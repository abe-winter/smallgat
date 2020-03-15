# terraform for beta on google cloud
# this relies on some shell vars and probably won't work without a populated .env-secure in your repo root

variable gcloud_project {}

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

resource google_compute_network smallgat {
  name = "smallgat"
}
