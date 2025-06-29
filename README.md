## DevOps API Flask 🚀

[![Pipeline Status](https://gitlab.com/devops-api-flask/devops-api-flask/badges/main/pipeline.svg)](https://gitlab.com/devops-api-flask/devops-api-flask/-/pipelines)  
[![Coverage Report](https://gitlab.com/devops-api-flask/devops-api-flask/badges/main/coverage.svg)](https://gitlab.com/devops-api-flask/devops-api-flask/-/graphs/main/charts)

Uma API de gerenciamento de tarefas em **Flask**, empacotada em **Docker**, orquestrada com **Docker Compose** (local), **Docker Swarm** (produção) e com **GitLab CI/CD** para integração e deploy contínuos.

> _“Build once, run everywhere”_ — código, testes, imagem de container, deploy e monitoramento em um fluxo automatizado.

---

## ✨ Funcionalidades

- **CRUD completo** de tarefas via rota `/tasks` (JSON)  
- **Testes automatizados** com **pytest** e cobertura ≥ 80%  
- **Build Docker multi-stage** para imagem enxuta e segura  
- **Ambiente local** pronto com **Docker Compose**  
- **Escalonamento** e **rolling updates** em **Docker Swarm**  
- **Pipeline CI/CD** no GitLab para build, testes, push e deploy automático  
- **Espelhamento (Mirror)** unidirecional para GitHub, com opção **bidirecional** (via GitLab EE/Premium ou webhooks)

---

## 🏗️ Pré-requisitos

| Ferramenta        | Versão mínima | Observações                           |
|-------------------|---------------|---------------------------------------|
| Python            | 3.11          | Use virtualenv ou venv                |
| Flask             | 3.x           |                                       |
| Docker Engine     | 26.x          |                                       |
| Docker Compose    | v2            |                                       |
| Docker Swarm      | integrado     |                                       |
| GitLab Runner     | 17.x          | com DIND habilitado                   |
| Git               | 2.20+         |                                       |
| Pytest            | 8.x           | pytest-cov para cobertura             |

---

## 🗂️ Estrutura do Projeto

```text
taskboard/
├── app.py                 # API Flask principal
├── requirements.txt       # Dependências Python
├── setup.py               # Metadados do pacote (entrypoint “taskboard”)
├── Dockerfile             # Build multi-stage
├── docker-compose.yml     # Compose para dev local
├── .gitlab-ci.yml         # CI/CD pipeline
├── pytest.ini             # Configuração pytest & cobertura
└── tests/                 # Testes (pytest)
    └── test_api.py
````

---

## 🚀 Desenvolvimento Local

1. Clone o repositório e acesse o diretório:

   ```bash
   git clone https://gitlab.com/devops-api-flask/devops-api-flask.git
   cd devops-api-flask
   ```
2. Crie e ative o ambiente virtual:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Inicialize containers com Docker Compose:

   ```bash
   docker compose up --build -d
   ```
4. Teste a API:

   ```bash
   curl -X POST http://localhost:5000/tasks \
     -H "Content-Type: application/json" \
     -d '{"title":"Estudar DevOps"}'
   curl http://localhost:5000/tasks
   ```

---

## 🐳 Dockerfile (Multi-stage)

```dockerfile
# Stage 1: build
FROM python:3.12-slim AS builder
WORKDIR /src
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: runtime
FROM python:3.12-alpine
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH="/root/.local/bin:$PATH"
CMD ["taskboard"]
```

---

## 🐝 GitLab CI/CD (`.gitlab-ci.yml`)

```yaml
stages:
  - build
  - test
  - deploy
  - mirror

variables:
  DOCKER_HOST: tcp://docker:2375
  DOCKER_TLS_CERTDIR: ""

build:
  stage: build
  image: docker:latest
  services: [docker:dind]
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA" .
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA"
  only: [main]

test:
  stage: test
  image: python:3.12
  script:
    - pip install -r requirements.txt pytest pytest-cov
    - pytest --cov=app --cov-report=xml
  artifacts:
    paths: [coverage.xml]
    reports:
      coverage_report: coverage.xml

deploy:
  stage: deploy
  when: manual
  script:
    - docker service update \
        --image "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA" \
        taskboard_web

mirror:
  stage: mirror
  image:
    name: alpine/git
    entrypoint: ["/bin/sh"]
  before_script:
    - apk add --no-cache openssh-client git
    - mkdir -p ~/.ssh
    - cp "$SSH_PRIVATE_KEY" ~/.ssh/id_ed25519_mirror
    - chmod 600 ~/.ssh/id_ed25519_mirror
    - ssh-keyscan github.com >> ~/.ssh/known_hosts
    - git config --global core.sshCommand \
        "ssh -i ~/.ssh/id_ed25519_mirror -o UserKnownHostsFile=$HOME/.ssh/known_hosts"
  script:
    - git clone --mirror "${CI_REPOSITORY_URL}" repo.git
    - cd repo.git
    - git remote add github git@github.com:theunrealryan/devops-api-flask.git || true
    - git push --mirror github
  only: [main]
```

---

## ⚓ Docker Swarm

```bash
# 1. Inicie o Swarm (manager)
docker swarm init --advertise-addr <IP_MANAGER>

# 2. Deploy da stack
docker stack deploy -c docker-compose.yml taskboard

# 3. Escalone para 3 réplicas
docker service scale taskboard_web=3

# 4. Rolling update
docker service update \
  --image "$CI_REGISTRY_IMAGE:latest" \
  --update-delay 10s \
  taskboard_web
```

---


## 🧪 Testes & Cobertura

```bash
pip install -r requirements.txt pytest pytest-cov
pytest --cov=app --cov-report=xml
```

* Cobertura mínima: **80%**
* Artefato `coverage.xml` publicado no GitLab

---



## 📜 Licença

MIT © [Ryan Ricardo de Souza](https://gitlab.com/theunrealryan)

---

*“Automate all the things, but understand each step.”*

