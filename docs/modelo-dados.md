# Modelo de Dados

```mermaid
erDiagram
    USERS {
        string  id          PK  "UUID"
        string  username        "único, indexado"
        string  password_hash
        enum    role            "USER | ADMIN"
        boolean ativo
        datetime created_at
    }

    VEHICLES {
        string  id          PK  "UUID"
        string  placa           "único entre ativos, indexado"
        string  marca           "indexado"
        string  modelo
        integer ano
        string  cor
        numeric preco_usd       "armazenado em dólar"
        boolean ativo           "soft delete"
        datetime created_at
        datetime updated_at
    }
```

## Observações

- `ativo = false` representa registros removidos via soft delete — nunca excluídos fisicamente.
- `preco_usd` é armazenado em dólar americano (USD). A conversão para BRL é feita em tempo de consulta usando a taxa em cache no Redis.
- `placa` possui índice único parcial no banco (`WHERE ativo = true`), ou seja, a mesma placa pode ser reutilizada após um soft delete. A validação na camada de serviço também filtra apenas veículos ativos, retornando HTTP 409 antes de atingir o banco.
