# Dedisalam Infrastructure & DevOps

This directory contains the infrastructure, datastores, message brokers, reverse proxies, and deployment configurations for the Dedisalam platform, maintained by the DevOps team.

## Overview

```text
infrastructure/
├── docker/
│   ├── grafana/           # Grafana dashboards and provisioning
│   ├── mongodb/           # MongoDB initialization scripts
│   ├── nginx/             # Nginx reverse proxy and SSL certificates
│   └── prometheus/        # Prometheus scrape configurations and alerts
├── jenkins/
│   └── job-config.xml     # Jenkins declarative pipeline job definition
├── Jenkinsfile            # Continuous deployment pipeline specification
├── docker-compose.yml     # Base container stack definition
├── docker-compose.dev.yml # Local development overlay (exposing ports to host)
├── docker-compose.dev.server.yml # Development server deployment (172.16.254.2)
└── docker-compose.prod.yml       # Production deployment configuration
```

## Services Managed

| Service | Technology | Internal Port | Host Port (Dev) | Description |
|---|---|---|---|---|
| **MongoDB** | mongo:7 | 27017 | 27017 | Primary datastore (user_db, notification_db) |
| **RabbitMQ** | rabbitmq:3.13-management-alpine | 5672, 15672 | 5672, 15672 | Asynchronous message broker & management console |
| **Redis** | redis:7-alpine | 6379 | 6379 | Session cache and refresh token storage |
| **Nginx** | nginxinc/nginx-unprivileged:1.25-alpine | 8080, 8443 | 80, 443 | Edge reverse proxy & SSL termination |
| **Prometheus** | prom/prometheus:latest | 9090 | - | Metrics collection and alerts |
| **Grafana** | grafana/grafana:latest | 3000 | 3005 | Metrics visualization dashboards |

## Common Commands

### 1. Local Development Infrastructure
Start databases and brokers for local development (services exposed on localhost):
```bash
docker compose -f docker-compose.dev.yml up -d
```

Stop infrastructure:
```bash
docker compose -f docker-compose.dev.yml down
```

View infrastructure logs:
```bash
docker compose -f docker-compose.dev.yml logs -f
```

### 2. Development Server Deployment (172.16.254.2)
```bash
ssh dedisalam@172.16.254.2
cd /path/to/infrastructure
docker compose -p fullstack-dev -f docker-compose.dev.server.yml up -d --build
```

### 3. Production Deployment (Manual)
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Continuous Deployment via Jenkins (`fullstack-infrastructure`)

Production deployments are automated via the Jenkins CD Pipeline **`fullstack-infrastructure`**, which coordinates zero-downtime updates and secret isolation.

#### Pipeline Architecture
1. **Trigger**: Downstream webhook triggered by `backend` pipeline on `main`/`master` merge, or manual execution with parameters.
2. **Secret Injection**: Injects production `.env` securely from Jenkins Credential Store (`infra-prod-env` of type `Secret file`) with `chmod 600` and purges it immediately in `post { always }`.
3. **Selective Deployment**: Supports updating specific microservices (`SERVICES="gateway user-service notification-service"`) with `--no-deps` to safeguard persistent datastores (MongoDB, Redis, RabbitMQ).
4. **Health Verification**: Performs automated health checks on API Gateway (`/api/v1/health`) post-deployment.
5. **Dangling Image Cleanup**: Runs `docker image prune -f` upon successful deployment.

#### Triggering Deployment via REST API
```powershell
# Authenticate and trigger parameterized build
curl.exe -X POST -i -u "<USER>:<API_TOKEN>" `
  "https://jenkins.dedisalam.my.id/job/fullstack-infrastructure/buildWithParameters?SERVICES=gateway%20user-service%20notification-service"
```

#### Creating / Updating Job via Jenkins REST API
```powershell
# Create job from XML configuration
curl.exe -X POST -u "<USER>:<API_TOKEN>" `
  -H "Content-Type: application/xml" `
  --data-binary "@jenkins/job-config.xml" `
  "https://jenkins.dedisalam.my.id/createItem?name=fullstack-infrastructure"
```
