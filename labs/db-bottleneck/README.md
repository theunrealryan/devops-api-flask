# Lab: gargalo de banco de dados sob pico de tráfego

Demonstra por que aumentar a máquina (*scale-up*) é paliativo para gargalos de banco de dados e o que resolve de fato: índice, cache e migrações que não travam a tabela.

Stack: API Flask (gunicorn + pool de conexões psycopg), PostgreSQL 16 com 3 milhões de pedidos, Redis e k6 para gerar carga. Tudo em Docker Compose.

## Pré-requisitos

- Docker com Compose v2
- Portas livres: `8080`

> No Git Bash, rode `export MSYS_NO_PATHCONV=1` antes dos comandos; sem isso, caminhos como `/sql/...` são convertidos para caminhos do Windows. No PowerShell e no Linux/macOS não é necessário.

## Subir o ambiente

```bash
docker compose --env-file envs/baseline.env up -d --build --wait
curl "localhost:8080/orders?customer_id=42"
```

O primeiro `up` gera os 3 milhões de linhas (cerca de 1 minuto). Para recomeçar do zero: `docker compose down -v`.

Atalhos usados abaixo:

```bash
docker compose exec -T db psql -U lab -d shop -f /sql/<arquivo>.sql
docker compose --env-file envs/<perfil>.env --profile load run --rm k6 run /scripts/<script>.js
```

Variáveis do k6 (via `-e`): `RATE` (req/s), `DURATION`, `CUSTOMERS` (quantidade de clientes "quentes", padrão 1000).

## Roteiro da demo

| # | Cenário | Comandos |
|---|---|---|
| 1 | Linha de base: máquina pequena, sem índice | `read.js` com `envs/baseline.env`, depois `explain.sql` |
| 2 | Scale-up: 4x CPU e memória | `docker compose --env-file envs/scale-up.env up -d --wait`, depois `read.js` com `envs/scale-up.env` |
| 3 | Índice na máquina pequena | Voltar para `baseline.env`, `index-create.sql`, `read.js`, `explain.sql` |
| 4 | Cache sem índice (cache não salva consulta ruim) | `index-drop.sql`, `up` com `envs/cache.env`, `read.js` |
| 5 | Índice + cache com 4x a carga | `index-create.sql`, `read.js` com `-e RATE=200` |
| 6 | Lock de migração | Em paralelo: `write.js`; após alguns segundos `long-transaction.sql`; depois `migration-unsafe.sql`; observar com `locks.sql` |
| 7 | Migração segura | `migration-reset.sql`, repetir o 6 trocando por `migration-safe.sql` (`lock_timeout = 2s`) |

Entre cenários, `docker compose restart api` descarta requisições ainda enfileiradas.

## Resultados medidos

Ambiente: Windows 11, Docker Desktop (WSL2) com 8 CPUs; limites do Postgres definidos em `envs/`. Leituras a 50 req/s por 20 s, salvo indicação; escritas a 20 req/s por 50 s.

| Cenário | Falhas | p95 | p99 | Consulta |
|---|---|---|---|---|
| 1. Baseline (0,5 CPU, 512 MB) | 99,1% | timeout | timeout | Seq Scan, 18,2 s sob carga |
| 2. Scale-up (2 CPU, 2 GB) | 95,2% | timeout | timeout | Seq Scan |
| 3. Índice (0,5 CPU) | 0% | 4,1 ms | 11,7 ms | Index Scan, 0,3 ms |
| 4. Cache sem índice | 99,6% | timeout | timeout | Seq Scan nos *misses* |
| 5. Índice + cache, 200 req/s | 0% | 10,8 ms | 222 ms | 73% de acerto no cache |
| 6. Migração sem `lock_timeout` | 72,3% das escritas | 10 s | 10 s | `ALTER` na fila bloqueia todos os `INSERT` |
| 7. Migração com `lock_timeout` | 0% | 45 ms | 1,55 s | `ALTER` cancelado em 2 s |

Em outra máquina os números absolutos mudam; a relação entre os cenários se mantém enquanto a tabela for grande o suficiente para o Seq Scan não caber no cache da memória.

A métrica `max` do k6 registrou valores próximos de 2 minutos em todas as rodadas, acima do timeout de 10 s das requisições; use p95, p99 e taxa de falhas.

## Por que cada cenário se comporta assim

- **Scale-up:** a consulta continua lendo a tabela inteira; CPU extra só divide o mesmo trabalho desnecessário.
- **Índice:** muda o algoritmo, de ler 3 milhões de linhas para ler 20.
- **Cache sem índice:** com o cache frio, cada *miss* é uma consulta lenta; a fila cresce, as requisições expiram e o cache nunca aquece.
- **Lock de migração:** o `ALTER TABLE` precisa de um lock exclusivo e entra na fila atrás da transação longa; todas as consultas seguintes entram na fila atrás do `ALTER`. A migração nem começou e a API já parou.
- **`lock_timeout`:** a migração desiste rápido e pode ser repetida fora do pico; o tráfego não para.
