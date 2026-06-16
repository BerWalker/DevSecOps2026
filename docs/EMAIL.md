# Email microservice (`services/email`)

Microserviço stateless de envio de e-mail via SMTP (Gmail). Acesso via **API Gateway** na porta pública; o container não é exposto no host.

Base URL (via gateway): `http://localhost:5000`

## Autenticação

Rotas `/api/internal/*` exigem o header `X-Internal-Key` com o valor de `INTERNAL_API_KEY` (mesmo segredo usado entre campaign e analytics).

Chamadas **service-to-service** na rede Docker continuam a usar `http://email:5010` diretamente (`EMAIL_SERVICE_URL`).

## Endpoints

| Método | URL (via gateway) | Auth |
|--------|-------------------|------|
| `POST` | `/api/internal/send` | `X-Internal-Key` |

O endpoint `/health` existe apenas dentro do container (healthcheck interno); não é exposto pelo gateway.

## Exemplo — enviar e-mail

```http
POST http://localhost:5000/api/internal/send
X-Internal-Key: <INTERNAL_API_KEY>
Content-Type: application/json

{
  "to": "joao@empresa.com",
  "subject": "Campanha Natal",
  "html_body": "<p>Clique no link para confirmar seus dados.</p>",
  "text_body": "Clique no link para confirmar seus dados."
}
```

Resposta (`200`):

```json
{
  "status": "success",
  "data": {
    "to": "joao@empresa.com",
    "subject": "Campanha Natal"
  }
}
```

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `EMAIL_SERVICE_PORT` | Porta interna no container (padrão `5010`) |
| `INTERNAL_API_KEY` | Segredo para API interna |
| `GMAIL_FROM` | Endereço remetente exibido |
| `GMAIL_USER` | Conta Gmail para autenticação SMTP |
| `GMAIL_APP_PASSWORD` | Senha de app do Google |
| `SMTP_HOST` | Servidor SMTP (padrão `smtp.gmail.com`) |
| `SMTP_PORT` | Porta SMTP (padrão `587`) |
| `EMAIL_SERVICE_URL` | URL interna para outros serviços (`http://email:5010`) |

Para Gmail, crie uma senha de app em: https://myaccount.google.com/apppasswords

## Subir com Docker

Na raiz do projeto:

```powershell
Copy-Item .env.example .env   # se ainda não existir
# Edite .env com credenciais Gmail reais e INTERNAL_API_KEY
docker compose up -d --build
```

O serviço email sobe com o stack completo (gateway + dependências). Para subir apenas email e gateway:

```powershell
docker compose up -d --build gateway email
```

Após alterar `gateway/nginx.conf`:

```powershell
docker compose exec gateway nginx -t
docker compose restart gateway
```

Gateway e arquitetura: [`../../gateway/README.md`](../../gateway/README.md).

---

## Insomnia

Crie um workspace ou pasta **Email** com base URL `http://localhost:5000`.

Defina uma **Environment** com:

| Variável | Valor |
|----------|-------|
| `base_url` | `http://localhost:5000` |
| `internal_key` | valor de `INTERNAL_API_KEY` no `.env` (ex.: `change-me-internal-key`) |

Em todos os pedidos abaixo, adicione o header:

| Header | Valor |
|--------|-------|
| `X-Internal-Key` | `{{ internal_key }}` |
| `Content-Type` | `application/json` |

Substitua `destino@exemplo.com` por um e-mail real para receber a mensagem de teste.

---

### 1. Enviar e-mail (sucesso)

| Campo | Valor |
|-------|-------|
| Method | `POST` |
| URL | `{{ base_url }}/api/internal/send` |

**Body (JSON):**

```json
{
  "to": "destino@exemplo.com",
  "subject": "Teste DevSecOps",
  "html_body": "<p>E-mail de teste via gateway.</p>",
  "text_body": "E-mail de teste via gateway."
}
```

**Expected:** `200`

```json
{
  "status": "success",
  "data": {
    "to": "destino@exemplo.com",
    "subject": "Teste DevSecOps"
  }
}
```

Verifique a caixa de entrada do destinatário (e spam).

---

### 2. Chave interna inválida — 401

| Campo | Valor |
|-------|-------|
| Method | `POST` |
| URL | `{{ base_url }}/api/internal/send` |
| Header | `X-Internal-Key: chave-errada` |

**Body (JSON):**

```json
{
  "to": "destino@exemplo.com",
  "subject": "Teste",
  "html_body": "<p>Teste</p>"
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

### 3. Chave interna ausente — 401

Igual ao teste 2, mas **sem** o header `X-Internal-Key`.

**Expected:** `401`

---

### 4. Destinatário inválido — 400

| Campo | Valor |
|-------|-------|
| Method | `POST` |
| URL | `{{ base_url }}/api/internal/send` |

**Body (JSON):**

```json
{
  "to": "nao-e-email",
  "subject": "Teste",
  "html_body": "<p>Teste</p>"
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

### 5. Assunto ausente — 400

**Body (JSON):**

```json
{
  "to": "destino@exemplo.com",
  "subject": "",
  "html_body": "<p>Teste</p>"
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

### 6. Corpo HTML ausente — 400

**Body (JSON):**

```json
{
  "to": "destino@exemplo.com",
  "subject": "Teste",
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

### 7. Método não permitido — GET → 405

| Campo | Valor |
|-------|-------|
| Method | `GET` |
| URL | `{{ base_url }}/api/internal/send` |

**Expected:** `405` (bloqueado pelo gateway)

---

### 8. Porta direta não exposta — conexão recusada

Tente aceder ao serviço email diretamente no host (sem gateway):

| Campo | Valor |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:5010/api/internal/send` |

**Expected:** timeout ou conexão recusada — o email só é acessível via gateway (`:5000`) ou na rede Docker (`email:5010`).

---

### 9. Checklist rápido

| # | Teste | Resultado esperado |
|---|--------|-------------------|
| 1 | POST send com chave válida | 200 + e-mail recebido |
| 2 | Chave inválida | 401 |
| 3 | Sem `X-Internal-Key` | 401 |
| 4 | E-mail inválido | 400 |
| 5 | Assunto vazio | 400 |
| 6 | `html_body` vazio | 400 |
| 7 | GET `/api/internal/send` | 405 |
| 8 | POST `:5010` no host | Falha de ligação |

---

## Desenvolvimento local (opcional)

```powershell
$env:FLASK_APP = "services.email.app"
$env:INTERNAL_API_KEY = "change-me-internal-key"
$env:GMAIL_FROM = "your@gmail.com"
$env:GMAIL_USER = "your@gmail.com"
$env:GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
python -m services.email.app
```

Base URL direta: `http://localhost:5010` (sem gateway).
