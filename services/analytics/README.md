# Analytics microservice (`services/analytics`)

Rastreamento de cliques em links de campanha e APIs de métricas consolidadas.

Base URL (via gateway): `http://localhost:5000`

## Responsabilidades

| RF | Funcionalidade |
|----|----------------|
| RF07 | Registrar cliques (timestamp, IP, geolocalização) |
| RF08 | Dashboard agregado de todas as campanhas |
| RF09 | Métricas detalhadas por campanha (visão por alvo) |
| RF10 | Exportação CSV do relatório da campanha |

## Autenticação

Rotas `/api/analytics/*` exigem JWT (`Authorization: Bearer <token>`).

Rota pública de tracking: `GET|POST /track/<token>` (sem autenticação).

## Modelo

| Entidade | Descrição |
|----------|-----------|
| `ClickEvent` | Evento de interação com IP, geolocalização e metadados da campanha/alvo |

A resolução do token é feita via API interna do serviço campaign (`/api/internal/tracking-links/<token>`).

## Endpoints

| Método | URL | Auth |
|--------|-----|------|
| `GET`/`POST` | `/track/<token>?event=click` | Não |
| `GET` | `/api/analytics/dashboard` | Sim |
| `GET` | `/api/analytics/campaigns/<id>` | Sim |
| `GET` | `/api/analytics/campaigns/<id>/export` | Sim |

`event` permitidos: `click` (padrão), `open`, `submit`.

## Exemplo — registrar clique

```http
GET http://localhost:5000/track/<token>?event=click
```

Resposta inclui IP, timestamp e geolocalização (quando disponível para IPs públicos).

## Exemplo — dashboard agregado

```http
GET /api/analytics/dashboard
Authorization: Bearer <token>
```

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `ANALYTICS_DATABASE_URL` | PostgreSQL dedicado (`analytics_db`) |
| `JWT_SECRET_KEY` | Mesmo segredo do auth |
| `ANALYTICS_SERVICE_PORT` | Porta interna (padrão `5003`) |
| `CAMPAIGN_SERVICE_URL` | URL interna do campaign (padrão `http://campaign:5002`) |
| `INTERNAL_API_KEY` | Segredo compartilhado com o campaign |

## Subir com Docker

Na raiz do projeto:

```powershell
docker compose up -d --build
```

Migrations do analytics são aplicadas no start do container.

## Desenvolvimento local (opcional)

```powershell
docker compose up -d postgres-analytics campaign
$env:FLASK_APP = "services.analytics.app"
$env:ANALYTICS_DATABASE_URL = "postgresql+psycopg://analytics:analytics@localhost:5434/analytics_db"
$env:CAMPAIGN_SERVICE_URL = "http://localhost:5002"
$env:INTERNAL_API_KEY = "change-me-internal-key"
flask db upgrade
python -m services.analytics.app
```

Base URL direta: `http://localhost:5003` (sem gateway).
