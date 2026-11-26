# Lab: gargalo de banco de dados sob pico de tráfego

Demonstra por que aumentar a máquina (*scale-up*) é paliativo para gargalos de banco de dados e o que resolve de fato: índice, cache e migrações que não travam a tabela.

Case sugerido por Igor Dantas, SRE Sênior no C6 Bank. Material da palestra "Funciona na minha máquina (grande): o paliativo do scale-up" (live 24h Black Friday LINUXtips 2026).

Stack: API Flask (gunicorn + pool de conexões psycopg), PostgreSQL 16 com 3 milhões de pedidos, Valkey como cache no padrão cache-aside e k6 para gerar carga. Banco, cache e API rodam em Docker Compose; o k6 roda direto na máquina.

```
k6 ──HTTP──> API Flask ──1. GET orders:{id}──> Valkey   (achou: responde)
                       ──2. SELECT ... LIMIT 20──> PostgreSQL   (não achou)
                       ──3. SET orders:{id} EX 30──> Valkey
```

## Pré-requisitos

- Docker com Compose v2
- k6 instalado na máquina (`winget install GrafanaLabs.k6`, `brew install k6` ou o pacote da distribuição)
- Python 3.11 ou mais novo, para o `run_scenarios.py`
- Porta livre: `8080`

O k6 roda fora do Docker de propósito. No Docker Desktop, o relógio da VM pula e o k6 dentro de um container registrou durações negativas e máximos acima do próprio timeout. O serviço `k6` do `compose.yaml` continua disponível para Linux, onde o problema não aparece.

> No Git Bash, rode `export MSYS_NO_PATHCONV=1` antes dos comandos `docker compose exec`; sem isso, caminhos como `/sql/...` são convertidos para caminhos do Windows.

## Rodar tudo

```bash
python run_scenarios.py
```

O script sobe o ambiente, roda os cenários na ordem e grava em `results/` a tabela `results.md`, o `results.json`, os dois `EXPLAIN` e as saídas das migrações. Leva cerca de 10 minutos.

## Gravar a demo

```bash
uv run --with pillow python demo/record_demo.py          # todos os clipes
uv run --with pillow python demo/record_demo.py 4        # só o clipe de cache
```

O script roda os comandos de verdade, captura a saída e renderiza um vídeo de terminal por cenário em `demo/out/` (MP4 1280x720 e a última tela em PNG). As esperas longas aparecem encurtadas e marcadas como "acelerado". Precisa de Docker, k6 e ffmpeg no PATH (`winget install Gyan.FFmpeg`). Ele para com erro se o Docker não estiver rodando.

Os números variam entre rodadas, principalmente perto da saturação: a tabela abaixo é uma rodada do `run_scenarios.py`, e cada vídeo mostra a rodada em que foi gravado.

## Rodar um cenário à mão

```bash
docker compose --env-file envs/baseline.env up -d --build --wait
curl "localhost:8080/orders?customer_id=42"
k6 run -e RATE=50 -e DURATION=20s k6/read.js
docker compose exec -T db psql -U lab -d shop -f /sql/<arquivo>.sql
```

O primeiro `up` gera os 3 milhões de linhas (cerca de 1 minuto). Para recomeçar do zero: `docker compose down -v`. Trocar de máquina ou ligar o cache é trocar o `--env-file`: `baseline.env` (0,5 CPU, 512 MB, sem cache), `scale-up.env` (2 CPU, 2 GB) e `cache.env` (máquina pequena, Valkey com TTL de 30 s). Entre cenários, `docker compose restart api` descarta requisições ainda enfileiradas.

| # | Cenário | O que muda |
|---|---|---|
| 1 | Sem índice, máquina pequena | `baseline.env`, `read.js` a 50 req/s, depois `explain.sql` |
| 2 | Scale-up | `scale-up.env`, mesma carga |
| 3 | Índice, máquina pequena | `index-create.sql`, `baseline.env`, mesma carga |
| 4 | Só o índice, carga maior | `read.js` a 200 e a 500 req/s |
| 5 | Índice + Valkey | `cache.env`, mesmas cargas do 4 |
| 6 | Lock de migração | `write.js` a 20 req/s; após 8 s `long-transaction.sql`; após 4 s `migration-unsafe.sql`; observar com `locks.sql` |
| 7 | Migração segura | Igual ao 6 com `migration-safe.sql` (`lock_timeout = 2s`) |

## Resultados medidos

Windows 11, Docker Desktop (WSL2) com 8 CPUs, k6 nativo. Leituras por 20 s; escritas a 20 req/s por 50 s. "Transações no banco" é o aumento de `xact_commit` durante a rodada e inclui o teste de conexão que o pool faz a cada uso; compare a proporção entre cenários.

| Cenário | Requisições | Falhas | p95 | p99 | Descartadas | Transações no banco | Acerto do cache |
|---|---|---|---|---|---|---|---|
| 1. Sem índice, 50 req/s | 576 | 99,3% | 10,0 s | 10,0 s | 425 | 184 | - |
| 2. Scale-up, 50 req/s | 592 | 92,4% | 10,0 s | 10,0 s | 411 | 433 | - |
| 3. Índice, 50 req/s | 1.001 | 0% | 15,8 ms | 30,4 ms | 0 | 1.910 | - |
| 4. Só índice, 200 req/s | 4.000 | 0% | 6,8 ms | 46,0 ms | 0 | 7.345 | - |
| 5. Índice + Valkey, 200 req/s | 4.000 | 0% | 21,9 ms | 43,6 ms | 0 | 4.648 | 35,0% |
| 4. Só índice, 500 req/s | 9.207 | 0% | 776 ms | 880 ms | 793 | 16.197 | - |
| 5. Índice + Valkey, 500 req/s | 9.975 | 0% | 90,8 ms | 147 ms | 25 | 8.144 | 58,7% |
| 6. Migração sem `lock_timeout` | 832 | 70,6% | 10,0 s | 10,0 s | 168 | - | - |
| 7. Migração com `lock_timeout` | 991 | 0% | 7,0 ms | 1,47 s | 10 | - | - |

`EXPLAIN (ANALYZE, BUFFERS)` da consulta do cliente 42: sem índice, Parallel Seq Scan com 1,5 milhão de linhas descartadas por worker e 5.697 ms (medido logo após a carga do cenário 1); com índice, Index Scan e 0,59 ms.

Em outra máquina os números absolutos mudam; a relação entre os cenários se mantém enquanto a tabela for grande demais para caber na memória.

## Por que cada cenário se comporta assim

- **Scale-up:** a consulta continua lendo a tabela inteira; CPU extra só divide o mesmo trabalho desnecessário.
- **Índice:** muda o algoritmo, de ler 3 milhões de linhas para ler 20.
- **Valkey:** a 200 req/s o índice sozinho dá conta e o cache só acrescenta um salto de rede. A 500 req/s o Valkey tirou de 20% a 47% da CPU do banco em todas as rodadas, mas a API (2 workers gunicorn) passa a usar perto de 2,7 CPUs e vira o gargalo; por isso o p95 oscila muito entre rodadas (a mediana de 3 rodadas foi 716 ms só com índice e 383 ms com Valkey, e numa delas o Valkey saiu pior). Depois de corrigir um gargalo, meça de novo: ele muda de lugar. Cache sem índice não ajuda: com o cache frio, cada *miss* é um Seq Scan, a fila cresce e o cache nunca aquece.
- **Lock de migração:** o `ALTER TABLE` precisa de um lock exclusivo e entra na fila atrás da transação longa; todas as consultas seguintes entram na fila atrás do `ALTER`. A migração nem começou e a API já parou.
- **`lock_timeout`:** a migração desiste rápido e pode ser repetida fora do pico; o tráfego não para.
