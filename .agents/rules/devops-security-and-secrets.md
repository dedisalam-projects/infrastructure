# DevOps Security and Secrets Management

**Context:** Security boundaries, credential injection, and isolation standards for infrastructure services.

## Zero Trust Directives
1. **Zero Hardcoded Secrets**: Never commit passwords, keys, or tokens in YAML files. All secrets must use environment variable interpolation (e.g., ${MONGO_INITDB_ROOT_PASSWORD}, ${REDIS_PASSWORD}).
2. **Unprivileged Execution**: Run edge proxy and container processes without root privileges (e.g., 
ginxinc/nginx-unprivileged:1.25-alpine, USER node).
3. **Read-Only Volume Mounts**: Configuration files, scripts, and certificates must be mounted as read-only (:ro), e.g., ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro.
4. **Privilege Escalation Prevention**: Production containers must specify security_opt: - no-new-privileges:true.
5. **Network Segregation**:
   - Local dev traffic stays on ackend_network bridge.
   - Server dev traffic stays on isolated pp-network-dev.
   - External public traffic routes exclusively through Cloudflare ingress network where configured.
