# API de Gerenciamento de Veículos

API REST para gerenciamento de veículos com controle de acesso por JWT (USER / ADMIN), construída com Python + FastAPI + PostgreSQL + Redis.

---

## Início rápido (Docker)

### 1. Copie e preencha as variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env`: defina `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` e `SECRET_KEY` (gere com `openssl rand -hex 32`). Os demais valores podem ser mantidos do exemplo.

### 2. Build e suba todos os serviços

```bash
docker compose up --build -d
```

Isso sobe o PostgreSQL 17, Redis 7 e a API. As migrations rodam automaticamente antes do servidor iniciar. A API ficará disponível em **`http://localhost:8000`**.

### 3. Crie os usuários iniciais

```bash
docker compose exec api sh -c "SEED_ADMIN_PASSWORD=admin123 SEED_USER_PASSWORD=user123 python scripts/seed.py"
```

Isso cria duas contas:
- `admin` / `admin123` — role ADMIN (acesso completo)
- `user` / `user123` — role USER (somente leitura)

### 4. Abra o Swagger UI

```
http://localhost:8000/docs
```

Para autenticar no Swagger:
1. Chame `POST /auth/token` com `{"username": "admin", "password": "admin123"}`
2. Copie o `access_token` da resposta
3. Clique em **Authorize** (canto superior direito) e cole o token

ReDoc (documentação em modo leitura) está em `http://localhost:8000/redoc`.

---

## Encerrando os serviços

```bash
docker compose down          # para os containers, mantém o volume do banco
docker compose down -v       # para e apaga o volume do banco
```

---

## Endpoints da API

| Método | Path | Acesso | Descrição |
|--------|------|--------|-----------|
| POST | `/auth/token` | Público | Obter token JWT |
| GET | `/veiculos` | USER, ADMIN | Listar veículos (paginado) |
| GET | `/veiculos?marca=&ano=&cor=&minPreco=&maxPreco=` | USER, ADMIN | Listar com filtros |
| GET | `/veiculos/{id}` | USER, ADMIN | Buscar veículo por ID |
| GET | `/veiculos/relatorios/por-marca` | USER, ADMIN | Contagem agrupada por marca |
| POST | `/veiculos` | ADMIN | Criar veículo |
| PUT | `/veiculos/{id}` | ADMIN | Atualização completa |
| PATCH | `/veiculos/{id}` | ADMIN | Atualização parcial |
| DELETE | `/veiculos/{id}` | ADMIN | Soft delete |

Parâmetros de listagem: `page` (padrão 1), `page_size` (padrão 20, máx 100), `order_by`, `order_dir` (`asc`/`desc`).

---

## Autenticação

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Use o `access_token` retornado como Bearer token em todas as demais requisições:

```bash
curl http://localhost:8000/veiculos \
  -H "Authorization: Bearer <token>"
```

---

## Rodando os testes

Os testes rodam contra as mesmas instâncias de PostgreSQL e Redis configuradas no `.env`. Suba os serviços com `docker compose up -d` antes de executar.

> **Atenção:** os testes recriam o schema do zero a cada execução. Após rodar os testes, reinicie a API e recrie os usuários:
> ```bash
> docker compose restart api
> docker compose exec api sh -c "SEED_ADMIN_PASSWORD=admin123 SEED_USER_PASSWORD=user123 python scripts/seed.py"
> ```

### 1. Instale as dependências

```bash
poetry install
```

### 2. Rode os testes com cobertura

```bash
poetry run pytest --cov=app --cov-report=term-missing
```

Cobertura atual: ~89%.

### 3. Lint

```bash
poetry run ruff check .
```

---

## Preço e taxa de câmbio

Os preços dos veículos são armazenados em USD (`preco_usd`). Cada resposta também inclui `preco_brl`, calculado em tempo real usando a taxa USD/BRL obtida da [AwesomeAPI](https://economia.awesomeapi.com.br/json/last/USD-BRL) com [Frankfurter](https://api.frankfurter.app/latest?from=USD&to=BRL) como fallback. A taxa é cacheada no Redis por `USD_CACHE_TTL` segundos (padrão 300).

---

## Comandos úteis

```bash
# Reiniciar apenas a API (re-executa migrations)
docker compose restart api

# Rebuild completo após mudanças de código
docker compose up -d --build api

# Logs em tempo real
docker compose logs -f api
docker compose logs -f db

# Banco do zero (apaga todos os dados)
docker compose down -v && docker compose up -d

# Verificar taxa de câmbio cacheada no Redis
docker compose exec redis redis-cli GET usd_brl_rate
```

---

## Arquitetura

```
app/
  core/         config, database, security, redis client
  models/       modelos ORM SQLAlchemy
  schemas/      schemas Pydantic de request/response
  repositories/ camada de acesso a dados
  services/     lógica de negócio (incluindo conversão de moeda)
  routers/      handlers de rotas FastAPI
  dependencies/ injeção de dependências FastAPI (db, auth)
scripts/
  seed.py       criação das contas iniciais admin/user
tests/
  unit/         testes de serviço com mocks
  integration/  testes de controller + repository contra DB real
  e2e/          fluxo completo: token → criar → listar → filtrar → detalhar → deletar
alembic/        migrations do banco de dados
docs/           diagramas de arquitetura e modelo de dados
```
