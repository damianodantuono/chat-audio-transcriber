output "cloud_run_url" {
  value = google_cloud_run_service.telegram_service.status[0].url
}
