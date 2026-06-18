#!/bin/bash
set -e

helm uninstall vault -n vault
kubectl delete namespace vault

echo "0. Setting up namespace..."
kubectl create namespace vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

echo "1. Installing Vault via Helm..."
helm install vault hashicorp/vault --namespace vault -f vault/override-values.yaml

echo "2. Waiting for vault-0 pod to start..."
sleep 10
kubectl get pods -n vault

echo "3. Initializing Vault and capturing keys..."
# The -format=json parameter allows jq to parse the data
INIT_RESPONSE=$(kubectl exec -n vault vault-0 -- vault operator init -format=json)

# Extracting the unseal keys and the Root Token
KEY_1=$(echo $INIT_RESPONSE | jq -r '.unseal_keys_b64[0]')
KEY_2=$(echo $INIT_RESPONSE | jq -r '.unseal_keys_b64[1]')
KEY_3=$(echo $INIT_RESPONSE | jq -r '.unseal_keys_b64[2]')
ROOT_TOKEN=$(echo $INIT_RESPONSE | jq -r '.root_token')

echo "Vault Initialized!"
echo "WARNING - SAVE THIS ROOT TOKEN: $ROOT_TOKEN"
echo "Keys temporarily saved in memory to unseal the nodes."

echo "4. Unsealing vault-0 (Leader)..."
kubectl exec -n vault vault-0 -- vault operator unseal $KEY_1 > /dev/null
kubectl exec -n vault vault-0 -- vault operator unseal $KEY_2 > /dev/null
kubectl exec -n vault vault-0 -- vault operator unseal $KEY_3 > /dev/null

echo "Waiting for Raft cluster to form and followers to sync state..."
sleep 15

echo "5. Unsealing vault-1..."
kubectl exec -n vault vault-1 -- vault operator unseal $KEY_1 > /dev/null
kubectl exec -n vault vault-1 -- vault operator unseal $KEY_2 > /dev/null
kubectl exec -n vault vault-1 -- vault operator unseal $KEY_3 > /dev/null

echo "Waiting for Raft cluster to form and followers to sync state..."
sleep 15

echo "6. Unsealing vault-2..."
kubectl exec -n vault vault-2 -- vault operator unseal $KEY_1 > /dev/null
kubectl exec -n vault vault-2 -- vault operator unseal $KEY_2 > /dev/null
kubectl exec -n vault vault-2 -- vault operator unseal $KEY_3 > /dev/null

echo "Vault Cluster is 100% up and unsealed!"
kubectl get pods -n vault
kubectl get svc -n vault vault-ui

# Define o token para a sessão atual dentro dos comandos
export VAULT_TOKEN=$ROOT_TOKEN
export VAULT_ADDR="http://127.0.0.1:8200"

echo "7. Enabling KV Secrets Engine..."
kubectl exec -n vault vault-0 -- vault login $ROOT_TOKEN > /dev/null
kubectl exec -n vault vault-0 -- vault secrets enable -path=secret kv-v2

echo "8. Writing application secrets to Vault..."
kubectl exec -n vault vault-0 -- vault kv put secret/my-app/env \
  INTERNAL_API_KEY="change-me-internal-key" \
  AUTH_POSTGRES_USER="auth" \
  AUTH_POSTGRES_DB="auth_db" \
  AUTH_DATABASE_URL="postgresql+psycopg://auth:auth@postgres-auth:5432/auth_db" \
  AUTH_POSTGRES_PASSWORD="auth" \
  CAMPAIGN_POSTGRES_USER="campaign" \
  CAMPAIGN_POSTGRES_DB="campaign_db" \
  CAMPAIGN_DATABASE_URL="postgresql+psycopg://campaign:campaign@postgres-campaign:5432/campaign_db" \
  CAMPAIGN_POSTGRES_PASSWORD="campaign" \
  ANALYTICS_POSTGRES_USER="analytics" \
  ANALYTICS_POSTGRES_DB="analytics_db" \
  ANALYTICS_DATABASE_URL="postgresql+psycopg://analytics:analytics@postgres-analytics:5432/analytics_db" \
  ANALYTICS_POSTGRES_PASSWORD="analytics" \
  JWT_SECRET_KEY="super-secret-key" \
  GMAIL_FROM="your@gmail.com" \
  GMAIL_USER="your@gmail.com" \
  GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"

echo "9. Enabling Kubernetes Auth Method..."
kubectl exec -n vault vault-0 -- vault auth enable kubernetes

echo "10. Configuring Kubernetes Auth Role..."
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/config \
    kubernetes_host="https://$KUBERNETES_SERVICE_HOST:443"

echo "11. Creating Read-Only Policy..."
kubectl exec -n vault -i vault-0 -- vault policy write my-app-policy - <<EOF
path "secret/data/my-app/env" {
  capabilities = ["read"]
}
EOF

echo "12. Binding Policy to Service Account..."
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/my-app-role \
    bound_service_account_names=my-app-sa \
    bound_service_account_namespaces=default \
    policies=my-app-policy \
    ttl=1h

echo "13. Setup complete. Starting port-forwarding (Press Ctrl+C to stop)..."
kubectl port-forward svc/vault-ui 8200:8200 -n vault