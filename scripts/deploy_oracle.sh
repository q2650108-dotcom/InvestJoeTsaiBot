#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER" || true

if [ ! -f .env ]; then
  echo ".env not found. Copy .env.example to .env and fill it first."
  exit 1
fi

docker compose up -d --build
docker compose ps
