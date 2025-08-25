DevOps API Flask: Uma Esteira de CI/CD Auto-hospedadaEste projeto demonstra a construção de uma plataforma de entrega de software moderna, segura e automatizada, utilizando um ecossistema de ferramentas totalmente auto-hospedado. O núcleo é uma API de gerenciamento de tarefas em Flask, mas o foco principal é a arquitetura de DevOps que a suporta, seguindo os princípios de Infraestrutura como Código (IaC).O objetivo é servir como um template prático de uma esteira de CI/CD completa, onde desde o versionamento do código até o deploy em produção com zero downtime é gerenciado por ferramentas sob seu controle, orquestradas em um cluster Docker Swarm.Arquitetura do SistemaA arquitetura é composta por componentes containerizados que trabalham em conjunto para automatizar o ciclo de vida da aplicação. O Traefik atua como o ponto de entrada, gerenciando o tráfego, a segurança (HTTPS) e o roteamento para todos os serviços.Snippet de códigograph TD
    subgraph "Developer"
        Dev(Developer)
    end

    subgraph "External Services"
        Registry(Container Registry)
    end

    subgraph "User"
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
    
    Runner -- 1. Runs Tests --> Runner
    Runner -- 2. Builds Image --> Runner
    Runner -- 3. Pushes Image --> Registry
    Runner -- 4. Connects via SSH --> Manager
    
    Manager -- docker stack deploy --> API

    User -- HTTPS Request --> Traefik
    Traefik -- routes to --> Gitea
    Traefik -- routes to --> API
Pilha TecnológicaComponenteTecnologiaDescriçãoControle de VersãoGiteaServidor Git leve e auto-hospedado, que também atua como o acionador do pipeline.CI/CDGitea ActionsExecuta os workflows de automação (testar, construir, publicar e implantar).Reverse ProxyTraefikRoteador de borda que gerencia o tráfego de entrada, HTTPS e a descoberta de serviços.BackendPython 3.11+, FlaskFramework web para a construção da API RESTful.ContainerizaçãoDocker Engine, Docker ComposeEmpacotamento da aplicação e de toda a infraestrutura em containers.OrquestraçãoDocker SwarmOrquestração dos containers em produção para escalabilidade e alta disponibilidade.TestesPytest, Pytest-CovFramework para garantir a qualidade do código e medir a cobertura.Pré-requisitos e VerificaçãoFerramentaVersão MínimaPropósito no ProjetoComando de VerificaçãoGit2.20+Sistema de controle de versão para gerenciar o código-fonte.git --versionPython3.11+Linguagem e runtime principal para a API Flask.python3 --versionDocker Engine26.x+Plataforma para construir, executar e gerenciar containers.docker --versionDocker Composev2+Ferramenta para definir e executar aplicações Docker multi-container.docker compose versionGuia de Início Rápido (Desenvolvimento Local)Siga estes passos para configurar e executar o projeto em seu ambiente local.1. Clonar o RepositórioBashgit clone <URL_DO_SEU_REPOSITORIO_GITEA>
cd devops-api-flask
2. Configurar o AmbienteCopie o arquivo de exemplo .env.example para criar sua configuração local.Bashcp.env.example.env
Revise o arquivo .env para ajustar portas ou outras configurações, se necessário.3. Iniciar os ContainersUtilize o Docker Compose para construir a imagem e iniciar o container da aplicação.Bashdocker compose up --build -d
4. Verificar a ExecuçãoBash# Verifique se o container está com o status "Up"
docker ps

# Verifique o endpoint de saúde da aplicação (health check)
curl http://localhost:5000/health
# Resposta esperada: {"status": "healthy"}
Estrutura do Projeto.
├──.gitea/workflows/       # Workflows de CI/CD para Gitea Actions
│   └── deploy.yml
├── tests/                  # Suíte de testes (pytest)
│   └── test_api.py
├── app.py                  # Aplicação principal da API Flask
├── docker-compose.yml      # Definição da stack para Docker Swarm/Compose
├── Dockerfile              # Arquivo de build Docker multi-stage
├── LICENSE                 # Licença do projeto (MIT)
├── pyproject.toml          # Metadados do projeto e configuração de build
├── pytest.ini              # Configuração para o pytest
└── requirements.txt        # Dependências Python
Pipeline de CI/CD com Gitea ActionsO coração da automação está no arquivo .gitea/workflows/deploy.yml. O pipeline é acionado a cada push no branch main e executa os seguintes passos:Test: A suíte de testes unitários é executada com pytest para validar a integridade do código.Build: Uma nova imagem Docker da aplicação é construída, utilizando a estratégia multi-stage para garantir uma imagem final enxuta e segura.Push: A imagem recém-construída é enviada para um registro de contêineres (como o Docker Hub).Deploy: O Gitea Runner se conecta ao nó manager do Docker Swarm via SSH e executa o comando docker stack deploy, que instrui o Swarm a atualizar o serviço da API com a nova imagem, realizando um rolling update sem downtime.Deploy e Orquestração com Docker Swarm e TraefikNesta arquitetura, o Docker Swarm orquestra não apenas a API, mas toda a plataforma (Gitea, Runner, etc.), enquanto o Traefik gerencia o acesso a esses serviços.Infraestrutura como Código: O arquivo docker-compose.yml define toda a stack. O deploy inicial e as atualizações são gerenciados pelo comando docker stack deploy.Descoberta de Serviços: Traefik detecta automaticamente os serviços em execução no Swarm (através de labels do Docker) e cria as rotas de acesso para eles.Rolling Updates: Quando o pipeline de CI/CD aciona um docker stack deploy, o Swarm atualiza os containers da API de forma gradual (rolling update), garantindo que a aplicação permaneça disponível durante a atualização.Comandos de Gerenciamento do SwarmBash# 1. Inicie o Swarm (se ainda não o fez)
docker swarm init --advertise-addr <IP_MANAGER>

# 2. Deploy inicial da stack completa
docker stack deploy -c docker-compose.yml nome-da-stack

# 3. Escalone um serviço específico (ex: a API)
docker service scale nome-da-stack_api=3
Estratégia de TestesA qualidade do código é garantida por uma suíte de testes automatizados utilizando pytest.Executando Testes LocalmenteBash# Crie e ative um ambiente virtual
python3 -m venv.venv
source.venv/bin/activate

# Instale as dependências
pip install -r requirements.txt pytest pytest-cov

# Execute os testes
pytest --cov=app
LicençaEste projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.“Automate all the things, but understand each step.”
