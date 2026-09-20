---
name: microfrontend-isolated-docker-containers
description: "Use when containerizing Angular micro-frontends with Docker, or when routing multiple subdomains via Cloudflare Zero Trust tunnels — isolate each micro-frontend into its own independent Docker image, Nginx container, and standard port 8080 (nginx-unprivileged)."
tier: local
target-stacks: ["angular", "docker", "nginx", "cloudflare", "jenkins"]
metadata:
  origin: auto-extracted
---

# Isolated Docker Containers for Micro-Frontends (Standard Port 8080) & Cloudflare Zero Trust

**Extracted:** 2026-09-13  
**Context:** Production containerization of Angular multi-project workspaces (`landing`, `auth`, `dashboard`) deployed behind Cloudflare Zero Trust (`cloudflared`) tunnels using standard unprivileged Nginx port `8080`.

> [!CAUTION]
> **Safety Guardrail**: Modifying Docker container ingress, ports, or image builds directly affects production web traffic. Always confirm container configurations and obtain approval before applying container changes to production.

## Problem

When multiple Angular micro-frontends share a single monolithic Docker image or a single Nginx web container:
1. **Asset Collision:** Overwriting build directories (e.g., `dist/dashboard/browser` vs `dist/auth/browser` both copied to `/usr/share/nginx/html`) causes missing chunks, bundle collisions, and 404 errors.
2. **Cloudflare Zero Trust Ingress Confusion:** Cloudflare Tunnel (`cloudflared`) routes traffic based on public hostnames (`auth.dedisalam.my.id`, `dash.dedisalam.my.id`, `dedisalam.my.id`). If routed to a single container on a single port, Nginx must perform complex virtual host demultiplexing, which breaks with SSL termination, headers, and reverse-proxy caching.
3. **Port Inconsistency:** Using arbitrary port numbers across micro-frontends creates cognitive overload and deployment configuration drift.

## Solution Architecture

Each Angular sub-project is containerized into its own dedicated Docker image and standalone container. Because each container runs in its own network namespace, every container standardizes uniformly on **standard port `8080`** (aligned with `nginxinc/nginx-unprivileged`).

### 1. Container Topology & Ingress Mapping

| Micro-frontend | Production Subdomain | Internal Container Service | Internal Port | Docker Image |
|---|---|---|---|---|
| **Landing** | `dedisalam.my.id` | `frontend-landing` | `8080` | `dedisalam/frontend-landing:latest` |
| **Auth** | `auth.dedisalam.my.id` | `frontend-auth` | `8080` | `dedisalam/frontend-auth:latest` |
| **Dashboard** | `dash.dedisalam.my.id` | `frontend-dashboard` | `8080` | `dedisalam/frontend-dashboard:latest` |

---

### 2. Multi-Stage Dockerfile per Sub-Project (Standard Port 8080)

Organize Dockerfiles under `docker/<project>/Dockerfile.prod`:

#### Example: `docker/landing/Dockerfile.prod`
```dockerfile
# Stage 1: Build library & target project
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
COPY . .
RUN npm run build:shared-ui && npm run build:landing

# Stage 2: Production Nginx container
FROM nginxinc/nginx-unprivileged:1.25-alpine AS production
COPY docker/landing/nginx.prod.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist/landing/browser /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

#### Example: `docker/landing/nginx.prod.conf`
```nginx
server {
    listen 8080;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(?:css|js|jpg|jpeg|gif|png|ico|cur|gz|svg|svgz|mp4|ogg|ogv|webm|htc|woff|woff2)$ {
        expires 1y;
        access_log off;
        add_header Cache-Control "public, no-transform";
    }
}
```

> **Note:** Apply the identical pattern for `docker/auth/` and `docker/dashboard/`. All containers expose and listen on port `8080`.

---

### 3. Cloudflare Zero Trust (`cloudflared`) Ingress Contract

In `infrastructure/docker/cloudflared/config.yml`:

```yaml
tunnel: <tunnel-uuid>
credentials-file: /etc/cloudflared/creds.json

ingress:
  # Landing Page (Standard 8080)
  - hostname: dedisalam.my.id
    service: http://frontend-landing:8080
    
  # Auth / Login Portal (Standard 8080)
  - hostname: auth.dedisalam.my.id
    service: http://frontend-auth:8080
    
  # Admin Dashboard (Standard 8080)
  - hostname: dash.dedisalam.my.id
    service: http://frontend-dashboard:8080
    
  # Backend API Gateway
  - hostname: api.dedisalam.my.id
    service: http://backend-gateway:3000

  - service: http_status:404
```

---

### 4. Jenkins Pipeline Multi-Image Build & Dual-Tagging

Update the `Build & Push Docker Image` stage in `Jenkinsfile` to build all 3 images with SemVer dual-tagging:

```groovy
stage('Build & Push Docker Images') {
    steps {
        script {
            def semver = sh(script: 'git describe --tags --exact-match 2>/dev/null || echo "v1.0.${BUILD_NUMBER}"', returnStdout: true).trim()
            env.RELEASE_TAG = semver
        }
        sh '''
            # Build and Push Landing (Port 8080)
            docker build -t dedisalam/frontend-landing:${RELEASE_TAG} -t dedisalam/frontend-landing:latest -f docker/landing/Dockerfile.prod .
            docker push dedisalam/frontend-landing:${RELEASE_TAG}
            docker push dedisalam/frontend-landing:latest

            # Build and Push Auth (Port 8080)
            docker build -t dedisalam/frontend-auth:${RELEASE_TAG} -t dedisalam/frontend-auth:latest -f docker/auth/Dockerfile.prod .
            docker push dedisalam/frontend-auth:${RELEASE_TAG}
            docker push dedisalam/frontend-auth:latest

            # Build and Push Dashboard (Port 8080)
            docker build -t dedisalam/frontend-dashboard:${RELEASE_TAG} -t dedisalam/frontend-dashboard:latest -f docker/dashboard/Dockerfile.prod .
            docker push dedisalam/frontend-dashboard:${RELEASE_TAG}
            docker push dedisalam/frontend-dashboard:latest
        '''
    }
}
```

---

### 5. Infrastructure Docker Compose (`docker-compose.prod.yml`)

```yaml
  frontend-landing:
    image: dedisalam/frontend-landing:latest
    container_name: frontend-landing
    restart: unless-stopped
    expose:
      - "8080"
    networks:
      - fullstack-net

  frontend-auth:
    image: dedisalam/frontend-auth:latest
    container_name: frontend-auth
    restart: unless-stopped
    expose:
      - "8080"
    networks:
      - fullstack-net

  frontend-dashboard:
    image: dedisalam/frontend-dashboard:latest
    container_name: frontend-dashboard
    restart: unless-stopped
    expose:
      - "8080"
    networks:
      - fullstack-net
```

## When to Use

1. When deploying an Angular multi-project workspace where each sub-project maps to a distinct subdomain (`dedisalam.my.id`, `auth.dedisalam.my.id`, `dash.dedisalam.my.id`).
2. When configuring Cloudflare Zero Trust tunnels (`cloudflared`) to forward hostnames cleanly to internal Docker services using uniform standard port `8080`.
3. When avoiding asset collisions and preventing monolith container failure across micro-frontends.


> [!IMPORTANT]
> **Rule Adherence**: Always strictly follow the `microfrontend-isolated-docker-containers` conventions outlined above to ensure workspace consistency and prevent regressions.
