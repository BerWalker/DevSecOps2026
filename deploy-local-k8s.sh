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

if kubectl get namespace vault >/dev/null 2>&1; then
  echo "4. Reloading pods that consume Vault secrets..."
  kubectl rollout restart deployment/postgres-auth deployment/postgres-campaign deployment/postgres-analytics \
    deployment/auth deployment/campaign deployment/analytics deployment/email
  kubectl rollout status deployment/email --timeout=120s
else
  echo "4. Vault namespace not found — run ./vault/deploy-vault.sh before sending emails."
fi

sleep 10

kubectl get pods
kubectl get svc

echo "Local Kubernetes deploy complete."

kubectl port-forward svc/gateway 5000:80