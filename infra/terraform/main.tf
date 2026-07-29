terraform {
  required_version = ">= 1.5"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ── Network ──

resource "docker_network" "devstation" {
  name = "devstation-network"
}

# ── Database ──

resource "docker_image" "postgres" {
  name = "postgres:16-alpine"
}

resource "docker_container" "db" {
  name  = "devstation-tf-db"
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=devstation",
    "POSTGRES_PASSWORD=changeme",
    "POSTGRES_DB=devstation",
  ]

  ports {
    internal = 5432
    external = 5433
  }

  networks_advanced {
    name = docker_network.devstation.name
  }
}

# ── API ──

resource "docker_image" "api" {
  name = "devstation-api:latest"
}

resource "docker_container" "api" {
  name  = "devstation-tf-api"
  image = docker_image.api.image_id

  env = [
    "DATABASE_URL=postgresql://devstation:changeme@devstation-tf-db:5432/devstation",
  ]

  ports {
    internal = 8000
    external = 8001
  }

  networks_advanced {
    name = docker_network.devstation.name
  }

  depends_on = [docker_container.db]
}

# ── Outputs ──

output "api_url" {
  value = "http://localhost:8001"
}

output "db_port" {
  value = "localhost:5433"
}