# Dedisalam Infrastructure & DevOps

This directory contains the infrastructure, datastores, message brokers, reverse proxies, and deployment configurations for the Dedisalam platform, maintained by the DevOps team.

## Overview

`
infrastructure/
├── docker/
│   ├── grafana/           # Grafana dashboards and provisioning
│   ├── mongodb/           # MongoDB initialization scripts
│   ├── nginx/             # Nginx reverse proxy and SSL certificates
│   └── prometheus/        # Prometheus scrape configurations and alerts
├── docker-compose.yml     # Base container stack definition
├── docker-compose.dev.yml # Local development overlay (exposing ports to host)
├── docker-compose.dev.server.yml # Development server deployment (172.16.254.2)
└── docker-compose.prod.yml       # Production deployment configuration
`

## Services Managed

| Service | Technology | Internal Port | Host Port (Dev) | Description |
|---|---|---|---|---|
| **MongoDB** | mongo:7 | 27017 | 27017 | Primary datastore (user_db, 
otification_db) |
| **RabbitMQ** | 
abbitmq:3.13-management-alpine | 5672, 15672 | 5672, 15672 | Asynchronous message broker & management console |
| **Redis** | 
edis:7-alpine | 6379 | 6379 | Session cache and refresh token storage |
| **Nginx** | 
ginxinc/nginx-unprivileged:1.25-alpine | 8080, 8443 | 80, 443 | Edge reverse proxy & SSL termination |
| **Prometheus** | prom/prometheus:latest | 9090 | - | Metrics collection and alerts |
| **Grafana** | grafana/grafana:latest | 3000 | 3005 | Metrics visualization dashboards |

## Common Commands

### 1. Local Development Infrastructure
Start databases and brokers for local development (services exposed on localhost):
`ash
docker compose -f docker-compose.dev.yml up -d
`

Stop infrastructure:
`ash
docker compose -f docker-compose.dev.yml down
`

View infrastructure logs:
`ash
docker compose -f docker-compose.dev.yml logs -f
`

### 2. Development Server Deployment (172.16.254.2)
`ash
ssh dedisalam@172.16.254.2
cd /path/to/infrastructure
docker compose -p fullstack-dev -f docker-compose.dev.server.yml up -d --build
`

### 3. Production Deployment
`ash
docker compose -f docker-compose.prod.yml up -d
`
