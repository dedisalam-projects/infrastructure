---
name: devops-compose-management
description: "Use when starting, stopping, building, or deploying Docker Compose stacks across local, dev server, or production environments in the infrastructure project."
tier: local
target-stacks: ["docker", "docker-compose", "mongodb", "rabbitmq", "redis", "nginx"]
metadata:
  origin: auto-extracted
---

# DevOps Compose Management

**Extracted:** 2026-09-10  
**Context:** Multi-environment Docker Compose lifecycle management for the Dedisalam platform infrastructure.

## Compose Profiles Reference

### 1. Local Development Stack
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

### 3. Development Server Deployment (172.16.254.2)
Deploy to isolated development server:
```bash
ssh dedisalam@172.16.254.2
cd /path/to/infrastructure
docker compose -p fullstack-dev -f docker-compose.dev.server.yml up -d --build
docker compose -p fullstack-dev -f docker-compose.dev.server.yml logs -f
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
docker compose -f docker-compose.dev.server.yml config --quiet
docker compose -f docker-compose.prod.yml config --quiet
```
