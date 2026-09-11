# DevOps Observability Standards

**Context:** Logging, metrics scraping, dashboard provisioning, and health monitoring for all infrastructure services.

## Metrics & Scraping Directives
1. **Prometheus Target Naming**: Service job names in docker/prometheus/prometheus.yml must match 
estjs-<app-name> with scrape target <container-name>:<port>.
2. **Scrape Intervals**: Maintain a unified 15s global scrape_interval and evaluation_interval.
3. **Alert Rule Files**: Store alerting rules in declarative YAML format (docker/prometheus/alerts.yml).

## Dashboards & Provisioning
1. **Declarative Provisioning**: Grafana dashboards and datasources must be stored in docker/grafana/provisioning/ and loaded automatically on container startup.
2. **Zero Manual Setup**: Never require manual dashboard import or data source configuration through the Grafana UI.

## Log Management
1. **Log Rotation**: In production, container log drivers must specify json-file with max-size: 10m and max-file: 3 to prevent disk saturation.
2. **Healthcheck Probes**: Health probes must hit lightweight /health endpoints with logging disabled (ccess_log off in Nginx) to eliminate log pollution.
