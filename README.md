# Ads Ingestion Service

High-availability ingestion service designed for real-time ad metrics.

## Architecture

<img width="1357" height="796" alt="image" src="https://github.com/user-attachments/assets/2e87b654-0aa2-4889-a96d-1e58bb67dd56" />

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


## Branch Strategy

- `main` → Production
- `develop` → Development integration
- `qa` → QA environment
- `staging` → Staging environment
- `feature/*` → Feature development
- `hotfix/*` → Production hotfix

  Branch-Driven Deployment Strategy:

This repository follows a branch-driven deployment model, where each Git branch maps directly to a specific environment. This ensures clarity, automation, and controlled promotion of code from development to production.

<img width="468" height="300" alt="image" src="https://github.com/user-attachments/assets/d89cf368-feb5-4979-b7a4-44a03e2ae7d1" />


## Features

- Async queue buffering with backpressure
- Batch processing
- Structured logging
- Prometheus metrics
- Kubernetes ready (Deployment + HPA + PDB)
- CI/CD with Jenkins

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
