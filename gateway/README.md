# API Gateway (nginx)

Single entry point for the API in Docker. The gateway listens on the public port (`GATEWAY_PORT`, default **5000**) and forwards `/api/auth/` to the `auth` microservice on the internal Compose network.

## Architecture

```
Client → localhost:5000 (gateway) → auth:5001 → postgres-auth
                                      campaign:5002 → postgres-campaign
```

| Component | File / service |
|-----------|----------------|
| Configuration | [`nginx.conf`](nginx.conf) |
| Container | `api_gateway` (`nginx:alpine`) |
| Upstream | `auth` service on port 5001 (not exposed on the host) |

## Start the stack

From the project root:

```bash
cp .env.example .env   # if .env does not exist yet
docker compose up -d --build
```

API base URL: `http://localhost:5000`

After changing `nginx.conf`:

```bash
docker compose exec gateway nginx -t
docker compose restart gateway
```

## What the gateway does

### Proxy

- Routes: `/api/auth/*` only (see full routing in `nginx.conf` for all services)
- Preserves the full path (e.g. `/api/auth/login` reaches Flask unchanged)
- Headers: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`

### CORS

Allowed origins (regex in `map`):

- `http://localhost` / `https://localhost` (any port)
- `http://127.0.0.1` / `https://127.0.0.1` (any port)

Exposed methods: `POST`, `OPTIONS`. Allowed headers: `Authorization`, `Content-Type`.

For other frontends in production, edit the `map $http_origin` block in [`nginx.conf`](nginx.conf).

### Security

| Rule | Detail |
|------|--------|
| HTTP methods | Only `POST` and `OPTIONS` on `/api/auth/`; others → `405` |
| Body size | Maximum 64 KB |
| Rate limit | 10 requests/s per IP (burst 20) |
| Response headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy` |
| nginx version | Hidden (`server_tokens off`) |
| Root `/` | `404` |

Clients without an `Origin` header (curl, Insomnia, Postman) are not affected by CORS.

Auth service documentation: [`../docs/AUTH.md`](../docs/AUTH.md).

---

## Validation tests

Run with the stack up (`docker compose ps` should show `api_gateway` and `auth_service` healthy/up).

Replace the port if you set `GATEWAY_PORT` to something other than `5000` in `.env`.

### 1. Valid nginx configuration

```bash
docker compose exec gateway nginx -t
```

**Expected:** `syntax is ok` and `test is successful`.

---

### 2. Proxy — register via gateway

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "http://localhost:5000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"gateway-readme@example.com","password":"Password1!","name":"Gateway Test"}'
```

**Expected:** `status: success` and HTTP `201`.  
(Use a different email if you already registered this one.)

---

### 3. Login via gateway

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"gateway-readme@example.com","password":"Password1!"}'
```

**Expected:** `status: success`, `token` field present, HTTP `200`.

---

### 4. Auth not exposed on host (port 5001)

```bash
curl -s -o /dev/null -w "%{http_code}\n" --connect-timeout 3 \
  -X POST "http://localhost:5001/api/auth/login" || echo "connection refused"
```

**Expected:** timeout or connection refused (auth is only reachable inside the Docker network).

---

### 5. Unknown route — 404 on root

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/"
```

**Expected:** `404`.

---

### 6. Method not allowed — GET → 405

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/api/auth/login"
```

**Expected:** `405`.

---

### 7. CORS preflight — allowed origin

```bash
curl -s -D - -o /dev/null -X OPTIONS "http://localhost:5000/api/auth/login" \
  -H "Origin: http://localhost:3000" \
  | grep -iE 'HTTP/|access-control'
```

**Expected:**

- Status `204`
- `Access-Control-Allow-Origin: http://localhost:3000`
- `Access-Control-Allow-Methods` includes `POST`

---

### 8. CORS preflight — disallowed origin

```bash
curl -s -D - -o /dev/null -X OPTIONS "http://localhost:5000/api/auth/login" \
  -H "Origin: http://evil.example.com" \
  | grep -iE 'HTTP/|access-control'
```

**Expected:**

- Status `204` (preflight response)
- `Access-Control-Allow-Origin` empty or absent — the browser blocks the actual request

---

### 9. Security headers

```bash
curl -s -D - -o /dev/null -X OPTIONS "http://localhost:5000/api/auth/login" \
  -H "Origin: http://localhost:3000" \
  | grep -iE 'x-content-type-options|x-frame-options|referrer-policy|content-security-policy'
```

**Expected:** values set, e.g. `nosniff`, `DENY`, `strict-origin-when-cross-origin`, and CSP with `default-src 'none'`.

---

### 10. Body too large — 413

```bash
big_body='{"email":"big@example.com","password":"'$(python3 -c "print('x'*70000)")'"}'
curl -s -o /dev/null -w "%{http_code}\n" -X POST "http://localhost:5000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "$big_body"
```

**Expected:** `413` (Request Entity Too Large).

---

### 11. Quick checklist

| # | Test | Expected result |
|---|------|-----------------|
| 1 | `nginx -t` in container | OK |
| 2 | POST register `:5000/api/auth/register` | 201 |
| 3 | POST login | 200 + token |
| 4 | POST `:5001` on host | Connection failure |
| 5 | GET `/` | 404 |
| 6 | GET `/api/auth/login` | 405 |
| 7 | OPTIONS + Origin localhost | 204 + CORS |
| 8 | OPTIONS + external Origin | No ACAO |
| 9 | Security headers | Present |
| 10 | Body > 64 KB | 413 |

---

## Customization

| Goal | Where to change |
|------|-----------------|
| Public port | `GATEWAY_PORT` in `.env` |
| New CORS origins | `map $http_origin` in [`nginx.conf`](nginx.conf) |
| New microservice | New `upstream` + `location` in [`nginx.conf`](nginx.conf) and service in [`compose.yaml`](../compose.yaml) |
| Rate limit / body size | `limit_req_zone`, `client_max_body_size` in [`nginx.conf`](nginx.conf) |
