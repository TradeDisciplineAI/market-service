# ☸️ Kubernetes Setup Guide for Market Service

This folder contains production-ready Kubernetes (k8s) manifests for deploying **`market-service`**, Redis broker, Celery worker pods, and Celery beat task scheduler.

---

## 📁 Manifest Directory Overview

| Manifest File | Purpose & Resources Defined |
| :--- | :--- |
| **`namespace.yaml`** | Namespace `market-service` for workload isolation. |
| **`configmap.yaml`** | Non-sensitive environment variables (`PORT`, `ENVIRONMENT`, `LOG_LEVEL`). |
| **`secret.example.yaml`** | Secret template for database credentials, Redis URLs, and API keys. |
| **`deployment.yaml`** | Deployment manifest for `market_app` containers with `/health` liveness & readiness probes. |
| **`service.yaml`** | `ClusterIP` Service exposing port `8001` internally. |
| **`redis-deployment.yaml` & `redis-service.yaml`** | Deployment & Service for Redis cache and Celery broker. |
| **`celery-deployment.yaml` & `celery-beat-deployment.yaml`** | Deployments for background Celery worker and beat scheduler. |

---

## 🚀 Quick Deployment Guide

### Step 1: Create Secret File
Copy the example secret file and update sensitive credentials:
```bash
cp k8s/secret.example.yaml k8s/secret.yaml
```

### Step 2: Apply Manifests
Apply all manifests in the correct order:
```bash
# 1. Create Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply ConfigMap & Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Deploy Redis Cache & Broker
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# 4. Deploy Market Service Web App & Celery Workers
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/celery-beat-deployment.yaml
```

### Step 3: Verify Deployment Health
```bash
# Check pod status in market-service namespace
kubectl get pods -n market-service

# Check services
kubectl get svc -n market-service
```
