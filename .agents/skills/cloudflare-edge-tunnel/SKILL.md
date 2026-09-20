---
name: cloudflare-edge-tunnel
description: "Use when configuring, managing, or diagnosing Cloudflare Tunnels (cloudflared), Zero Trust dashboard ingress routes, DNS records, or R2 S3-compatible object storage"
tier: local
target-stacks: ["cloudflare", "cloudflared", "zero-trust", "docker-compose", "bash", "powershell", "s3", "r2"]
metadata:
  origin: auto-extracted
---

# Cloudflare Edge Tunnel & Zero Trust Orchestration

**Extracted:** 2026-09-12  
**Context:** Managing Cloudflare Tunnels (`cloudflared`), Zero Trust web ingress routing, remote host bridge networking, and S3-compatible R2 storage for dedicated infrastructure (`dedisalam.my.id`).

> [!CAUTION]
> **Safety Guardrail**: Modifying DNS routing, ingress tunnels, or Zero Trust access policies directly impacts public network accessibility. Always request user confirmation and approval before updating routing rules or altering edge configurations.

---

## Problem

1. **Secure Ingress Without Port Forwarding**: Exposing local services (Jenkins, Nginx, n8n) to the internet without opening router ports, exposing public IPs, or managing manual dynamic DNS.
2. **Docker Bridge Ingress Connectivity**: A `cloudflared` container must reach host-bound services (like Jenkins on `localhost:8080`) without networking collisions.
3. **Programmatic Route Management**: Managing public hostnames and ingress rules via Cloudflare REST API without relying entirely on manual web clicks.
4. **Secret Protection**: Preventing Cloudflare API tokens, Tunnel run tokens, and R2 S3 secret keys from being leaked in repository files.

---

## Architecture & Topology

```
Internet Requests (*.dedisalam.my.id)
            │
            ▼
   Cloudflare Edge (Anycast / SSL termination)
            │
    (Encrypted QUIC / HTTP2 Tunnel)
            │
            ▼
 ThinkCentre Host (172.16.254.2)
   └─ Container: cloudflared (172.19.0.4 on 'cloudflare' network)
            ├── jenkins.dedisalam.my.id  ──> http://172.19.0.1:8080 (Jenkins Host)
            ├── dedisalam.my.id          ──> http://nginx:80 (Production Proxy)
            └── n8n.dedisalam.my.id      ──> http://n8n:5678 (n8n Service)
```

---

## Dashboard Navigation Quick Reference

| Component | Dashboard URL | Key Function |
|---|---|---|
| **Account Overview** | `https://dash.cloudflare.com/<CF_ACCOUNT_ID>` | Zone & DNS overview |
| **Zero Trust Console** | `https://one.dash.cloudflare.com/<CF_ACCOUNT_ID>` | Access policies & WARP settings |
| **Tunnel Management** | `https://one.dash.cloudflare.com/<CF_ACCOUNT_ID>/networks/tunnels` | Inspect active connections & health |
| **Specific Tunnel** | `https://one.dash.cloudflare.com/<CF_ACCOUNT_ID>/networks/tunnels/<TUNNEL_ID>` | Add/edit Public Hostname ingress rules |
| **R2 Object Storage** | `https://dash.cloudflare.com/<CF_ACCOUNT_ID>/r2/default/overview` | Bucket management & S3 credentials |

---

## REST API Operations (Automated Management)

Store credentials in persistent User environment variables:
- `CF_ACCOUNT_ID`
- `CF_API_TOKEN`

### 1. Verify Token & Account Scope
```powershell
$acc = [Environment]::GetEnvironmentVariable("CF_ACCOUNT_ID", "User")
$token = [Environment]::GetEnvironmentVariable("CF_API_TOKEN", "User")

curl.exe -s -X GET "https://api.cloudflare.com/client/v4/accounts/$acc/tokens/verify" `
    -H "Authorization: Bearer $token"
```

### 2. Inspect Tunnel Health & Ingress Configurations
```powershell
# Query all tunnels
curl.exe -s -X GET "https://api.cloudflare.com/client/v4/accounts/$acc/cfd_tunnel" `
    -H "Authorization: Bearer $token"

# Query active ingress configuration
curl.exe -s -X GET "https://api.cloudflare.com/client/v4/accounts/$acc/cfd_tunnel/<TUNNEL_ID>/configurations" `
    -H "Authorization: Bearer $token"
```

### 3. Host-Gateway Ingress Pattern in Docker
When routing a public hostname to a service running directly on the Docker host (such as Jenkins on port 8080):
- **Do not** use `http://localhost:8080` inside the container.
- Route to the Docker bridge gateway interface: `http://172.19.0.1:8080` (or `http://host.docker.internal:8080`).

### 4. Zero Trust Dual-Homed Container Network Pattern (Direct Service Discovery)
Rather than routing containerized services through the host bridge (`172.19.0.1:<PORT>`), edge-facing containers (`gateway`, `nginx`) should join the external `cloudflare` network directly:

```yaml
services:
  gateway:
    networks:
      - default     # Internal communication with datastores & microservices
      - cloudflare  # Direct internal resolution by cloudflared

  nginx:
    networks:
      - default
      - cloudflare

networks:
  default:
    name: fullstack-infrastructure_default
  cloudflare:
    name: cloudflare
    external: true
```

**Ingress Target:** In the Cloudflare Tunnel ingress configuration, target containers directly by internal Docker DNS name:
- `api.dedisalam.my.id`  ──> `http://gateway:3000`
- `dedisalam.my.id`      ──> `http://nginx:8080`

This eliminates dependence on host port exposures and provides pure internal Zero Trust isolation.

---

## R2 S3 Storage Configuration

Connect using standard S3 client credentials:
- **Endpoint**: `https://<CF_ACCOUNT_ID>.r2.cloudflarestorage.com`
- **Region**: `auto`
- **Access Key ID**: `<R2_ACCESS_KEY_ID>`
- **Secret Access Key**: `<R2_SECRET_ACCESS_KEY>`

---

## When to Use

- When diagnosing external accessibility issues for `jenkins.dedisalam.my.id`, `dedisalam.my.id`, or `n8n.dedisalam.my.id`.
- When adding new public hostnames or routing new microservice endpoints through Cloudflare Tunnel.
- When configuring object storage backups for MongoDB, Jenkins build artifacts, or uploads using Cloudflare R2.
- When inspecting edge connectivity health and connection logs for the `ThinkCentre` tunnel.
