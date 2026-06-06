# API Gateway (nginx)

Ponto de entrada único da API em Docker. O gateway escuta na porta pública (`GATEWAY_PORT`, padrão **5000**) e encaminha `/api/auth/` para o microserviço `auth` na rede interna do Compose.

## Arquitetura

```
Cliente → localhost:5000 (gateway) → auth:5001 → postgres-auth
                                      campaign:5002 → postgres-campaign
```

| Componente | Ficheiro / serviço |
|------------|-------------------|
| Configuração | [`nginx.conf`](nginx.conf) |
| Container | `api_gateway` (`nginx:alpine`) |
| Upstream | serviço `auth` na porta 5001 (não exposto no host) |

## Subir o stack

Na raiz do projeto:

```powershell
Copy-Item .env.example .env   # se ainda não existir
docker compose up -d --build
```

Base URL da API: `http://localhost:5000`

Após alterar `nginx.conf`:

```powershell
docker compose exec gateway nginx -t
docker compose restart gateway
```

## O que o gateway faz

### Proxy

- Rotas: apenas `/api/auth/*`
- Preserva o path completo (ex.: `/api/auth/login` chega igual ao Flask)
- Headers: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`

### CORS

Origens permitidas (regex no `map`):

- `http://localhost` / `https://localhost` (qualquer porta)
- `http://127.0.0.1` / `https://127.0.0.1` (qualquer porta)

Métodos expostos: `POST`, `OPTIONS`. Headers permitidos: `Authorization`, `Content-Type`.

Para outros frontends em produção, edite o bloco `map $http_origin` em [`nginx.conf`](nginx.conf).

### Segurança

| Regra | Detalhe |
|-------|---------|
| Métodos HTTP | Só `POST` e `OPTIONS` em `/api/auth/`; resto → `405` |
| Tamanho do body | Máximo 64 KB |
| Rate limit | 10 pedidos/s por IP (burst 20) |
| Headers de resposta | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy` |
| Versão nginx | Ocultada (`server_tokens off`) |
| Raiz `/` | `404` |

Clientes sem header `Origin` (curl, Insomnia, Postman) não são afetados por CORS.

Documentação do serviço auth: [`../services/auth/README.md`](../services/auth/README.md).

---

## Testes de validação

Execute com o stack a correr (`docker compose ps` deve mostrar `api_gateway` e `auth_service` healthy/up).

Substitua a porta se definir `GATEWAY_PORT` diferente de `5000` no `.env`.

### 1. Configuração nginx válida

```powershell
docker compose exec gateway nginx -t
```

**Esperado:** `syntax is ok` e `test is successful`.

---

### 2. Proxy — registo via gateway

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5000/api/auth/register" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"gateway-readme@example.com","password":"Password1!","name":"Gateway Test"}'
```

**Esperado:** `status: success` e HTTP `201`.  
(Use outro email se já registou este.)

---

### 3. Login via gateway

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5000/api/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"gateway-readme@example.com","password":"Password1!"}'
```

**Esperado:** `status: success`, campo `token` presente, HTTP `200`.

---

### 4. Auth não exposto no host (porta 5001)

```powershell
try {
  Invoke-WebRequest -Uri "http://localhost:5001/api/auth/login" -Method POST -TimeoutSec 3 -UseBasicParsing
} catch {
  $_.Exception.Message
}
```

**Esperado:** timeout ou conexão recusada (auth só acessível dentro da rede Docker).

---

### 5. Rota desconhecida — 404 na raiz

```powershell
try {
  Invoke-WebRequest -Uri "http://localhost:5000/" -UseBasicParsing
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

**Esperado:** `404`.

---

### 6. Método não permitido — GET → 405

```powershell
try {
  Invoke-WebRequest -Uri "http://localhost:5000/api/auth/login" -Method GET -UseBasicParsing
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

**Esperado:** `405`.

---

### 7. CORS preflight — origem permitida

```powershell
$r = Invoke-WebRequest `
  -Uri "http://localhost:5000/api/auth/login" `
  -Method OPTIONS `
  -Headers @{ Origin = "http://localhost:3000" } `
  -UseBasicParsing

"Status: $($r.StatusCode)"
"Access-Control-Allow-Origin: $($r.Headers['Access-Control-Allow-Origin'])"
"Access-Control-Allow-Methods: $($r.Headers['Access-Control-Allow-Methods'])"
```

**Esperado:**

- Status `204`
- `Access-Control-Allow-Origin: http://localhost:3000`
- `Access-Control-Allow-Methods` contém `POST`

---

### 8. CORS preflight — origem não permitida

```powershell
$r = Invoke-WebRequest `
  -Uri "http://localhost:5000/api/auth/login" `
  -Method OPTIONS `
  -Headers @{ Origin = "http://evil.example.com" } `
  -UseBasicParsing

"Status: $($r.StatusCode)"
"Access-Control-Allow-Origin: '$($r.Headers['Access-Control-Allow-Origin'])'"
```

**Esperado:**

- Status `204` (resposta ao preflight)
- `Access-Control-Allow-Origin` vazio ou ausente — o browser bloqueia o pedido real

---

### 9. Headers de segurança

```powershell
$r = Invoke-WebRequest `
  -Uri "http://localhost:5000/api/auth/login" `
  -Method OPTIONS `
  -Headers @{ Origin = "http://localhost:3000" } `
  -UseBasicParsing

$r.Headers['X-Content-Type-Options']
$r.Headers['X-Frame-Options']
$r.Headers['Referrer-Policy']
$r.Headers['Content-Security-Policy']
```

**Esperado:** valores definidos, por exemplo `nosniff`, `DENY`, `strict-origin-when-cross-origin`, e CSP com `default-src 'none'`.

---

### 10. Body demasiado grande — 413

```powershell
$bigBody = '{"email":"big@example.com","password":"' + ('x' * 70000) + '"}'
try {
  Invoke-WebRequest `
    -Uri "http://localhost:5000/api/auth/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $bigBody `
    -UseBasicParsing
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

**Esperado:** `413` (Request Entity Too Large).

---

### 11. Checklist rápido

| # | Teste | Resultado esperado |
|---|--------|-------------------|
| 1 | `nginx -t` no container | OK |
| 2 | POST register `:5000/api/auth/register` | 201 |
| 3 | POST login | 200 + token |
| 4 | POST `:5001` no host | Falha de ligação |
| 5 | GET `/` | 404 |
| 6 | GET `/api/auth/login` | 405 |
| 7 | OPTIONS + Origin localhost | 204 + CORS |
| 8 | OPTIONS + Origin externo | Sem ACAO |
| 9 | Headers de segurança | Presentes |
| 10 | Body > 64 KB | 413 |

---

## Personalização

| Objetivo | Onde alterar |
|----------|----------------|
| Porta pública | `GATEWAY_PORT` no `.env` |
| Novas origens CORS | `map $http_origin` em [`nginx.conf`](nginx.conf) |
| Novo microserviço | Novo `upstream` + `location` em [`nginx.conf`](nginx.conf) e serviço no [`compose.yaml`](../compose.yaml) |
| Rate limit / tamanho body | `limit_req_zone`, `client_max_body_size` em [`nginx.conf`](nginx.conf) |
