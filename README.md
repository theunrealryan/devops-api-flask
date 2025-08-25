````markdown
# 🐙 DevOps API Flask — Esteira de CI/CD 100% Auto-hospedada

> Template prático de **entrega contínua** com **Flask** + **Docker/Swarm** + **Traefik** + **Gitea Actions**, seguindo **Infraestrutura como Código (IaC)** e realizando *rolling updates* sem downtime.

O app de exemplo é uma API em **Flask** (com *health check* em `GET /health`), mas o foco é a **arquitetura DevOps**: do `git push` ao deploy em produção, usando ferramentas **sob seu controle** em um cluster **Docker Swarm** com **Traefik** na borda.

---

## 📚 Sumário

- [Arquitetura](#-arquitetura)
- [Pilha Tecnológica](#-pilha-tecnológica)
- [Pré-requisitos](#-pré-requisitos)
- [Guia Rápido (Local)](#-guia-rápido-local)
- [Execução com Docker Compose](#-execução-com-docker-compose)
- [Orquestração: Docker Swarm + Traefik](#-orquestração-docker-swarm--traefik)
- [CI/CD com Gitea Actions](#-cicd-com-gitea-actions)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Testes e Cobertura](#-testes-e-cobertura)
- [Configuração (.env)](#-configuração-env)
- [Boas Práticas de Segurança](#-boas-práticas-de-segurança)
- [Troubleshooting](#-troubleshooting)
- [Licença](#-licença)

---

## 🏛 Arquitetura

A plataforma é composta por serviços containerizados. O **Traefik** executa a terminação TLS/HTTPS, o roteamento dinâmico por *labels* e o *service discovery* do Swarm. *Workflows* do **Gitea Actions** testam, criam e publicam a imagem da API e executam o deploy com *rolling update* no nó *manager* do Swarm.

```mermaid
graph TD
  subgraph Dev["👨‍💻 Developer"]
    D[git push]
  end

  subgraph Gitea["🐙 Gitea (Git + Actions)"]
    G[Gitea Server]
    R[Runner]
  end

  subgraph Registry["☁️ Container Registry"]
    CR[(Registry)]
  end

  subgraph Swarm["🧩 Docker Swarm Cluster"]
    T[Traefik Edge Router]
    A[(Flask API)]
    M[(Manager)]
  end

  subgraph User["👤 User"]
    U[HTTPS Request]
  end

  D --> G
  G -->|trigger| R
  R -->|1. Test| R
  R -->|2. Build| R
  R -->|3. Push| CR
  R -->|4. SSH| M
  M -->|docker stack deploy| A

  U -->|HTTPS| T
  T -->|routes| A
  T -->|routes| G
````

---

## 🛠️ Pilha Tecnológica

| Componente             | Tecnologia               | O que faz                                                         |
| ---------------------- | ------------------------ | ----------------------------------------------------------------- |
| **Controle de versão** | **Gitea**                | Repositório Git auto-hospedado; aciona *workflows*.               |
| **CI/CD**              | **Gitea Actions**        | *Runners* executam testes, *build*, *push* e *deploy*.            |
| **Edge / Proxy**       | **Traefik**              | Roteamento dinâmico via *labels*, TLS/HTTPS, *service discovery*. |
| **Backend**            | **Python 3.11+ / Flask** | API REST com *health check* em `/health`.                         |
| **Containerização**    | **Docker**               | Imagens reprodutíveis (multi-stage).                              |
| **Orquestração**       | **Docker Swarm**         | *Stacks*, *services*, *rolling updates* e *rollback*.             |
| **Testes**             | **pytest / pytest-cov**  | Testes de unidade e relatório de cobertura.                       |

---

## ✅ Pré-requisitos

| Ferramenta     | Versão mínima | Verificar                |
| -------------- | ------------- | ------------------------ |
| Git            | 2.20+         | `git --version`          |
| Python         | 3.11+         | `python3 --version`      |
| Docker Engine  | 26.x+         | `docker --version`       |
| Docker Compose | v2+           | `docker compose version` |

---

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

## 🧩 Orquestração: Docker Swarm + Traefik

1. **Inicializar o Swarm (nó manager):**

```bash
docker swarm init --advertise-addr <IP_MANAGER>
```

2. **Deploy da stack:**

```bash
docker stack deploy -c docker-compose.yml devops
```

3. **Escalar a API (exemplo):**

```bash
docker service scale devops_api=3
```

4. **Atualizar imagem (rolling update) e rollback:**

```bash
# Trocar imagem do service
docker service update --image <registry>/devops-api-flask:<tag> devops_api

# Se algo falhar, reverter
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

> Em Swarm, *labels* de serviços ficam sob `deploy.labels`. Garanta que o Traefik esteja na **mesma overlay network** da API.

---

## 🚦 CI/CD com Gitea Actions

O pipeline (ex.: `.gitea/workflows/deploy.yml`) executa:

1. **Testes** com `pytest`;
2. **Build** da imagem Docker (multi-stage);
3. **Push** ao *registry*;
4. **Deploy** no *manager* do Swarm via SSH, com `docker stack deploy -c docker-compose.yml <stack>`.

### Exemplo conceitual de workflow (`.gitea/workflows/deploy.yml`)

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
        run: |
          docker login "$REGISTRY_URL" -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD"
          IMAGE_TAG=${GITEA_SHA::7}
          docker build -t "$REGISTRY_URL/devops-api-flask:$IMAGE_TAG" .
          docker push "$REGISTRY_URL/devops-api-flask:$IMAGE_TAG"

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
            "IMAGE_TAG=${GITEA_SHA::7} STACK_NAME=$STACK_NAME docker stack deploy -c $COMPOSE_FILE $STACK_NAME"
```

**Secrets sugeridos** (repositório/organização):

* `REGISTRY_URL`, `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`
* `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`
* `STACK_NAME` (ex.: `devops`) e `COMPOSE_FILE` (ex.: `docker-compose.yml`)

> Dica: mantenha a tag da imagem atrelada ao SHA do commit (`${GITEA_SHA::7}`) para *rollbacks* previsíveis.

---

## 📁 Estrutura do Repositório

```
.
├─ .gitea/workflows/      # Workflows de CI/CD (Gitea Actions)
├─ tests/                 # Testes (pytest)
├─ app.py                 # Aplicação Flask (expõe /health)
├─ Dockerfile             # Build multi-stage
├─ docker-compose.yml     # Stack para Compose/Swarm
├─ pyproject.toml         # Metadados e config de build
├─ pytest.ini             # Configuração de testes
├─ requirements.txt       # Dependências Python
├─ .gitignore
├─ .gitlab-ci.yml         # (alternativa CI) GitLab CI
└─ LICENSE                # MIT
```

---

## 🧪 Testes e Cobertura

Executar localmente (fora de Docker):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest pytest-cov
pytest --cov=app
```

> Recomendações: cubra *rotas* críticas, *health check* e *tratamento de erros*. Integre `pytest-cov` ao pipeline para bloquear merges com cobertura abaixo de um limiar.

---

## ⚙️ Configuração (.env)

Crie seu `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Variáveis comuns:

| Variável       | Exemplo               | Uso                                                               |
| -------------- | --------------------- | ----------------------------------------------------------------- |
| `FLASK_ENV`    | `production`          | Modo de execução do Flask.                                        |
| `FLASK_HOST`   | `0.0.0.0`             | Host de *bind* do servidor.                                       |
| `FLASK_PORT`   | `5000`                | Porta do app (use a mesma no Traefik `loadbalancer.server.port`). |
| `REGISTRY_URL` | `registry.local:5000` | Registry para *push* da imagem.                                   |
| `STACK_NAME`   | `devops`              | Nome lógico da *stack* no Swarm.                                  |

> **Importante:** não *commitar* `.env` — use secrets no Gitea para credenciais e chaves.

---

## 🔐 Boas Práticas de Segurança

* **Segredos no Gitea**: tokens do registry, chaves SSH, etc.
* **Princípio do menor privilégio** no host *manager* (sem `root` desnecessário).
* **TLS por padrão** via Traefik (certificados válidos, *entrypoints* seguros).
* **Rollback** planejado para qualquer atualização (Swarm suporta rollback manual).
* **Pin de versão** em imagens base do Dockerfile (evita que *builds* quebrem silenciosamente).

---

## 🛟 Troubleshooting

* **Traefik não roteia** → verifique *labels* sob `deploy.labels` e a **overlay network** compartilhada.
* **Rolling update travado** → `docker service ps <service>` e `docker service logs <service>`. Se preciso, `docker service update --rollback`.
* **/health falha** → mantenha o *health check* leve (sem dependências externas) para evitar reinícios em cascata.
* **Falha ao acessar registry** → confirme DNS/porta, login no *registry* e permissões de push.

---

## 📄 Licença

Este projeto é licenciado sob **MIT**. Veja `LICENSE`.

> *“Automate all the things, but understand each step.”*

```

**Fonte de verificação do conteúdo do repositório:** :contentReference[oaicite:0]{index=0}
::contentReference[oaicite:1]{index=1}
```
