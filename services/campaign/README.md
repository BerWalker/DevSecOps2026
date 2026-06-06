# Campaign microservice (`services/campaign`)

CRUD de campanhas de phishing simulado: nome, grupos de alvos, conteúdo do e-mail e link de rastreamento único por alvo.

Base URL (via gateway): `http://localhost:5000`

## Autenticação

Rotas `/api/campaigns*` exigem JWT do serviço auth (`Authorization: Bearer <token>`). A validação é stateless (assinatura e expiração); revogação de logout é gerida apenas pelo serviço auth.

Rota pública de tracking: `GET|POST /track/<token>` (sem autenticação).

## Modelo

| Entidade | Descrição |
|----------|-----------|
| `Campaign` | Nome + conteúdo do e-mail |
| `TargetGroup` | Grupo de alvos dentro da campanha |
| `Target` | Alvo (e-mail + nome opcional) |
| `TrackingLink` | Token único por alvo |
| `Interaction` | Clique/abertura/etc. registrado no link |

Ao criar ou atualizar `target_groups`, um link de rastreamento é gerado automaticamente para cada alvo.

## Endpoints

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/campaigns` | Sim |
| `POST` | `/api/campaigns` | Sim |
| `GET` | `/api/campaigns/<id>` | Sim |
| `PUT` | `/api/campaigns/<id>` | Sim |
| `DELETE` | `/api/campaigns/<id>` | Sim |
| `GET`/`POST` | `/track/<token>?event=click` | Não |

`event` permitidos: `click` (padrão), `open`, `submit`.

## Exemplo — criar campanha

```json
POST /api/campaigns
Authorization: Bearer <token>

{
  "name": "Campanha Natal",
  "email_content": "<p>Clique no link para confirmar seus dados.</p>",
  "target_groups": [
    {
      "name": "Financeiro",
      "targets": [
        { "email": "joao@empresa.com", "name": "João Silva" },
        { "email": "maria@empresa.com", "name": "Maria Souza" }
      ]
    }
  ]
}
```

Resposta (`201`) inclui `target_groups[].targets[].tracking.url` — link único por alvo.

## Exemplo — registrar clique

```http
GET http://localhost:5000/track/<token>?event=click
```

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `CAMPAIGN_DATABASE_URL` | PostgreSQL dedicado (`campaign_db`) |
| `JWT_SECRET_KEY` | Mesmo segredo do auth |
| `CAMPAIGN_SERVICE_PORT` | Porta interna (padrão `5002`) |
| `TRACKING_BASE_URL` | Base pública dos links (padrão `http://localhost:5000`) |

## Subir com Docker

Na raiz do projeto:

```powershell
docker compose up -d --build
```

Migrations do campaign são aplicadas no start do container.

## Desenvolvimento local (opcional)

```powershell
docker compose up -d postgres-campaign
$env:FLASK_APP = "services.campaign.app"
$env:CAMPAIGN_DATABASE_URL = "postgresql+psycopg://campaign:campaign@localhost:5433/campaign_db"
flask db upgrade
python -m services.campaign.app
```

Base URL direta: `http://localhost:5002` (sem gateway).
