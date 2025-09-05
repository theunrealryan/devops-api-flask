# 🐙 DevOps API Flask: Esteira de CI/CD 100% Auto-hospedada

> Template prático de **entrega contínua** com **Flask** + **Docker/Swarm** + **Traefik** + **Gitea Actions**, seguindo **Infraestrutura como Código (IaC)** e realizando *rolling updates* sem downtime.

A aplicação de exemplo é uma API em **Flask** (com *health check* em `GET /health`), mas o foco é a **arquitetura DevOps**: do `git push` ao deploy em produção, usando ferramentas **sob seu controle** em um cluster **Docker Swarm** com **Traefik** na borda.

---

## 📚 Sumário

* [Arquitetura](#arquitetura)
* [Pilha Tecnológica](#pilha-tecnologica)
* [Observabilidade (Métricas e Logs)](#observabilidade)
* [Pré-requisitos](#pre-requisitos)
* [Guia Rápido (Local)](#guia-rapido-local)
* [Execução com Docker Compose](#execucao-com-docker-compose)
* [Orquestração: Docker Swarm + Traefik](#orquestracao-docker-swarm-traefik)
* [CI/CD com Gitea Actions](#cicd-com-gitea-actions)
* [Estrutura do Repositório](#estrutura-do-repositorio)
* [Testes e Cobertura](#testes-e-cobertura)
* [Configuração (.env)](#configuracao-env)
* [Boas Práticas de Segurança](#boas-praticas-de-seguranca)
* [Troubleshooting](#troubleshooting)
* [Licença](#licenca)

---

<a id="arquitetura"></a>

## 🏛 Arquitetura

A plataforma é composta por serviços containerizados. O **Traefik** executa a terminação TLS/HTTPS, o roteamento dinâmico por *labels* e o *service discovery* do Swarm. *Workflows* do **Gitea Actions** testam, criam e publicam a imagem da API e executam o deploy com *rolling update* no nó *manager* do Swarm.

A **stack de observabilidade** composta por **Prometheus**, **Loki** e **Grafana** é responsável por monitorar e coletar métricas e logs de todos os componentes, permitindo diagnósticos rápidos e visibilidade em tempo real.

```mermaid
flowchart TD
  %% Subgráficos
  subgraph Developer[Developer]
    D[git push]
  end

  subgraph Gitea[Gitea: Git + Actions]
    GS[Gitea Server]
    R[Runner]
  end

  subgraph Registry[Container Registry]
    CR[Registry]
  end

  subgraph Swarm[Docker Swarm Cluster]
    M[Manager]
    T[Traefik Edge Router]
    A[Flask API Service]
  end

  subgraph Observability[Observability Stack]
    P[Prometheus]
    L[Loki]
    G[Grafana]
    NE[Node Exporter]
    PT[Promtail]
  end

  subgraph User[User]
    U[HTTPS Request]
  end

  %% CI flow
  D --> GS
  GS -->|trigger| R
  R -->|tests| R_T[pytest]
  R -->|build| R_B[docker build]
  R -->|push| CR
  R -->|ssh| M
  M -->|docker stack deploy| A

  %% Runtime flow
  U -->|HTTPS| T
  T --> A

  %% Observability flow
  P -->|scrapes metrics| T
  P -->|scrapes metrics| A
  P -->|scrapes metrics| NE
  PT -->|collects logs| L
  G -->|queries metrics| P
  G -->|queries logs| L
```

---

<a id="pilha-tecnologica"></a>

## 🛠️ Pilha Tecnológica

| Componente             | Tecnologia                            | O que faz                                                         |
| ---------------------- | ------------------------------------- | ----------------------------------------------------------------- |
| **Controle de versão** | **Gitea**                             | Repositório Git auto-hospedado; aciona *workflows*.               |
| **CI/CD**              | **Gitea Actions**                     | *Runners* executam testes, *build*, *push* e *deploy*.            |
| **Edge / Proxy**       | **Traefik**                           | Roteamento dinâmico via *labels*, TLS/HTTPS, *service discovery*. |
| **Backend**            | **Python 3.11+ / Flask**              | API REST com *health check* em `/health`.                         |
| **Containerização**    | **Docker**                            | Imagens reprodutíveis (multi-stage).                              |
| **Orquestração**       | **Docker Swarm**                      | *Stacks*, *services*, *rolling updates* e *rollback*.             |
| **Observabilidade**    | **Prometheus**, **Loki**, **Grafana** | Coleta e visualização de métricas e logs de toda a plataforma.    |
| **Testes**             | **pytest / pytest-cov**               | Testes de unidade e relatório de cobertura.                       |

---

<a id="observabilidade"></a>

## 🔭 Observabilidade (Métricas e Logs)

Uma plataforma DevOps robusta precisa de visibilidade completa sobre sua saúde e desempenho. A stack de **observabilidade** nesta arquitetura permite monitoramento em tempo real de todos os componentes, proporcionando uma visão consolidada de métricas e logs para uma rápida identificação de problemas e diagnóstico preciso.

### Ferramentas

| **Ferramenta** | **O que faz**                                                                                    | **Como**                                                                                                                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Prometheus** | Coleta de Métricas (o "quê" e "quando"): CPU, memória, solicitações por segundo, etc.            | Realiza "scraping" (coleta periódica) de endpoints `/metrics` expostos por **cAdvisor** (métricas de contêineres), **Node Exporter** (métricas dos hosts) e **Traefik**.                               |
| **Loki**       | Coleta de Logs (o "porquê"): Registros de eventos, erros e saídas de todas as aplicações.        | Recebe os logs enviados pelo agente **Promtail**, que é implantado em todos os nós do cluster, descobrindo e monitorando automaticamente os logs de todos os contêineres Docker.                       |
| **Grafana**    | Visualização Unificada: Criação de dashboards e gráficos a partir das métricas e logs coletados. | Conecta-se ao **Prometheus** e **Loki** como fontes de dados ("Data Sources"), permitindo a criação de painéis que correlacionam métricas e logs em uma única interface, tudo provisionado via código. |

### Implementação como Código

A configuração de toda a stack de observabilidade é gerida via **Infraestrutura como Código (IaC)**, garantindo consistência e reprodutibilidade entre os ambientes. Abaixo estão os trechos de código para configurar os componentes essenciais de observabilidade, como **Prometheus**, **Loki** e **Grafana**, em um ambiente Docker Swarm.

### 1. Definição dos Serviços no `docker-compose.yml`

Os serviços necessários para a stack de observabilidade (Prometheus, Loki, Grafana, cAdvisor e Node Exporter) são definidos para serem implantados no Docker Swarm. O cAdvisor e o Node Exporter são implantados em modo global para garantir que cada nó do cluster seja monitorado.

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus-data:/etc/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    networks:
      - traefik_proxy
    deploy:
      placement:
        constraints:
          - node.role == manager
      # Labels do Traefik para acesso via https://prometheus.local.lan

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.51.0
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - traefik_proxy
    deploy:
      mode: global

  loki:
    image: grafana/loki:2.9.0
    volumes:
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - traefik_proxy
    deploy:
      placement:
        constraints:
          - node.role == manager

  grafana:
    image: grafana/grafana:11.0.0
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana-data/provisioning:/etc/grafana/provisioning
    networks:
      - traefik_proxy
    deploy:
      placement:
        constraints:
          - node.role == manager
      # Labels do Traefik para acesso via https://grafana.local.lan

networks:
  traefik_proxy:
    external: true

volumes:
  prometheus-data:
  loki_data:
  grafana_data:
```

### 2. Configuração do Prometheus (`prometheus.yml`)

A configuração do **Prometheus** é crucial para garantir a coleta de métricas dos serviços certos. O Prometheus vai fazer scraping dos endpoints `/metrics` expostos pelos serviços **cAdvisor**, **Node Exporter** e **Traefik**.

```yaml
scrape_configs:
  # Configuração para o próprio Prometheus
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Configuração para coletar métricas do Traefik
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']

  # Configuração para coletar métricas do cAdvisor (monitoramento de contêineres)
  - job_name: 'cadvisor'
    dns_sd_configs:
      - names:
          - 'tasks.cadvisor'
        type: 'A'
        port: 8080
    metric_relabel_configs:
      - source_labels: [container_label_com_docker_swarm_service_name]
        target_label: service
        regex: (.+)
        replacement: '$1'

  # Configuração para coletar métricas do Node Exporter (monitoramento de hosts)
  - job_name: 'node-exporter'
    dns_sd_configs:
      - names:
          - 'tasks.node-exporter'
        type: 'A'
        port: 9100
```

---

<a id="pre-requisitos"></a>

## ✅ Pré-requisitos

| Ferramenta     | Versão mínima | Verificar                |
| -------------- | ------------- | ------------------------ |
| Git            | 2.20+         | `git --version`          |
| Python         | 3.11+         | `python3 --version`      |
| Docker Engine  | 24.x+         | `docker --version`       |
| Docker Compose | v2+           | `docker compose version` |

> **Dica:** Garanta que o usuário no host *manager* pode executar Docker sem `sudo` (ou ajuste os comandos).

---

<a id="guia-rapido-local"></a>

## 🚀 Guia Rápido (Local)

### 1) Clonar o repositório

```bash
git clone https://github.com/theunrealryan/devops-api-flask.git
cd devops-api-flask
```

### 2) Rodar localmente (sem Docker, opcional)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 3) Verificar *health*

```bash
curl http://localhost:5000/health
# Esperado: {"status":"healthy"}
```

---

<a id="execucao-com-docker-compose"></a>

## 🐳 Execução com Docker Compose

> Útil para desenvolvimento local com containers e validação da imagem.

```bash
docker compose up --build -d
docker ps
curl http://localhost:5000/health
```

Para parar/remover:

```bash
docker compose down -v
```

---

<a id="orquestracao-docker-swarm-traefik"></a>

## 🧩 Orquestração: Docker Swarm + Traefik

### 1) Criar a *overlay network* compartilhada (uma vez)

```bash
docker network create --driver=overlay --attachable web
```

### 2) Inicializar o Swarm (nó manager)

```bash
docker swarm init --advertise-addr <IP_MANAGER>
```

### 3) Deploy da stack

```bash
docker stack deploy -c docker-compose.yml devops
```

### 4) Escalar a API (exemplo)

```bash
docker service scale devops_api=3
```

### 5) Atualizar imagem (rolling update) e rollback

```bash
docker service update --image <registry>/devops-api-flask:<tag> devops_api
docker service update --rollback devops_api
```

### Exemplo de *labels* Traefik (ajuste domínio/porta)

```yaml
services:
  api:
    image: <registry>/devops-api-flask:latest
    networks:
      - web     # mesma overlay network do Traefik
    deploy:
      labels:
        - traefik.enable=true
        - traefik.http.routers.api.rule=Host(`api.seu-dominio.com`)
        - traefik.http.routers.api.entrypoints=websecure
        - traefik.http.routers.api.tls=true
        - traefik.http.services.api.loadbalancer.server.port=5000

networks:
  web:
    external: true
```

> Em Swarm, *labels* ficam sob `deploy.labels`. Garanta **mesma overlay** entre Traefik e API.

---

<a id="cicd-com-gitea-actions"></a>

## 🚦 CI/CD com Gitea Actions

O pipeline (ex.: `.gitea/workflows/deploy.yml`) executa:

1. **Testes** com `pytest`;
2. **Build** da imagem Docker (multi-stage);
3. **Push** ao *registry*;
4. **Deploy** no *manager* do Swarm via SSH, com `docker stack deploy -c docker-compose.yml <stack>`.

### Exemplo de workflow (`.gitea/workflows/deploy.yml`)

```yaml
name: Deploy
on:
  push:
    branches: [ main ]

jobs:
  build-test-push-deploy:
    runs-on: docker
    steps:
      - uses: actions/checkout@v4

      - name: Testes
        run: |
          python -V
          pip install -r requirements.txt pytest pytest-cov
          pytest --maxfail=1 --disable-warnings -q

      - name: Build & Push
        env:
          REGISTRY_URL: ${{ secrets.REGISTRY_URL }}
          REGISTRY_USERNAME: ${{ secrets.REGISTRY_USERNAME }}
          REGISTRY_PASSWORD: ${{ secrets.REGISTRY_PASSWORD }}
          IMAGE_REPO: devops-api-flask
        run: |
          docker login "$REGISTRY_URL" -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD"
          IMAGE_TAG=${GITHUB_SHA::7}
          docker build -t "$REGISTRY_URL/$IMAGE_REPO:$IMAGE_TAG" .
          docker push "$REGISTRY_URL/$IMAGE_REPO:$IMAGE_TAG"

      - name: Deploy no Swarm (SSH)
        env:
          SSH_HOST: ${{ secrets.SSH_HOST }}
          SSH_USER: ${{ secrets.SSH_USER }}
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          STACK_NAME: ${{ secrets.STACK_NAME }}
          COMPOSE_FILE: ${{ secrets.COMPOSE_FILE }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
            "IMAGE_TAG=${GITHUB_SHA::7} STACK_NAME=$STACK_NAME docker stack deploy -c $COMPOSE_FILE $STACK_NAME"
```

**Secrets sugeridos**:

* `REGISTRY_URL`, `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`
* `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`
* `STACK_NAME` (ex.: `devops`) e `COMPOSE_FILE` (ex.: `docker-compose.yml`)

> **Dica:** versionar imagens com a *tag* baseada no SHA curto do commit (`${GITHUB_SHA::7}`) facilita *rollbacks* reprodutíveis.

---

<a id="estrutura-do-repositorio"></a>

## 📁 Estrutura do Repositório

```
.
├─ .gitea/workflows/      # Workflows de CI/CD (Gitea Actions)
├─ tests/                 # Testes (pytest)
├─ app.py                 # Aplicação Flask (expõe /health)
├─ Dockerfile             # Build multi-stage
├─ docker-compose.yml     # Stack para Compose/Swarm (com deploy/labels)
├─ pyproject.toml         # Metadados e config de build
├─ pytest.ini             # Configuração de testes
├─ requirements.txt       # Dependências Python
├─ .gitignore
└─ LICENSE                # MIT
```

---

<a id="testes-e-cobertura"></a>

## 🧪 Testes e Cobertura

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest pytest-cov
pytest --cov=app
```

**Recomendações:**

* Cubra *rotas* críticas (incluindo `/health`) e fluxos de erro.
* Publique o *coverage* no pipeline e **falhe** *builds* abaixo de um limiar mínimo (ex.: 80%).

---

<a id="configuracao-env"></a>

## ⚙️ Configuração (.env)

Crie seu `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Variáveis comuns:

| Variável     | Exemplo      | Uso                        |
| ------------ | ------------ | -------------------------- |
| `FLASK_ENV`  | `production` | Modo de execução do Flask. |
| `FLASK_HOST` | \`0          |                            |


.0.0.0`            | Host de *bind* do servidor.                                       |
|`FLASK\_PORT`  |`5000`               | Porta do app (use a mesma no Traefik`loadbalancer.server.port`). | | `REGISTRY\_URL`|`registry.local:5000`| Registry para *push* da imagem.                                   |
|`STACK\_NAME`  |`devops\`              | Nome lógico da *stack* no Swarm.                                  |

> **Importante:** não *commitar* `.env`. Use **Secrets** no Gitea para credenciais/chaves.

---

<a id="boas-praticas-de-seguranca"></a>

## 🔐 Boas Práticas de Segurança

* **Segredos no Gitea**: tokens do registry, chaves SSH, etc.
* **Menor privilégio** no host *manager* (evite `root` e chaves amplas).
* **TLS por padrão** via Traefik (certificados válidos e *entrypoints* seguros).
* **Rollback** pronto para qualquer atualização (Swarm suporta rollback manual).
* **Pin de versão** no `Dockerfile` (evita *breakages* silenciosos).
* **Dependências auditadas**: fixe/atualize `requirements.txt` periodicamente.

---

<a id="troubleshooting"></a>

## 🛟 Troubleshooting

* **Traefik não roteia** → verifique *deploy.labels* e a **overlay network** compartilhada.
* **Rolling update travado** → `docker service ps <service>` e `docker service logs <service>`; se preciso, `docker service update --rollback`.
* **/health falha** → *health check* leve (sem dependências externas) para evitar reinícios em cascata.
* **Falha no registry** → cheque DNS/porta, `docker login` e permissões de *push*.
* **Overlay ausente** → `docker network create --driver=overlay --attachable web` e conecte Traefik + serviços.

---

<a id="licenca"></a>

## 📄 Licença

Este projeto é licenciado sob **MIT**. Veja `LICENSE`.

> *“Automate all the things, but understand each step.”*
