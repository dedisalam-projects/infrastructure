---
name: docker-container-observability
description: "Use when configuring, deploying, diagnosing, or querying container-level metrics, Prometheus alerting rules, cAdvisor, or Grafana dashboards across production or staging Docker stacks."
tier: local
target-stacks: ["docker", "cadvisor", "prometheus", "grafana", "node-exporter", "alerts"]
metadata:
  origin: auto-extracted
---

# Docker Container Observability & Alerting Stack

**Extracted:** 2026-09-14  
**Context:** Zero-instrumentation container monitoring, host metrics, broker leak detection, and automated alerting using Prometheus, cAdvisor, Node Exporter, and Grafana on Docker Compose infrastructure.

---

## Architecture & Principles

### 1. Zero-Instrumentation Container Discovery
Microservices and datastores (MongoDB, Redis, RabbitMQ, Nginx frontends) do not all have custom Prometheus exporters enabled by default. **cAdvisor** runs at the host Docker daemon level to dynamically discover and monitor **all active containers**:
- CPU usage cores (`rate(container_cpu_usage_seconds_total[1m])`)
- Memory working set bytes (`container_memory_working_set_bytes`)
- Restart crash loops (`increase(container_start_time_seconds[15m])`)
- Network and Disk I/O

### 2. Decoupled Lifecycle Compose Pattern
Monitoring services must NOT be placed inside the main application `docker-compose.prod.yml`. Placing them in a standalone `docker-compose.monitoring.yml` guarantees that:
- Application rolling deployments and restarts do not disrupt monitoring data collection or alert state history.
- The monitoring stack can be updated, restarted, or diagnosed independently.
- Connect to the application network via `external: true`:
  ```yaml
  networks:
    fullstack-infrastructure_default:
      external: true
  ```

---

## Critical Metric Gotchas & Lessons Learned

### Gotcha 1: Node Exporter Root Filesystem Mount Translation
When running `prom/node-exporter` with `--path.rootfs=/rootfs`, Node Exporter translates the mountpoint inside its metrics output back to `/`.
- **Incorrect Query**: `node_filesystem_avail_bytes{mountpoint="/rootfs"}` (Returns empty vector `[]`)
- **Correct Query**: `node_filesystem_avail_bytes{mountpoint="/"}` (Returns rootfs bytes)

### Gotcha 2: RabbitMQ Prometheus Exporter Metric Names
The native RabbitMQ Prometheus plugin (`rabbitmq_prometheus` on port `15692`) does not expose `rabbitmq_queues_total`:
- **Current Queue Count**: Use `rabbitmq_queues` (not `rabbitmq_queues_total`).
- **Ready Messages**: Use `sum(rabbitmq_queue_messages_ready)` (not `rabbitmq_messages_ready_total`).
- **Resident RAM**: Use `rabbitmq_process_resident_memory_bytes`.

### Gotcha 3: Scoping `up == 0` Alert Rules
Do not use a bare `up == 0` rule if some application microservices in the scrape pool do not yet expose `/metrics`. This causes permanent false-alarm firing.
- **Correct Pattern**: Explicitly filter to active infrastructure jobs:
  ```yaml
  expr: up{job=~"cadvisor|node-exporter|rabbitmq|prometheus"} == 0
  ```

---

## Production Prometheus Alert Rules Template

Add to `/etc/prometheus/alerts.yml`:

```yaml
groups:
  - name: InfrastructureCoreAlerts
    rules:
      # 1. Critical Infrastructure Service Down
      - alert: ServiceInstanceDown
        expr: up{job=~"cadvisor|node-exporter|rabbitmq|prometheus"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service instance {{ $labels.instance }} is down"
          description: "Target {{ $labels.instance }} of job {{ $labels.job }} has been unreachable for > 1m."

      # 2. Container Memory Approaching Limit (Warning)
      - alert: ContainerMemoryApproachingLimit
        expr: (container_memory_working_set_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""}) > 0.80 and container_spec_memory_limit_bytes{name!=""} > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} memory usage > 80%"
          description: "Container {{ $labels.name }} is using > 80% of its memory limit. Risk of OOM-Kill."

      # 3. Container Memory Critical (Imminent OOM)
      - alert: ContainerMemoryCritical
        expr: (container_memory_working_set_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""}) > 0.90 and container_spec_memory_limit_bytes{name!=""} > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CRITICAL: Container {{ $labels.name }} memory usage > 90%"
          description: "Container {{ $labels.name }} memory usage > 90%. Immediate OOM-Kill imminent."

      # 4. Crash-Restart Loop Detection
      - alert: ContainerRestartLoop
        expr: increase(container_start_time_seconds{name!=""}[15m]) > 2
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} crash-restart loop"
          description: "Container {{ $labels.name }} has restarted > 2 times in the last 15 minutes."

      # 5. RabbitMQ / Message Broker Queue Spike (RPC / Healthcheck Leak)
      - alert: RabbitMQQueueSpike
        expr: rabbitmq_queues > 50
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "RabbitMQ ghost queue leak detected (total: {{ $value }})"
          description: "Total RabbitMQ queues count reached {{ $value }} (threshold: 50). Probable uncollected RPC/healthcheck queue leak."

      # 6. Host Root Disk Low
      - alert: HostDiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Host filesystem free disk space < 15%"
          description: "ThinkCentre host root filesystem free space is below 15%."
```

---

## Grafana REST API & Service Account Authentication

### 1. Windows Environment Credential Resolution
Never hardcode Grafana tokens or credentials in repository files. Store them in persistent Windows User Environment variables (`HKCU:\Environment`) and resolve dynamically in scripts:

```powershell
# Auto-load persistent User environment credentials into session if missing
if (-not $env:GRAFANA_API_TOKEN) {
    $env:GRAFANA_API_TOKEN = (Get-ItemProperty -Path 'HKCU:\Environment').GRAFANA_API_TOKEN
    $env:GRAFANA_URL = (Get-ItemProperty -Path 'HKCU:\Environment').GRAFANA_URL
}
```

### 2. Service Account Bearer Authentication
Grafana Service Account tokens (`glsa_*`) authenticate via standard HTTP `Authorization: Bearer` header:

```bash
# Verify organization identity
curl.exe -s -H "Authorization: Bearer $env:GRAFANA_API_TOKEN" "$env:GRAFANA_URL/api/org"

# Search all dashboards
curl.exe -s -H "Authorization: Bearer $env:GRAFANA_API_TOKEN" "$env:GRAFANA_URL/api/search"

# Query specific dashboard by UID
curl.exe -s -H "Authorization: Bearer $env:GRAFANA_API_TOKEN" "$env:GRAFANA_URL/api/dashboards/uid/infra-prod-all"
```

---

## Verification & Diagnostic Commands

```bash
# Count total containers monitored by cAdvisor
curl -s "http://localhost:9090/api/v1/query?query=count(container_last_seen{name!=''})"

# Top 5 containers by RAM consumption
curl -s "http://localhost:9090/api/v1/query?query=topk(5,container_memory_working_set_bytes{name!=''})"

# Verify all Prometheus active scrape targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check active alert rules evaluation status
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert: .name, state: .state}'

# Validate alert rules file syntax using promtool in Docker
docker run --rm -v "${PWD}/docker/prometheus:/etc/prometheus" --entrypoint promtool prom/prometheus:v2.51.0 check rules /etc/prometheus/alerts.yml
```
