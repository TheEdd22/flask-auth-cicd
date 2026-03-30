# Flask Auth API — CI/CD com Docker & Kubernetes

"Este é um projeto de Portfólio e não deve ser usado em produção sem ajustes adicionais de segurança!!!"
> ⚠️ Os exemplos abaixo usam dados fictícios e são apenas para fins educacionais.


![CI/CD Pipeline](https://github.com/SEU_USUARIO/flask-auth-cicd/actions/workflows/ci-cd.yml/badge.svg)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=flat&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat&logo=python&logoColor=white)

> **Projeto de portfólio DevOps** demonstrando um pipeline CI/CD completo com autenticação JWT, containerização Docker e deploy automatizado em Kubernetes.

---

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Executar Localmente](#executar-localmente)
- [Pipeline CI/CD](#pipeline-cicd)
- [Kubernetes Deploy](#kubernetes-deploy)
- [API Endpoints](#api-endpoints)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Testes](#testes)

---

### Visão Geral

Sistema de autenticação de usuários com JWT construído com **Flask**, containerizado com **Docker** (multi-stage build) e orquestrado por **Kubernetes**. O pipeline CI/CD automatiza testes, build da imagem e deploy a cada push na branch `main`.

### Fluxo do Pipeline

```
Push → GitHub Actions → [Testes] → [Lint/Security] → [Docker Build/Push] → [Deploy K8s]
                            ↓              ↓                  ↓                   ↓
                         pytest         flake8            Docker Hub          kubectl apply
                         coverage       bandit            + Trivy scan        + rollout status
```

---

##  Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions                        │
│  push/PR → test → lint → build image → deploy to k8s   │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │    Docker Hub        │
              │  flask-auth:sha-xxx  │
              └──────────┬──────────┘
                         │ kubectl apply
         ┌───────────────▼────────────────────┐
         │         Kubernetes Cluster          │
         │  Namespace: flask-auth              │
         │                                     │
         │  ┌─────────────┐  ┌─────────────┐  │
         │  │  Flask App  │  │  Flask App  │  │  ← 2 réplicas (HPA: 2-10)
         │  │  Pod #1     │  │  Pod #2     │  │
         │  └──────┬──────┘  └──────┬──────┘  │
         │         └────────┬────────┘         │
         │          ┌───────▼───────┐          │
         │          │   Service     │          │
         │          │  LoadBalancer │          │
         │          └───────────────┘          │
         │                                     │
         │  ┌─────────────────────────────┐    │
         │  │     PostgreSQL Pod          │    │
         │  │  + PersistentVolumeClaim    │    │
         │  └─────────────────────────────┘    │
         └─────────────────────────────────────┘
```

---

## Tecnologias

| Camada          | Tecnologia                |
|-----------------|---------------------------|
| Aplicação       | Python 3.11 + Flask 3.0   |
| Banco de Dados  | PostgreSQL 15             |
| Container       | Docker (multi-stage)      |
| Orquestração    | Kubernetes (minikube/EKS) |
| CI/CD           | GitHub Actions            |
| CI/CD Alt.      | Jenkins                   |
| Autenticação    | JWT (Flask-JWT-Extended)  |
| Testes          | pytest + coverage         |
| Segurança       | Bandit + Trivy + Safety   |

---

## Executar Localmente

### Pré-requisitos
- Docker + Docker Compose
- Python 3.11 (para testes locais)

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU_USUARIO/flask-auth-cicd.git
cd flask-auth-cicd
```

### 2. Subir com Docker Compose
```bash
# Ambiente de produção
docker-compose up --build -d

# Com Adminer (interface DB)
docker-compose --profile dev up --build -d
```

### 3. Verificar saúde da aplicação
```bash
curl http://localhost:5000/health
# {"status": "healthy", "version": "1.0.0"}
```

### 4. Parar os serviços
```bash
docker-compose down -v
```

---

## Pipeline CI/CD

### GitHub Actions (`.github/workflows/ci-cd.yml`)

O pipeline possui **4 jobs** executados em sequência:

```
┌─────────┐    ┌──────┐    ┌───────┐    ┌────────┐
│  test   │───▶│ lint │───▶│ build │───▶│ deploy │
│ pytest  │    │flake8│    │docker │    │  k8s   │
│coverage │    │bandit│    │ push  │    │kubectl │
└─────────┘    └──────┘    └───────┘    └────────┘
```

#### Configurar Secrets no GitHub
```
Settings → Secrets and variables → Actions → New repository secret
```

| Secret | Descrição |
|--------|-----------|
| `DOCKERHUB_USERNAME` | Seu usuário Docker Hub |
| `DOCKERHUB_TOKEN`    | Token de acesso Docker Hub |
| `KUBECONFIG`         | kubeconfig em base64: `cat ~/.kube/config \| base64` |

---

#### Segurança no Workflow GitHub Actions
| Item | Descrição |
|------|-----------|
| **Uso de Secrets** | Todas as credenciais são armazenadas em GitHub Secrets, nunca no repositório. |
| **Mascaramento automático** | Secrets são mascarados nos logs do Actions, evitando exposição acidental. |
| **Rotação periódica** | Tokens e kubeconfig devem ser rotacionados regularmente. |
| **Princípio do menor privilégio** | Secrets devem ter apenas as permissões necessárias (push de imagem, acesso restrito ao cluster). |
| **Auditoria** | Revisar periodicamente os secrets configurados no repositório e remover os obsoletos. |



#### Configurar Credenciais no Jenkins
```Dashboard -> Manage Jenkins -> Credentials -> (Global) -> Add Credentials
```
| Credencial | Descrição |
|--------|-----------|
| `dockerhub-credentials` | Usuário e senha/token do Docker Hub armazenados no Jenkins Credentials Store |
| `kubeconfig`         | Arquivo kubeconfig seguro para acesso ao cluster Kubernetes (preferencialmente como secret file) |

#### Boas Práticas de Segurança no Jenkinsfile
| Item | Descrição |
|--------|-----------|
| `Uso de credentials()` | As credenciais são buscadas do Jenkins Credentials Store, nunca versionadas no repositório. |
| `Mascaramento em logs`         | Variáveis sensíveis devem ser mascaradas nos logs (withCredentials ou plugins de mask). |
| `Kubeconfig seguro`         | Armazenar como secret file no Jenkins, em vez de string, e usar permissões mínimas. |
| `Rotação de credenciais`         |Tokens e senhas devem ser rotacionados periodicamente para reduzir risco de vazamento.. |
| `Princípio do menor privilégio`         | Credenciais devem ter apenas as permissões necessárias (ex.: Docker push, acesso restrito ao cluster).. |
| `Auditoria`         | Armazenar como secret file no Jenkins, em vez de string, e usar permissões mínimas. |


## Kubernetes Deploy

### Minikube (desenvolvimento local)

```bash
# Iniciar cluster
minikube start --driver=docker --memory=4096

# Habilitar métricas (para HPA)
minikube addons enable metrics-server

# Aplicar manifests
kubectl apply -f k8s/deployment.yaml

# Acessar o serviço
minikube service flask-auth-service -n flask-auth

# Verificar pods
kubectl get all -n flask-auth
```

### Verificar o deploy

```bash
# Pods em execução
kubectl get pods -n flask-auth

# Logs de um pod
kubectl logs -f deployment/flask-auth-app -n flask-auth

# Descrever deployment
kubectl describe deployment flask-auth-app -n flask-auth

# Verificar HPA
kubectl get hpa -n flask-auth
```

### Rollback manual
```bash
kubectl rollout undo deployment/flask-auth-app -n flask-auth
kubectl rollout history deployment/flask-auth-app -n flask-auth
```

---

## API Endpoints

### Health Check
```http
GET /health
```
```json
{"status": "healthy", "version": "1.0.0"}
```

### Registrar Usuário
```http
POST /api/register
Content-Type: application/json

{
  "username": "joao",
  "email": "joao@email.com",
  "password": "senha123"
}
```

### Login
```http
POST /api/login
Content-Type: application/json

{
  "username": "joao",
  "password": "senha123"
}
```
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {"id": 1, "username": "joao", "email": "joao@email.com"}
}
```

### Perfil (autenticado)
```http
GET /api/profile
Authorization: Bearer <access_token>
```

### Listar Usuários (autenticado)
```http
GET /api/users
Authorization: Bearer <access_token>
```

---

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_URL` | `sqlite:///users.db` | URL de conexão com banco |
| `JWT_SECRET_KEY` | `dev-secret-...` | Chave secreta JWT (mudar em produção!) |
| `FLASK_DEBUG` | `false` | Modo debug |
| `APP_VERSION` | `1.0.0` | Versão da aplicação |

---

## Testes

```bash
# Instalar dependências
pip install -r app/requirements.txt

# Executar testes
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=app --cov-report=html

# Abrir relatório de cobertura
open htmlcov/index.html
```

### Casos de teste cobertos:
- ✅ Health check endpoint
- ✅ Registro de novo usuário
- ✅ Rejeição de username duplicado
- ✅ Login com credenciais válidas
- ✅ Rejeição de credenciais inválidas
- ✅ Proteção de rota com JWT
- ✅ Acesso ao perfil com token válido
- ✅ Validação de campos obrigatórios

---

## Estrutura do Projeto

```
flask-auth-cicd/
├── app/
│   ├── app.py              # Aplicação Flask principal
│   └── requirements.txt    # Dependências Python
├── tests/
│   └── test_app.py         # Testes unitários e de integração
├── k8s/
│   └── deployment.yaml     # Manifests Kubernetes completos
├── jenkins/
│   └── Jenkinsfile         # Pipeline Jenkins (alternativo)
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # GitHub Actions pipeline
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Ambiente local
└── README.md
```

---

## Contribuindo

1. Fork o projeto
2. Crie sua branch: `git checkout -b feature/nova-feature`
3. Commit: `git commit -m 'feat: adiciona nova feature'`
4. Push: `git push origin feature/nova-feature`
5. Abra um Pull Request

---


#### Checklist de Publicação Segura
| Item | Descrição |
|------|-----------|
| **Secrets** | Nunca versionar `.env`, senhas, tokens ou kubeconfig. Usar GitHub Secrets/Jenkins Credentials. |
| **Placeholders** | Manifests Kubernetes e docker-compose devem conter credenciais fictícias (`YOUR_DOCKERHUB_USER`, `super-secret-key`). |
| **.gitignore** | Garantir que arquivos locais (`*.db`, logs, coverage, IDE configs) estão ignorados. |
| **Branch Protection** | Configurar regras no GitHub: PR obrigatório, testes passando, revisão antes de merge em `main`. |
| **Dependabot** | Ativar para alertas de vulnerabilidade em dependências Python. |
| **CodeQL Analysis** | Ativar análise de segurança nativa do GitHub. |
| **Pipeline Secrets** | Configurar `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `KUBECONFIG` via GitHub Secrets. |
| **Aviso no README** | Informar que o projeto é educacional/portfólio e não deve ser usado em produção sem ajustes. |
| **Licença** | Incluir MIT License (já presente). |
| **Auditoria** | Revisar commits para garantir que nenhum dado sensível foi versionado. |




## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">
  <strong>Desenvolvido como projeto de portfólio DevOps</strong><br>
  Docker • Kubernetes • CI/CD • Flask • PostgreSQL
</div>
