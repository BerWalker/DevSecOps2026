# Campaign microservice (`services/campaign`)

CRUD for simulated phishing campaigns: name, target groups, email content, and a unique tracking link per target.

Base URL (via gateway): `http://localhost:5000`

## Authentication

`/api/campaigns*` routes require a JWT from the auth service (`Authorization: Bearer <token>`). Validation is stateless (signature and expiry); logout revocation is handled only by the auth service.

Click tracking is handled by the **analytics** service (`/track/<token>`). This service exposes only the internal token resolution API.

## Model

| Entity | Description |
|--------|-------------|
| `Campaign` | Name + email content |
| `TargetGroup` | Target group within a campaign |
| `Target` | Target (email + optional name) |
| `TrackingLink` | Unique token per target |
| `Interaction` | Legacy (events are recorded in the analytics service) |

When creating or updating `target_groups`, a tracking link is generated automatically for each target.

## Endpoints

| Method | URL | Auth |
|--------|-----|------|
| `GET` | `/api/campaigns` | Yes |
| `POST` | `/api/campaigns` | Yes |
| `GET` | `/api/campaigns/<id>` | Yes |
| `PUT` | `/api/campaigns/<id>` | Yes |
| `DELETE` | `/api/campaigns/<id>` | Yes |
| `GET` | `/api/internal/tracking-links/<token>` | `X-Internal-Key` (analytics service) |

## Example — create campaign

```json
POST /api/campaigns
Authorization: Bearer <token>

{
  "name": "Holiday Campaign",
  "email_content": "<p>Click the link to confirm your details.</p>",
  "target_groups": [
    {
      "name": "Finance",
      "targets": [
        { "email": "john@company.com", "name": "John Smith" },
        { "email": "mary@company.com", "name": "Mary Jones" }
      ]
    }
  ]
}
```

Response (`201`) includes `target_groups[].targets[].tracking.url` — one unique link per target.

## Environment variables

| Variable | Description |
|----------|-------------|
| `CAMPAIGN_DATABASE_URL` | Dedicated PostgreSQL (`campaign_db`) |
| `JWT_SECRET_KEY` | Same secret as auth |
| `CAMPAIGN_SERVICE_PORT` | Internal port (default `5002`) |
| `TRACKING_BASE_URL` | Public base URL for links (default `http://localhost:5000`) |
| `INTERNAL_API_KEY` | Secret for internal API (analytics) |

## Run with Docker

From the project root:

```bash
docker compose up -d --build
```

Campaign migrations are applied on container start.

## Local development (optional)

```bash
docker compose up -d postgres-campaign
export FLASK_APP="services.campaign.app"
export CAMPAIGN_DATABASE_URL="postgresql+psycopg://campaign:campaign@localhost:5433/campaign_db"
flask db upgrade
python -m services.campaign.app
```

Direct base URL: `http://localhost:5002` (no gateway).
