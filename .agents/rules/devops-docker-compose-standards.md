# DevOps Docker Compose Standards

**Context:** Docker Compose configuration and service lifecycle standards in the infrastructure repository.

## Compose Profile Architecture
Every service configuration must strictly belong to one of the defined environment profiles:
- `docker-compose.yml`: Invariant base stack. Defines healthchecks, resource limits, and internal network boundaries.
- `docker-compose.dev.yml`: Local development overlay (strictly local PC). Extends base stack to expose database, broker, and cache ports to localhost (27017, 5672, 15672, 6379).
- `docker-compose.staging.yml`: Staging stack. Uses `-p fullstack-staging` with dedicated isolated ports (27018, 5673, 15673, 6380, 3005) for CI test suites.
- `docker-compose.prod.yml`: Production stack. Must bind exclusively to private server IPs, enforce log rotation, and specify `no-new-privileges: true`.

## Directives
1. **Strict Local-Only Development**: Development stacks and exposed dev ports are strictly forbidden on remote servers (172.16.254.2). Remote hosts are exclusively dedicated to Staging and Production environments.
2. **No Obsolete Syntax**: Never include top-level `version:` in compose files (deprecated in Compose Specification / v2).
3. **Mandatory Healthchecks**: All stateful services (MongoDB, RabbitMQ, Redis, Nginx) must define automated healthchecks with `interval: 30s`, `timeout: 10s`, and `retries: 3`.
4. **Strict Startup Ordering**: Dependent services must use `depends_on: <service>: condition: service_healthy`, never raw `condition: service_started`.
5. **Resource Constraints**: Production and base services must define `deploy.resources.limits` (e.g., `cpus: '1.0'`, `memory: 512M`) to avoid host starvation.
6. **Context Decoupling**: Application build contexts must use relative paths to component repositories (`../backend`, `../frontend`).
