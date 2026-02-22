# Ads Ingestion Service

High-availability ingestion service designed for real-time ad metrics.

## Features

- Async queue buffering
- Batch processing
- Backpressure (HTTP 429)
- Prometheus metrics
- Kubernetes ready
- Jenkins CI/CD pipeline

## Run locally

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080

## Docker

docker build -t ads-ingestion-service .
docker run -p 8080:8080 ads-ingestion-service

