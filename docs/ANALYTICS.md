# Analytics microservice (`services/analytics`)

Click tracking on campaign links and consolidated metrics APIs.

Base URL (via gateway): `http://localhost:5000`

## Responsibilities

| Req | Feature |
|-----|---------|
| RF07 | Record clicks (timestamp, IP, geolocation) |
| RF08 | Aggregated dashboard across all campaigns |
| RF09 | Detailed per-campaign metrics (per-target view) |
| RF10 | CSV export of campaign report |

## Authentication

`/api/analytics/*` routes require JWT (`Authorization: Bearer <token>`).

Public tracking route: `GET|POST /track/<token>` (no authentication).

## Model

| Entity | Description |
|--------|-------------|
| `ClickEvent` | Interaction event with IP, geolocation, and campaign/target metadata |

Token resolution is done via the campaign service internal API (`/api/internal/tracking-links/<token>`).

## Endpoints

| Method | URL | Auth |
|--------|-----|------|
| `GET`/`POST` | `/track/<token>?event=click` | No |
| `GET` | `/api/analytics/dashboard` | Yes |
| `GET` | `/api/analytics/campaigns/<id>` | Yes |
| `GET` | `/api/analytics/campaigns/<id>/export` | Yes |

Allowed `event` values: `click` (default), `open`, `submit`.

## Example — record click

```http
GET http://localhost:5000/track/<token>?event=click
```

Response includes IP, timestamp, and geolocation (when available for public IPs).

## Example — aggregated dashboard

```http
GET /api/analytics/dashboard
Authorization: Bearer <token>
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `ANALYTICS_DATABASE_URL` | Dedicated PostgreSQL (`analytics_db`) |
| `JWT_SECRET_KEY` | Same secret as auth |
| `ANALYTICS_SERVICE_PORT` | Internal port (default `5003`) |
| `CAMPAIGN_SERVICE_URL` | Internal campaign URL (default `http://campaign:5002`) |
| `INTERNAL_API_KEY` | Shared secret with campaign |

## Run with Docker

From the project root:

```bash
docker compose up -d --build
```

Analytics migrations are applied on container start.

## Local development (optional)

```bash
docker compose up -d postgres-analytics campaign
export FLASK_APP="services.analytics.app"
export ANALYTICS_DATABASE_URL="postgresql+psycopg://analytics:analytics@localhost:5434/analytics_db"
export CAMPAIGN_SERVICE_URL="http://localhost:5002"
export INTERNAL_API_KEY="change-me-internal-key"
flask db upgrade
python -m services.analytics.app
```

Direct base URL: `http://localhost:5003` (no gateway).
