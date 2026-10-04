#!/usr/bin/env bash
set -e

echo "==> [1/3] Deploying containers via Docker Compose..."
docker compose down
docker compose up -d --build

echo "==> [2/3] Waiting for service to initialize..."
sleep 5

echo "==> [3/3] Running healthcheck validation..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "Deployment successful: Application is healthy."
    echo "Dashboard available at: http://localhost:8000"
    echo "Metrics available at:   http://localhost:9090"
else
    echo "Deployment failed: Healthcheck endpoint did not return 200 OK."
    exit 1
fi