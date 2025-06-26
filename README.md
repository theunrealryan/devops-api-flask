<<<<<<< HEAD
# DevOps-API-Flask 🚀
=======
# DevOps API Flask
>>>>>>> 3a7dc08 (Teste de espelhamento para GitHub)

[![pipeline status](https://gitlab.com/devops-api-flask/devops-api-flask/badges/main/pipeline.svg)](https://gitlab.com/devops-api-flask/devops-api-flask/-/pipelines)
[![coverage report](https://gitlab.com/devops-api-flask/devops-api-flask/badges/main/coverage.svg)](https://gitlab.com/devops-api-flask/devops-api-flask/-/graphs/main/charts)

API de tarefas simples escrita em **Flask** e empacotada em **Docker** com **Docker Compose** para desenvolvimento local, **Docker Swarm** para orquestração em produção e **GitLab CI/CD** para pipeline automatizado.

> “Build once, run everywhere” – código, testes, imagem, deploy e observabilidade num único fluxo.

---

## ✨ Funcionalidades

* CRUD de tarefas (`/tasks`) em JSON.  
* Testes unitários com **pytest** & cobertura ≥ 80 %.  
* Imagem Docker otimizada via *multi-stage build* :contentReference[oaicite:0]{index=0}.  
* Ambiente local com **docker compose** :contentReference[oaicite:1]{index=1}.  
* Escalonamento e *rolling update* em **Docker Swarm** :contentReference[oaicite:2]{index=2}.  
* Pipeline **GitLab CI/CD** que _builda_, testa, publica no *Container Registry* e faz deploy :contentReference[oaicite:3]{index=3}.

---

## 🏗️ Requisitos

| Ferramenta | Versão sugerida | Referência |
|------------|-----------------|------------|
| Python | ≥ 3.11 | :contentReference[oaicite:4]{index=4} |
| Docker Engine | ≥ 26.x | :contentReference[oaicite:5]{index=5} |
| Docker Compose | v2 | :contentReference[oaicite:6]{index=6} |
| GitLab Runner | ≥ 17 | :contentReference[oaicite:7]{index=7} |

---

## 📂 Estrutura do projeto

```

.
├── app.py              # Código Flask
├── requirements.txt    # Dependências Python
├── Dockerfile          # Build multi-stage
├── docker-compose.yml  # Ambiente local
├── tests/              # Pytest
└── .gitlab-ci.yml      # Pipeline CI/CD

````

---

## 🚀 Instalação & Execução local

```bash
# 1. clone o repositório
git clone https://gitlab.com/devops-api-flask/devops-api-flask.git
cd devops-api-flask

# 2. suba tudo com Compose
docker compose up --build -d          # cria API + Postgres

# 3. teste a API
curl -X POST http://localhost:5000/tasks \
     -H "Content-Type: application/json" \
     -d '{"title":"Estudar DevOps"}'
curl http://localhost:5000/tasks
````

O **Compose** simplifica ambientes multi-contêiner com um único arquivo YAML ([docs.docker.com][1]).

---

## 🐳 Imagem Docker

Criada em duas fases para reduzir tamanho e dependências:

```dockerfile
# build
FROM python:3.12-slim AS builder
WORKDIR /src
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# runtime
FROM python:3.12-alpine
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH="/root/.local/bin:$PATH"
CMD ["python", "app.py"]
```

Multi-stage mantém a imagem final enxuta e segura ([docs.docker.com][2]).

---

## 🐝 Pipeline GitLab CI/CD (`.gitlab-ci.yml`)

1. **build** – cria & sobe imagem para *Container Registry*.
2. **test** – roda pytest + cobertura.
3. **deploy** – atualiza serviço no Swarm via `docker service update`.

Exemplo de estágio *build*:

```yaml
build:
  stage: build
  image: docker:latest
  services: [docker:dind]
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

A combinação **Docker-in-Docker** + Runner em modo `privileged` é recomendada para builds de imagem ([docs.gitlab.com][3]).

---

## ⚓ Deploy em Docker Swarm

```bash
# no nó manager
docker swarm init --advertise-addr <IP_MANAGER>

# criar rede overlay
docker network create --driver overlay taskboard_net

# deploy inicial
docker stack deploy -c docker-compose.yml taskboard
docker service ls            # confere réplicas

# rolling update (zero-downtime)
docker service update --image $REGISTRY/taskboard:latest \
                      --update-delay 10s taskboard_web
```

O Swarm gerencia escala, auto-recuperação e rollback automático ([docs.docker.com][4]).

---

## 🧪 Testes

```bash
pip install -r requirements.txt pytest pytest-cov
pytest --cov=app
```

Os relatórios de cobertura são publicados como *artifacts* no pipeline ([docs.gitlab.com][5]).

---

## 🤝 Como contribuir

1. Crie um *fork* e uma branch `feature/<sua-feature>`.
2. Envie *Merge Request* seguindo o template.
3. Garanta pipeline verde + cobertura ≥ 80 %.
4. Será feita revisão de código assíncrona.

---

## 📜 Licença

Distribuído sob a licença **MIT** – consulte `LICENSE` para mais detalhes.

---

## 🙋‍♀️ Créditos

Inspirado na documentação oficial do Flask ([flask.palletsprojects.com][6]) e nos guias de **Docker** ([docs.docker.com][7]) e **GitLab CI/CD** ([docs.gitlab.com][8]). Agradecimentos à comunidade DevOps que mantém essas ferramentas incríveis!

---

*“Automate all the things, but entenda cada passo.”*

```
::contentReference[oaicite:16]{index=16}
```

[1]: https://docs.docker.com/compose/gettingstarted/?utm_source=chatgpt.com "Docker Compose Quickstart"
[2]: https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/?utm_source=chatgpt.com "Multi-stage builds - Docker Docs"
[3]: https://docs.gitlab.com/ci/docker/using_docker_images/?utm_source=chatgpt.com "Run your CI/CD jobs in Docker containers - GitLab Docs"
[4]: https://docs.docker.com/engine/swarm/swarm-tutorial/rolling-update/?utm_source=chatgpt.com "Apply rolling updates to a service - Docker Docs"
[5]: https://docs.gitlab.com/ci/quick_start/?utm_source=chatgpt.com "Tutorial: Create and run your first GitLab CI/CD pipeline"
[6]: https://flask.palletsprojects.com/en/stable/quickstart/?utm_source=chatgpt.com "Quickstart — Flask Documentation (3.1.x)"
[7]: https://docs.docker.com/get-started/docker-concepts/running-containers/multi-container-applications/?utm_source=chatgpt.com "Multi-container applications - Docker Docs"
[8]: https://docs.gitlab.com/ci/examples/?utm_source=chatgpt.com "GitLab CI/CD examples"
