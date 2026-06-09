# Email microservice (`services/email`)

Microserviço stateless de envio de e-mail via SMTP (Gmail). Acesso apenas interno na rede Docker — outros serviços chamam com `X-Internal-Key`.

## Endpoints

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/health` | Não |
| `POST` | `/api/internal/send` | `X-Internal-Key` |

## Exemplo — enviar e-mail

```json
POST http://email:5010/api/internal/send
X-Internal-Key: <INTERNAL_API_KEY>

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
| `EMAIL_SERVICE_PORT` | Porta interna (padrão `5010`) |
| `INTERNAL_API_KEY` | Segredo para API interna |
| `GMAIL_FROM` | Endereço remetente exibido |
| `GMAIL_USER` | Conta Gmail para autenticação SMTP |
| `GMAIL_APP_PASSWORD` | Senha de app do Google |
| `SMTP_HOST` | Servidor SMTP (padrão `smtp.gmail.com`) |
| `SMTP_PORT` | Porta SMTP (padrão `587`) |

Para Gmail, crie uma senha de app em: https://myaccount.google.com/apppasswords

## Subir com Docker

Na raiz do projeto:

```powershell
Copy-Item .env.example .env
# Edite .env com credenciais Gmail reais
docker compose up -d --build email
```

## Teste local (PowerShell)

Com o stack rodando e credenciais configuradas:

```powershell
$headers = @{
  "X-Internal-Key" = "change-me-internal-key"
  "Content-Type"   = "application/json"
}
$body = @{
  to        = "destino@exemplo.com"
  subject   = "Teste DevSecOps"
  html_body = "<p>E-mail de teste.</p>"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5010/api/internal/send" `
  -Method POST -Headers $headers -Body $body
```
