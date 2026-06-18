#!/bin/bash
set -e

# =============================================================================
# CI-only Vault deployment script.
# Uses dev mode (auto-initialized, auto-unsealed, single replica).
# Much simpler than deploy-vault.sh which targets production-like HA setups.
# =============================================================================

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

ROOT_TOKEN="ci-root-token"

# --- 0. Cleanup any previous run ---
helm uninstall vault -n vault 2>/dev/null || true
kubectl delete namespace vault --wait=false 2>/dev/null || true
# Wait briefly for namespace deletion to propagate
sleep 3

# --- 1. Install Vault in dev mode ---
echo "1. Setting up namespace and installing Vault (dev mode)..."
kubectl create namespace vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --namespace vault \
  -f vault/ci-values.yaml \
  --wait \
  --timeout=120s

echo "   Vault is ready (dev mode — auto-initialized, auto-unsealed)."
kubectl get pods -n vault

# --- 2. Write application secrets ---
echo "2. Writing application secrets to Vault..."
kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault secrets enable -path=secret kv-v2" 2>/dev/null || true

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

# --- 3. Enable and configure Kubernetes auth ---
echo "3. Enabling Kubernetes Auth Method..."
kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault auth enable kubernetes" 2>/dev/null || true

echo "4. Configuring Kubernetes Auth..."
kubectl exec -n vault vault-0 -- sh -c "
export VAULT_TOKEN='${ROOT_TOKEN}'
JWT=\$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
vault write auth/kubernetes/config \
  kubernetes_host=\"https://\${KUBERNETES_SERVICE_HOST}:\${KUBERNETES_SERVICE_PORT:-443}\" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt=\"\${JWT}\"
"

# --- 4. Create policy and role ---
echo "5. Creating Read-Only Policy..."
kubectl exec -n vault -i vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault policy write my-app-policy -" <<EOF
path "secret/data/my-app/env" {
  capabilities = ["read"]
}
EOF

echo "6. Binding Policy to Service Account..."
kubectl exec -n vault vault-0 -- sh -c "VAULT_TOKEN='$ROOT_TOKEN' vault write auth/kubernetes/role/my-app-role \
    bound_service_account_names=my-app-sa \
    bound_service_account_namespaces=default \
    policies=my-app-policy \
    ttl=1h"

echo "7. CI Vault setup complete!"
kubectl get pods -n vault
