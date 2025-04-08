provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required_services" {
  for_each = toset([
    "run.googleapis.com",
    "speech.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com"
  ])
  service = each.key
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-bot-sa"
  display_name = "Cloud Run Telegram Bot SA"
}

resource "google_project_iam_member" "sa_permissions" {
  for_each = toset([
    "roles/run.invoker",
    "roles/logging.logWriter",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/speech.admin"
  ])
  role   = each.key
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
  project = var.project_id
}

resource "google_secret_manager_secret" "telegram_token" {
  secret_id = var.telegram_bot_token
  replication {
    auto {}
  }
}

resource "google_cloud_run_service" "telegram_service" {
  name     = "telegram-summarizer"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.cloud_run_sa.email
      containers {
        image = var.image_url
        env {
          name  = "telegram_bot_token"
          value = google_secret_manager_secret.telegram_token.id
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.required_services]
}

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.telegram_service.location
  service  = google_cloud_run_service.telegram_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
