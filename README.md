🐙 DevOps API Flask: Uma Esteira de CI/CD 100% Auto-hospedadaEste projeto é um guia prático e um template para construir uma plataforma de entrega de software moderna, segura e automatizada, utilizando um ecossistema de ferramentas totalmente auto-hospedado.O núcleo é uma API de gerenciamento de tarefas em Flask, mas o verdadeiro protagonista é a arquitetura de DevOps que a suporta, seguindo os princípios de Infraestrutura como Código (IaC). O objetivo é claro: demonstrar uma esteira de CI/CD completa, onde cada etapa — do git push ao deploy em produção com zero downtime — é gerenciada por ferramentas sob seu total controle, orquestradas em um cluster Docker Swarm.🏛️ Arquitetura do SistemaA arquitetura é composta por componentes containerizados que trabalham em conjunto para automatizar o ciclo de vida da aplicação. O Traefik atua como o ponto de entrada (Edge Router), gerenciando todo o tráfego, a segurança (HTTPS) e o roteamento para todos os serviços internos.Snippet de códigograph TD
    subgraph "👨‍💻 Developer"
        Dev(Developer)
    end

    subgraph "☁️ External Services"
        Registry(Container Registry)
    end

    subgraph "👤 User"
        User(User)
    end

    subgraph "Self-Hosted Cluster (Docker Swarm)"
        Gitea
        Runner
        Traefik
        Manager
        API
    end

    Dev -- git push --> Gitea
    Gitea -- triggers workflow --> Runner
    
    Runner -- 1. ✅ Runs Tests --> Runner
    Runner -- 2. 📦 Builds Image --> Runner
    Runner -- 3. ⬆️ Pushes Image --> Registry
    Runner -- 4.  SSH --> Manager
    
    Manager -- docker stack deploy --> API

    User -- HTTPS Request --> Traefik
    Traefik -- routes to --> Gitea
    Traefik -- routes to --> API
🛠️ Pilha TecnológicaComponenteTecnologiaDescrição Técnica🐙 Controle de VersãoGiteaServidor Git leve e auto-hospedado. Atua como o origin do nosso código e o acionador (trigger) do pipeline de CI/CD.🚀 CI/CDGitea ActionsOrquestrador de workflows que executa as automações definidas em .gitea/workflows/. É o "motor" do nosso pipeline.🚦 Reverse ProxyTraefikRoteador de borda dinâmico. Gerencia o tráfego de entrada, emite certificados SSL/TLS (HTTPS) e descobre serviços automaticamente no Docker Swarm.🐍 BackendPython 3.11+ / FlaskFramework web minimalista usado para construir a API RESTful.🐳 ContainerizaçãoDocker & ComposeEmpacota a aplicação e toda a infraestrutura em containers portáteis e consistentes. O docker-compose.yml define a stack completa.swarm OrquestraçãoDocker SwarmOrquestra os containers em produção, garantindo escalabilidade, alta disponibilidade e atualizações sem downtime (rolling updates).🧪 TestesPytest & Pytest-CovFramework para garantir a qualidade do código através de testes automatizados e para medir a cobertura de código.✅ Pré-requisitosGaranta que seu ambiente de desenvolvimento possua as seguintes ferramentas instaladas:FerramentaVersão MínimaPropósito no ProjetoComando de VerificaçãoGit2.20+Sistema de controle de versão.git --versionPython3.11+Linguagem e runtime da API.python3 --versionDocker Engine26.x+Plataforma para construir e executar containers.docker --versionDocker Composev2+Ferramenta para definir e executar a stack.docker compose version🚀 Guia de Início Rápido (Desenvolvimento Local)Siga estes passos para ter o projeto rodando em sua máquina local.1. Clonar o RepositórioBashgit clone <URL_DO_SEU_REPOSITORIO_GITEA>
cd devops-api-flask
2. Configurar o AmbienteCopie o arquivo de exemplo .env.example para criar sua configuração local.Bashcp.env.example.env
💡 Revise o arquivo .env para ajustar portas ou outras configurações, se necessário.3. Iniciar os ContainersUtilize o Docker Compose para construir a imagem e iniciar o container da aplicação em modo detached.Bashdocker compose up --build -d
4. Verificar a ExecuçãoBash# Verifique se o container está com o status "Up"
docker ps

# Verifique o endpoint de saúde da aplicação (health check)
curl http://localhost:5000/health
# Resposta esperada: {"status": "healthy"}
📁 Estrutura do Projeto.
├──.gitea/workflows/       # 🚀 Workflows de CI/CD para Gitea Actions
│   └── deploy.yml
├── tests/                  # 🧪 Suíte de testes (pytest)
│   └── test_api.py
├── app.py                  # 🐍 Aplicação principal da API Flask
├── docker-compose.yml      # 🏗️ Definição da stack para Docker Swarm/Compose
├── Dockerfile              # 📦 Arquivo de build Docker multi-stage
├── LICENSE                 # 📜 Licença do projeto (MIT)
├── pyproject.toml          # ⚙️ Metadados do projeto e configuração de build
├── pytest.ini              # 🔬 Configuração para o pytest
└── requirements.txt        # 📦 Dependências Python
🔄 Pipeline de CI/CD com Gitea ActionsO coração da automação está no arquivo .gitea/workflows/deploy.yml. O pipeline é acionado a cada push no branch main e executa os seguintes passos:✅ Test: A suíte de testes unitários é executada com pytest para validar a integridade do código.📦 Build: Uma nova imagem Docker da aplicação é construída, utilizando a estratégia multi-stage para garantir uma imagem final enxuta e segura.⬆️ Push: A imagem recém-construída é enviada para um registro de contêineres (como o Docker Hub).🚀 Deploy: O Gitea Runner se conecta ao nó manager do Docker Swarm via SSH e executa o comando docker stack deploy, que instrui o Swarm a atualizar o serviço da API com a nova imagem, realizando um rolling update sem downtime.🏗️ Deploy e Orquestração com Docker Swarm + TraefikInfraestrutura como Código (IaC): O arquivo docker-compose.yml é a única fonte da verdade para toda a stack. O deploy e as atualizações são gerenciados pelo comando docker stack deploy.Descoberta de Serviços: Traefik detecta automaticamente os serviços em execução no Swarm (através de labels do Docker) e cria as rotas de acesso para eles. Não há necessidade de configuração manual de proxy.Rolling Updates: Quando o pipeline aciona um docker stack deploy, o Swarm atualiza os containers da API de forma gradual, garantindo que a aplicação permaneça disponível durante a atualização.Comandos de Gerenciamento do SwarmBash# 1. Inicie o Swarm (se ainda não o fez)
docker swarm init --advertise-addr <IP_MANAGER>

# 2. Deploy inicial da stack completa
docker stack deploy -c docker-compose.yml nome-da-stack

# 3. Escale um serviço específico (ex: a API)
docker service scale nome-da-stack_api=3
🧪 Estratégia de TestesA qualidade do código é garantida por uma suíte de testes automatizados utilizando pytest.Executando Testes LocalmenteBash# Crie e ative um ambiente virtual
python3 -m venv.venv
source.venv/bin/activate

# Instale as dependências
pip install -r requirements.txt pytest pytest-cov

# Execute os testes e veja o relatório de cobertura
pytest --cov=app
📜 LicençaEste projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.“Automate all the things, but understand each step.”
