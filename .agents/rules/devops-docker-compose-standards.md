# DevOps Docker Compose Standards

**Context:** Docker Compose configuration and service lifecycle standards in the infrastructure repository.

## Compose Profile Architecture
Every service configuration must strictly belong to one of the 4 defined profiles:
- docker-compose.yml: Invariant base stack. Defines healthchecks, resource limits, and internal network boundaries.
- docker-compose.dev.yml: Local development overlay. Extends base stack to expose database, broker, and cache ports to localhost (27017, 5672, 15672, 6379).
- docker-compose.dev.server.yml: Development server (172.16.254.2). Must use -p fullstack-dev, pp-network-dev, <name>-dev container names, and dev_<name> volumes.
- docker-compose.prod.yml: Production stack. Must bind exclusively to private server IPs, enforce log rotation, and specify 
o-new-privileges:true.

## Directives
1. **No Obsolete Syntax**: Never include top-level ersion: in compose files (deprecated in Compose Specification / v2).
2. **Mandatory Healthchecks**: All stateful services (MongoDB, RabbitMQ, Redis, Nginx) must define automated healthchecks with interval: 30s, 	imeout: 10s, and 
etries: 3.
3. **Strict Startup Ordering**: Dependent services must use depends_on: <service>: condition: service_healthy, never raw condition: service_started.
4. **Resource Constraints**: Production and base services must define deploy.resources.limits (e.g., cpus: '1.0', memory: 512M) to avoid host starvation.
5. **Context Decoupling**: Application build contexts must use relative paths to component repositories (../backend, ../frontend).
