#!/usr/bin/env bash
set -e

echo "==> [1/3] Preparing workspace and cleaning cache..."
rm -rf dist app_artifact.tar.gz
mkdir -p dist

echo "==> [2/3] Generating build artifact..."
# Пакуем код в артефакт (исключая лишнее)
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='dist' \
    -czf dist/app_artifact.tar.gz main.py requirements.txt

echo "Artifact created at: dist/app_artifact.tar.gz"

echo "==> [3/3] Building Docker image..."
docker build -t devops-app:latest .

echo "Build process completed successfully."