---
name: nginx-edge-proxy
description: "Use when configuring, debugging, or updating Nginx reverse proxy routes, SSL certificates, WebSocket upgrades, or security headers in the infrastructure project."
tier: local
target-stacks: ["nginx", "docker", "ssl"]
metadata:
  origin: auto-extracted
---

# Nginx Edge Proxy

**Extracted:** 2026-09-10  
**Context:** Reverse proxy routing, SSL termination, and security headers for the Dedisalam edge layer.

> [!CAUTION]
> **Safety Guardrail**: Updating reverse proxy routing or TLS certificates can disrupt live network connections. Always request confirmation and approval before reloading Nginx or altering proxy configurations.

## Architecture
Nginx runs unprivileged using image `nginxinc/nginx-unprivileged:1.25-alpine`:
- Port `8080` mapped to host `80`
- Port `8443` mapped to host `443`

## Routing Rules
- `/api/` -> Passes to `http://gateway:3000`
- `/socket.io/` -> Passes to `http://gateway:3000` with WebSocket upgrade (`Upgrade $http_upgrade`, `Connection "upgrade"`)
- `/rabbitmq/` -> Passes to `http://rabbitmq:15672/` management UI
- `/` -> Passes to frontend web application (`http://web:4200`)
- `/health` -> Internal healthcheck returning `200 'OK'` with `access_log off`

## Mandatory Security Headers
Every Nginx server block must include:
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'" always;
proxy_set_header X-Correlation-ID $request_id;
```

## Configuration Testing
```bash
# Test Nginx syntax inside running container
docker exec -it nginx nginx -t

# Reload configuration without downtime
docker exec -it nginx nginx -s reload
```
