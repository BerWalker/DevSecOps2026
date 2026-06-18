#!/bin/bash
set -e

echo "1. Building local images..."
docker build -f frontend/Dockerfile -t frontend:latest .
docker build -f services/auth/Dockerfile -t auth:latest .
docker build -f services/campaign/Dockerfile -t campaign:latest .
docker build -f services/analytics/Dockerfile -t analytics:latest .
docker build -f services/email/Dockerfile -t email:latest .

echo "2. Loading images into Minikube..."
minikube image load frontend:latest
minikube image load auth:latest
minikube image load campaign:latest
minikube image load analytics:latest
minikube image load email:latest

echo "3. Applying Kubernetes manifests..."
kubectl apply -k kubernetes/

sleep 15

kubectl get pods
kubectl get svc

echo "Local Kubernetes deploy complete."
echo "If you are using Kind or Minikube and the cluster cannot see local Docker images, load the images manually before running this script."
