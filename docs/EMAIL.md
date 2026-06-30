# Email microservice (`services/email`)

Stateless email delivery microservice via SMTP (Gmail). Accessed through the **API Gateway** on the public port; the container is not exposed on the host.

Base URL (via gateway): `http://localhost:5000`

## Authentication

`/api/internal/*` routes require the `X-Internal-Key` header with the value of `INTERNAL_API_KEY` (same secret used between campaign and analytics).

**Service-to-service** calls on the Docker network still use `http://email:5010` directly (`EMAIL_SERVICE_URL`).

## Endpoints

| Method | URL (via gateway) | Auth |
|--------|-------------------|------|
| `POST` | `/api/internal/send` | `X-Internal-Key` |

The `/health` endpoint exists only inside the container (internal healthcheck); it is not exposed by the gateway.

## Example — send email

```http
POST http://localhost:5000/api/internal/send
X-Internal-Key: <INTERNAL_API_KEY>
Content-Type: application/json

{
  "to": "john@company.com",
  "subject": "Holiday Campaign",
  "html_body": "<p>Click the link to confirm your details.</p>",
  "text_body": "Click the link to confirm your details."
}
```

Response (`200`):

```json
{
  "status": "success",
  "data": {
    "to": "john@company.com",
    "subject": "Holiday Campaign"
  }
}
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `EMAIL_SERVICE_PORT` | Internal container port (default `5010`) |
| `INTERNAL_API_KEY` | Secret for internal API |
| `GMAIL_FROM` | Displayed sender address |
| `GMAIL_USER` | Gmail account for SMTP authentication |
| `GMAIL_APP_PASSWORD` | Google app password |
| `SMTP_HOST` | SMTP server (default `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default `587`) |
| `EMAIL_SERVICE_URL` | Internal URL for other services (`http://email:5010`) |

For Gmail, create an app password at: https://myaccount.google.com/apppasswords

## Run with Docker

From the project root:

```bash
cp .env.example .env   # if .env does not exist yet
# Edit .env with real Gmail credentials and INTERNAL_API_KEY
docker compose up -d --build
```

The email service starts with the full stack (gateway + dependencies). To start only email and gateway:

```bash
docker compose up -d --build gateway email
```

After changing `gateway/nginx.conf`:

```bash
docker compose exec gateway nginx -t
docker compose restart gateway
```

Gateway and architecture: [`gateway/README.md`](../gateway/README.md).

---

## Insomnia

Create a workspace or **Email** folder with base URL `http://localhost:5000`.

Define an **Environment** with:

| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:5000` |
| `internal_key` | value of `INTERNAL_API_KEY` in `.env` (e.g. `change-me-internal-key`) |

For all requests below, add the header:

| Header | Value |
|--------|-------|
| `X-Internal-Key` | `{{ internal_key }}` |
| `Content-Type` | `application/json` |

Replace `recipient@example.com` with a real email address to receive the test message.

---

### 1. Send email (success)

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `{{ base_url }}/api/internal/send` |

**Body (JSON):**

```json
{
  "to": "recipient@example.com",
  "subject": "DevSecOps Test",
  "html_body": "<p>Test email via gateway.</p>",
  "text_body": "Test email via gateway."
}
```

**Expected:** `200`

```json
{
  "status": "success",
  "data": {
    "to": "recipient@example.com",
    "subject": "DevSecOps Test"
  }
}
```

Check the recipient's inbox (and spam folder).

---

### 2. Invalid internal key — 401

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `{{ base_url }}/api/internal/send` |
| Header | `X-Internal-Key: wrong-key` |

**Body (JSON):**

```json
{
  "to": "recipient@example.com",
  "subject": "Test",
  "html_body": "<p>Test</p>"
}
```

**Expected:** `401`

```json
{
  "status": "error",
  "message": "Unauthorized."
}
```

---

### 3. Missing internal key — 401

Same as test 2, but **without** the `X-Internal-Key` header.

**Expected:** `401`

---

### 4. Invalid recipient — 400

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `{{ base_url }}/api/internal/send` |

**Body (JSON):**

```json
{
  "to": "not-an-email",
  "subject": "Test",
  "html_body": "<p>Test</p>"
}
```

**Expected:** `400`

```json
{
  "status": "error",
  "message": "Invalid email address."
}
```

---

### 5. Missing subject — 400

**Body (JSON):**

```json
{
  "to": "recipient@example.com",
  "subject": "",
  "html_body": "<p>Test</p>"
}
```

**Expected:** `400`

```json
{
  "status": "error",
  "message": "Subject is required."
}
```

---

### 6. Missing HTML body — 400

**Body (JSON):**

```json
{
  "to": "recipient@example.com",
  "subject": "Test",
  "html_body": ""
}
```

**Expected:** `400`

```json
{
  "status": "error",
  "message": "html_body is required."
}
```

---

### 7. Method not allowed — GET → 405

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL | `{{ base_url }}/api/internal/send` |

**Expected:** `405` (blocked by gateway)

---

### 8. Direct port not exposed — connection refused

Try to access the email service directly on the host (without gateway):

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5010/api/internal/send` |

**Expected:** timeout or connection refused — email is only reachable via gateway (`:5000`) or on the Docker network (`email:5010`).

---

### 9. Quick checklist

| # | Test | Expected result |
|---|------|-----------------|
| 1 | POST send with valid key | 200 + email received |
| 2 | Invalid key | 401 |
| 3 | No `X-Internal-Key` | 401 |
| 4 | Invalid email | 400 |
| 5 | Empty subject | 400 |
| 6 | Empty `html_body` | 400 |
| 7 | GET `/api/internal/send` | 405 |
| 8 | POST `:5010` on host | Connection failure |

---

## Local development (optional)

```bash
export FLASK_APP="services.email.app"
export INTERNAL_API_KEY="change-me-internal-key"
export GMAIL_FROM="your@gmail.com"
export GMAIL_USER="your@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
python -m services.email.app
```

Direct base URL: `http://localhost:5010` (no gateway).
