---
name: devops-compose-management
description: "Use when starting, stopping, building, or deploying Docker Compose stacks, or when preparing local development environments for frontend (full backend parity) or backend (datastores only) with 100% real production-cloned seed data."
tier: local
target-stacks: ["docker", "docker-compose", "mongodb", "rabbitmq", "redis", "nginx", "nestjs"]
metadata:
  origin: auto-extracted
---

# DevOps Compose Management

**Extracted:** 2026-09-10  
**Context:** Multi-environment Docker Compose lifecycle management for the Dedisalam platform infrastructure.

> **Environment Policy**: Development workloads are strictly local PC only (`docker-compose.dev.yml` or containerized local stack). Remote servers (172.16.254.2) are exclusively dedicated to Staging and Production.

## Compose Profiles Reference

### 1. Local Development Stack (Strictly Local PC)
Run backing datastores and brokers for local microservice developers with host port exposure:
```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml down
```

#### Target Disambiguation Gate (Frontend vs Backend)
When the user generically requests "siapkan lingkungan development" (or "prepare development environment") **without specifying** whether frontend or backend is targeted:
1. **Mandatory Clarification**: Do NOT guess or spin up/stop services prematurely. Ask the user for clarification:
   > *"Which development environment would you like to prepare?*  
   > *1. **Frontend**: Runs production backend images + all datastores in Docker (port 3000, 27017, etc.) so you can run the frontend manually (`npm run dev`).*  
   > *2. **Backend**: Runs only datastores and message brokers in Docker (MongoDB, Redis, RabbitMQ) and frees host application ports (3000, 3001, 3002) so you can run NestJS microservices manually (`npm run start:dev`)."*
2. **Execute Confirmed Protocol**: Once the user chooses, execute either the Frontend or Backend protocol below.

#### Production Data Cloning Protocol (100% Real Production Seed)
Executed as a mandatory step when preparing any local development environment (frontend or backend) to ensure developers never guess mock data:
1. **Extract Production Credentials Dynamically** (Zero hardcoded secrets):
   ```powershell
   $prodMongoPass = (docker.exe --context prod-server exec mongodb env | Select-String "MONGO_INITDB_ROOT_PASSWORD=").ToString().Split("=")[1].Trim()
   ```
2. **Dump Production Databases to Archive**:
   ```powershell
   docker.exe --context prod-server exec mongodb mongodump -u root -p $prodMongoPass --authenticationDatabase admin --archive=/tmp/prod_dump.archive
   ```
3. **Transfer and Restore Directly to Local Development MongoDB**:
   ```powershell
   docker.exe --context prod-server cp mongodb:/tmp/prod_dump.archive ./scratch_prod_dump.archive
   docker.exe cp ./scratch_prod_dump.archive mongodb:/tmp/prod_dump.archive
   Remove-Item ./scratch_prod_dump.archive -Force
   docker.exe exec mongodb mongorestore -u root -p rootpassword --authenticationDatabase admin --archive=/tmp/prod_dump.archive --nsInclude="user_db.*" --nsInclude="notification_db.*" --drop
   docker.exe --context prod-server exec mongodb rm -f /tmp/prod_dump.archive
   ```

#### Production-Parity Frontend Development Environment Protocol
Triggered whenever requested to prepare development environment for frontend work ("prepare development environment [frontend]"):
1. **Pull Latest Production Images**: Pull newest immutable backend microservice images from Docker Hub to ensure exact parity with production:
   ```bash
   docker pull dedisalam/backend-gateway:latest
   docker pull dedisalam/backend-user-service:latest
   docker pull dedisalam/backend-notification-service:latest
   ```
2. **Recreate Dev Stack Without Data Loss**: Recreate containers using `docker-compose.dev.yml` while preserving persistent data volumes (`mongodb_data`, `rabbitmq_data`):
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```
3. **Clone Production Seed Data**: Execute the *Production Data Cloning Protocol* to sync real production records into local MongoDB.
4. **Mandatory Health Verification**: Verify all containers report `Up (healthy)`:
   - Gateway: `curl -i http://localhost:3000/health` (must return `{"status":"ok","realtime":true}`)
   - MongoDB: Exposed on port `27017`
   - Redis: Exposed on port `6379`
   - RabbitMQ: AMQP on `5672`, Management UI on `15672`
5. **Dangling Image Cleanup**: Automatically reclaim disk space by purging superseded container image layers:
   ```bash
   docker image prune -f
   ```
6. **Frontend Handoff**: Verify frontend dev ports (`4000`, `4001`, `4002`) are free and `dist/shared-ui` is built, leaving the frontend dev server (`npm run dev`) for the user to launch manually.

#### Backend Development Environment Protocol (Datastores Only)
Triggered whenever requested to prepare development environment for backend work ("prepare development environment [backend]"):
1. **Start Datastores & Message Brokers Only**: Spin up or retain only the stateful datastore dependencies matching production configurations:
   ```bash
   docker compose -f docker-compose.dev.yml up -d mongodb redis rabbitmq
   ```
2. **Stop Containerized Backend Microservices**: If containerized backend services (`gateway`, `user-service`, `notification-service`) are running, stop them to release host application ports:
   ```bash
   docker compose -f docker-compose.dev.yml stop gateway user-service notification-service
   ```
3. **Clone Production Seed Data**: Execute the *Production Data Cloning Protocol* to sync real production records into local MongoDB.
4. **Mandatory Health Verification**: Verify all datastore services report `Up (healthy)`:
   - MongoDB: Exposed on port `27017`
   - Redis: Exposed on port `6379`
   - RabbitMQ: AMQP on `5672`, Management UI on `15672`
5. **Backend Handoff**: Confirm application ports (`3000`, `3001`, `3002`, `3011`, `3012`) are unblocked and free, ready for the user to run backend microservices manually on the host (`npm run start:dev`).

### 2. Full Containerized Local Stack
Run all services and edge proxy locally in containerized networks:
```bash
docker compose up -d
docker compose ps
docker compose down -v
```

### 3. Staging Deployment
Deploy to isolated staging environment for automated CI testing and verification:
```bash
docker compose -p fullstack-staging --env-file .env.staging -f docker-compose.staging.yml up -d
docker compose -p fullstack-staging --env-file .env.staging -f docker-compose.staging.yml ps
docker compose -p fullstack-staging --env-file .env.staging -f docker-compose.staging.yml down -v
```

### 4. Production Deployment
Production execution using pre-built immutable images pulled from Docker Hub:
```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f
```

### 5. Production Observability Stack
Standalone monitoring stack (Prometheus, cAdvisor, Node Exporter, Grafana) attached to `fullstack-infrastructure_default`:
```bash
docker compose -f docker-compose.monitoring.yml up -d
docker compose -f docker-compose.monitoring.yml ps
docker compose -f docker-compose.monitoring.yml logs -f
```

## Useful Diagnostics
```bash
# Check service health status
docker inspect --format='{{json .State.Health}}' <container_name> | jq

# Validate compose syntax without running
docker compose -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.staging.yml config --quiet
docker compose -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.monitoring.yml config --quiet
```
