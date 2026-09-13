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
├── Jenkinsfile.staging    # Staging continuous integration pipeline
├── docker-compose.yml     # Base container stack definition
├── docker-compose.dev.yml # Local development overlay (exposing ports to host - strictly local PC)
├── docker-compose.staging.yml # Staging stack deployment
└── docker-compose.prod.yml       # Production deployment configuration
```

> **Environment Policy**: Development environments are strictly restricted to local developer machines (`docker-compose.dev.yml`). Remote servers are exclusively reserved for Staging and Production workloads.

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

### 2. Production Deployment (Manual)
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 3. Continuous Deployment via Jenkins (`fullstack-infrastructure`)

Production deployments are automated via the Jenkins CD Pipeline **`fullstack-infrastructure`**, which coordinates zero-downtime updates and secret isolation.

#### Pipeline Architecture
1. **Trigger**: Downstream webhook triggered by `backend` pipeline on `main`/`master` merge, or manual execution with parameters.
2. **Secret Injection**: Injects production `.env` securely from Jenkins Credential Store (`infra-prod-env` of type `Secret file`) with `chmod 600` and purges it immediately in `post { always }`.
3. **Full & Selective Deployment**: Default execution (`SERVICES="all"`) ensures full stack synchronization including datastores, networks, and secrets. Supports selective updating of specific microservices (e.g. `SERVICES="gateway user-service"`) with `--no-deps` when datastores are untouched.
4. **Health Verification**: Performs automated health checks on API Gateway (`/health`) post-deployment.
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

### 4. Dedicated Staging Environment & CI Pipeline (`fullstack-infra-stagging`)

To safeguard production datastores from automated tests and ensure determinism across the 7-layer testing matrix (Unit, PBT, Mutation, Realtime Socket.IO E2E, Contracts, Concurrency Load, and Chaos Resilience), a dedicated Staging Docker Compose stack is provided.

- **Compose Configuration**: `docker-compose.staging.yml`
- **Environment Template**: `.env.staging.example`
- **Jenkins Credential**: `infra-staging-env` (`Secret file` containing `.env.staging`)
- **Jenkins Pipeline Job**: `fullstack-infra-stagging` (`Jenkinsfile.staging`)

#### Staging Port & Service Allocation (Zero Conflict)
- Gateway Staging: `3005` (`GATEWAY_URL=http://localhost:3005`)
- MongoDB Staging: `27018` (Databases: `user_db_staging`, `notification_db_staging`)
- Redis Staging: `6380`
- RabbitMQ Staging: `5673` (Management: `15673`)
- Microservices: `3021` (`user-service-staging`), `3022` (`notification-service-staging`)

#### Triggering Staging Lifecycle via REST API
```powershell
# Deploy staging stack
curl.exe -X POST -i -u "<USER>:<API_TOKEN>" `
  "https://jenkins.dedisalam.my.id/job/fullstack-infra-stagging/buildWithParameters?ACTION=deploy&SERVICES=all"

# Check staging status
curl.exe -X POST -i -u "<USER>:<API_TOKEN>" `
  "https://jenkins.dedisalam.my.id/job/fullstack-infra-stagging/buildWithParameters?ACTION=status"

# Tear down staging stack
curl.exe -X POST -i -u "<USER>:<API_TOKEN>" `
  "https://jenkins.dedisalam.my.id/job/fullstack-infra-stagging/buildWithParameters?ACTION=down"
```

