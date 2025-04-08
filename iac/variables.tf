variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "image_url" {
  type = string
  description = "Docker image URL for Cloud Run service"
}

variable "telegram_bot_token" {
  type = string
  description = "Telegram bot token secret"
}
