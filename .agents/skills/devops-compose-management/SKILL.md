---
name: devops-compose-management
description: "Use when starting, stopping, building, or deploying Docker Compose stacks across local development, staging, or production environments in the infrastructure project."
tier: local
target-stacks: ["docker", "docker-compose", "mongodb", "rabbitmq", "redis", "nginx"]
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

## Useful Diagnostics
```bash
# Check service health status
docker inspect --format='{{json .State.Health}}' <container_name> | jq

# Validate compose syntax without running
docker compose -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.staging.yml config --quiet
docker compose -f docker-compose.prod.yml config --quiet
```
