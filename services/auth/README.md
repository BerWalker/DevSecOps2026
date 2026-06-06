# Authentication microservice (`services/auth`)

Base URL: `http://localhost:5000` (nginx API Gateway → auth service)

## Setup

From the project root (Docker — recommended):

```powershell
Copy-Item .env.example .env   # if .env does not exist yet
docker compose up -d --build
```

API: `http://localhost:5000` via the gateway (`gateway/nginx.conf` proxies `/api/auth/` to the auth container). Migrations run automatically on auth container start.

Auth uses a dedicated PostgreSQL instance (`postgres-auth`, database `auth_db`). If you previously ran the monolithic `migrations/` setup, drop campaign tables from `auth_db` or reset the volume: `docker compose down -v` then `docker compose up -d --build`.

The auth service is not published on the host; use the gateway port (`GATEWAY_PORT`, default `5000`). To hit auth directly for debugging, use `docker compose exec auth` or temporarily add a `ports` mapping on the `auth` service.

### Gateway (security and CORS)

See [`gateway/README.md`](../../gateway/README.md) for architecture, security rules, and validation tests.

Copy `.env.example` to `.env` and change `JWT_SECRET_KEY` (and other secrets) before production.

### Local development (optional, without Docker for the app)

```powershell
docker compose up -d postgres-auth
.\.venv\Scripts\pip install -r requirements.txt
$env:FLASK_APP = "services.auth.app"
$env:AUTH_DATABASE_URL = "postgresql+psycopg://auth:auth@localhost:5432/auth_db"
.\.venv\Scripts\flask db upgrade
.\.venv\Scripts\python -m services.auth.app
```

For local runs, set `AUTH_DATABASE_URL` to a full connection string (python-dotenv does not expand `${AUTH_POSTGRES_*}` in `.env`). Use base URL `http://localhost:5001` (no gateway).

## Email rules (register and login)

- Valid format (RFC-style), normalized to lowercase
- Maximum 255 characters (database limit)
- Must be a JSON string (not a number or object)
- Rejects control characters and line breaks (injection hardening)
- Login returns `Invalid credentials.` for malformed emails (no account enumeration)

## Password rules (register)

- At least 8 characters
- At least one uppercase letter (`A-Z`)
- At least one number (`0-9`)
- At least one symbol (non-alphanumeric, e.g. `!@#$%`)

User `id` is a UUID (string in JSON and in JWT claim `sub`).

---

## Insomnia

Create a workspace or folder **Auth** with base URL `http://localhost:5000`.

For logout, set header `Authorization` to `Bearer <token>` using the token returned by login.

### 1. Register (success)

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5000/api/auth/register` |
| Header | `Content-Type: application/json` |

**Body (JSON):**

```json
{
  "email": "test@example.com",
  "password": "Password1!",
  "name": "Test User"
}
```

**Expected:** `201`

```json
{
  "status": "success",
  "message": "User registered successfully.",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "name": "Test User"
  }
}
```

---

### 2. Register (duplicate email)

Same as above (same email). **Expected:** `409`

```json
{
  "status": "error",
  "message": "Email is already registered."
}
```

---

### 3. Register (weak password)

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5000/api/auth/register` |

**Body (JSON):**

```json
{
  "email": "weak@example.com",
  "password": "short"
}
```

**Expected:** `400` — e.g. `"Password must be at least 8 characters long."`

---

### 4. Login (success)

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5000/api/auth/login` |
| Header | `Content-Type: application/json` |

**Body (JSON):**

```json
{
  "email": "test@example.com",
  "password": "Password1!"
}
```

**Expected:** `200`

```json
{
  "status": "success",
  "message": "Login successful.",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

Copy `token` for logout requests.

---

### 5. Login (invalid credentials)

**Body (JSON):**

```json
{
  "email": "test@example.com",
  "password": "WrongPass1!"
}
```

**Expected:** `401`

```json
{
  "status": "error",
  "message": "Invalid credentials."
}
```

---

### 6. Logout (success)

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5000/api/auth/logout` |
| Header | `Authorization: Bearer <paste_token_here>` |

No body.

**Expected:** `200`

```json
{
  "status": "success",
  "message": "Logout successful."
}
```

---

### 7. Logout again (idempotent)

Same request as #6 with the same token. **Expected:** `200` (token already revoked).

---

### 8. Logout (no token)

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5000/api/auth/logout` |

No `Authorization` header. **Expected:** `401`

---

### 9. Logout (revoked token)

Use a token that was already logged out. **Expected:** `401`

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token."
}
```

---

### Suggested test order (Insomnia)

1. Register → 201  
2. Login → 200 (save token)  
3. Logout → 200  
4. Logout again → 200  
5. Logout with same token → 401  
6. Register duplicate → 409  
7. Login wrong password → 401  

---

## PowerShell (one-liners)

Run with the service up. Replace the email if you already registered it.

**Register**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","password":"Password1!","name":"Test User"}'
```

**Login (saves `$token`)**

```powershell
$login = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","password":"Password1!"}'; $token = $login.token; $login
```

**Logout**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/auth/logout" -Method POST -Headers @{ Authorization = "Bearer $token" }
```

**Full happy path (single line)**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","password":"Password1!","name":"Test"}'; $login = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","password":"Password1!"}'; $token = $login.token; Invoke-RestMethod -Uri "http://localhost:5000/api/auth/logout" -Method POST -Headers @{ Authorization = "Bearer $token" }
```

**Duplicate email (409)**

```powershell
try { Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","password":"Password1!"}' } catch { $_.Exception.Response.StatusCode.value__; ($_ | Select-Object -ExpandProperty ErrorDetails).Message }
```

**Weak password (400)**

```powershell
try { Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" -Method POST -ContentType "application/json" -Body '{"email":"weak@example.com","password":"short"}' } catch { $_.Exception.Response.StatusCode.value__; ($_ | Select-Object -ExpandProperty ErrorDetails).Message }
```

**Wrong password (401)**

```powershell
try { Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"test@example.com","password":"WrongPass1!"}' } catch { $_.Exception.Response.StatusCode.value__; ($_ | Select-Object -ExpandProperty ErrorDetails).Message }
```

**Logout without token (401)**

```powershell
try { Invoke-RestMethod -Uri "http://localhost:5000/api/auth/logout" -Method POST } catch { $_.Exception.Response.StatusCode.value__; ($_ | Select-Object -ExpandProperty ErrorDetails).Message }
```

**Logout with revoked token (401)**

```powershell
try { Invoke-RestMethod -Uri "http://localhost:5000/api/auth/logout" -Method POST -Headers @{ Authorization = "Bearer $token" } } catch { $_.Exception.Response.StatusCode.value__; ($_ | Select-Object -ExpandProperty ErrorDetails).Message }
```
