#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"

get_env() {
  local key="$1"
  local default="$2"
  if [[ -f "$ENV_FILE" ]]; then
    local line
    line=$(grep -E "^${key}=" "$ENV_FILE" | head -1 || true)
    if [[ -n "$line" ]]; then
      echo "${line#*=}"
      return
    fi
  fi
  echo "$default"
}

if helm status vault -n vault >/dev/null 2>&1; then
  echo "Removing existing Vault Helm release..."
  helm uninstall vault -n vault
fi

if kubectl get namespace vault >/dev/null 2>&1; then
  echo "Deleting existing vault namespace..."
  kubectl delete namespace vault
fi

echo "0. Setting up namespace..."
kubectl create namespace vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

echo "1. Installing Vault via Helm..."
helm install vault hashicorp/vault --namespace vault -f vault/override-values.yaml

echo "2. Waiting for vault-0 pod to start..."
echo "Waiting for vault-0 pod to be created..."
for i in $(seq 1 30); do kubectl get pod/vault-0 -n vault &>/dev/null && break || sleep 2; done
kubectl wait --for=jsonpath='{.status.phase}'=Running pod/vault-0 -n vault --timeout=120s
kubectl get pods -n vault

echo "3. Initializing Vault and capturing keys..."
INIT_RESPONSE=$(kubectl exec -n vault vault-0 -- vault operator init -format=json | tr -d '\r')

# Extract keys in one pass; shlex.quote avoids Windows/Git Bash mangling base64 (+, /, =)
eval "$(echo "$INIT_RESPONSE" | python -c "
import json, sys, shlex
data = json.load(sys.stdin)
for i, key in enumerate(data['unseal_keys_b64'][:3], start=1):
    print(f'KEY_{i}={shlex.quote(key.strip())}')
print(f'ROOT_TOKEN={shlex.quote(data[\"root_token\"].strip())}')
")"

if [[ -z "$KEY_1" || -z "$KEY_2" || -z "$KEY_3" || -z "$ROOT_TOKEN" ]]; then
  echo "ERROR: Failed to extract unseal keys or root token from vault operator init."
  exit 1
fi

echo "Vault Initialized!"
echo "WARNING - SAVE THIS ROOT TOKEN: $ROOT_TOKEN"
echo "Keys temporarily saved in memory to unseal the nodes."

echo "4. Unsealing vault-0 (Leader)..."
kubectl exec -n vault vault-0 -- vault operator unseal "$KEY_1" > /dev/null
kubectl exec -n vault vault-0 -- vault operator unseal "$KEY_2" > /dev/null
kubectl exec -n vault vault-0 -- vault operator unseal "$KEY_3" > /dev/null

echo "Waiting for Raft cluster to form and followers to sync state..."
sleep 15

echo "5. Unsealing vault-1..."
kubectl exec -n vault vault-1 -- vault operator unseal "$KEY_1" > /dev/null
kubectl exec -n vault vault-1 -- vault operator unseal "$KEY_2" > /dev/null
kubectl exec -n vault vault-1 -- vault operator unseal "$KEY_3" > /dev/null

echo "Waiting for Raft cluster to form and followers to sync state..."
sleep 15

echo "6. Unsealing vault-2..."
kubectl exec -n vault vault-2 -- vault operator unseal "$KEY_1" > /dev/null
kubectl exec -n vault vault-2 -- vault operator unseal "$KEY_2" > /dev/null
kubectl exec -n vault vault-2 -- vault operator unseal "$KEY_3" > /dev/null

echo "Vault Cluster is 100% up and unsealed!"
kubectl get pods -n vault
kubectl get svc -n vault vault-ui

# Set the token for the current session inside commands
export VAULT_TOKEN=$ROOT_TOKEN
export VAULT_ADDR="http://127.0.0.1:8200"

echo "7. Enabling KV Secrets Engine..."
kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault secrets enable -path=secret kv-v2" 2>/dev/null || true

echo "8. Writing application secrets to Vault..."
INTERNAL_API_KEY="$(get_env INTERNAL_API_KEY 'change-me-internal-key')"
JWT_SECRET_KEY="$(get_env JWT_SECRET_KEY 'super-secret-key')"
GMAIL_FROM="$(get_env GMAIL_FROM 'your@gmail.com')"
GMAIL_USER="$(get_env GMAIL_USER "$GMAIL_FROM")"
GMAIL_APP_PASSWORD="$(get_env GMAIL_APP_PASSWORD 'xxxx xxxx xxxx xxxx')"

kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault kv put secret/my-app/env \
  INTERNAL_API_KEY='${INTERNAL_API_KEY}' \
  AUTH_POSTGRES_USER='auth' \
  AUTH_POSTGRES_DB='auth_db' \
  AUTH_DATABASE_URL='postgresql+psycopg://auth:auth@postgres-auth:5432/auth_db' \
  AUTH_POSTGRES_PASSWORD='auth' \
  CAMPAIGN_POSTGRES_USER='campaign' \
  CAMPAIGN_POSTGRES_DB='campaign_db' \
  CAMPAIGN_DATABASE_URL='postgresql+psycopg://campaign:campaign@postgres-campaign:5432/campaign_db' \
  CAMPAIGN_POSTGRES_PASSWORD='campaign' \
  ANALYTICS_POSTGRES_USER='analytics' \
  ANALYTICS_POSTGRES_DB='analytics_db' \
  ANALYTICS_DATABASE_URL='postgresql+psycopg://analytics:analytics@postgres-analytics:5432/analytics_db' \
  ANALYTICS_POSTGRES_PASSWORD='analytics' \
  JWT_SECRET_KEY='${JWT_SECRET_KEY}' \
  GMAIL_FROM='${GMAIL_FROM}' \
  GMAIL_USER='${GMAIL_USER}' \
  GMAIL_APP_PASSWORD='${GMAIL_APP_PASSWORD}' \
  SMTP_HOST='$(get_env SMTP_HOST 'smtp.gmail.com')' \
  SMTP_PORT='$(get_env SMTP_PORT '587')'"

echo "9. Enabling Kubernetes Auth Method..."
kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault auth enable kubernetes" 2>/dev/null || true

echo "10. Configuring Kubernetes Auth (must run inside vault-0 — host env vars are empty)..."
kubectl exec -n vault vault-0 -- sh -c "
export VAULT_TOKEN='${ROOT_TOKEN}'
JWT=\$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
vault write auth/kubernetes/config \
  kubernetes_host=\"https://\${KUBERNETES_SERVICE_HOST}:\${KUBERNETES_SERVICE_PORT:-443}\" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt=\"\${JWT}\"
"

echo "11. Creating Read-Only Policy..."
kubectl exec -n vault -i vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault policy write my-app-policy -" <<EOF
path "secret/data/my-app/env" {
  capabilities = ["read"]
}
EOF

echo "12. Binding Policy to Service Account..."
kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault write auth/kubernetes/role/my-app-role \
    bound_service_account_names=my-app-sa \
    bound_service_account_namespaces=default \
    policies=my-app-policy \
    ttl=1h"

echo "13. Restarting app pods to load Vault secrets into running processes..."
kubectl rollout restart deployment/postgres-auth deployment/postgres-campaign deployment/postgres-analytics \
  deployment/auth deployment/campaign deployment/analytics deployment/email 2>/dev/null || true
kubectl rollout status deployment/email --timeout=120s 2>/dev/null || true

echo "14. Setup complete. Starting port-forwarding (Press Ctrl+C to stop)..."
kubectl port-forward svc/vault-ui 8200:8200 -n vault &