---
name: database-operations
description: "Use when executing MongoDB or Redis maintenance, initialization scripts, healthchecks, or volume management in the infrastructure project."
tier: local
target-stacks: ["mongodb", "redis", "docker"]
metadata:
  origin: auto-extracted
---

# Database Operations & Maintenance

**Extracted:** 2026-09-10  
**Context:** Operational procedures for managing MongoDB 7 and Redis 7 in the Dedisalam infrastructure.

## MongoDB 7 Operations
- **Databases Initialized**: `user_db` and `notification_db` via `docker/mongodb/mongo-init.js`.
- **Authentication**: Admin credentials supplied via `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD`.
- **Healthcheck Command**:
  ```bash
  mongosh --eval "db.runCommand('ping')"
  ```
- **Manual Shell Access**:
  ```bash
  docker exec -it mongodb mongosh -u root -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin
  ```

## Redis 7 Operations
- **Configuration**: Protected with `--requirepass ${REDIS_PASSWORD}`, max memory capped at 256MB with `--maxmemory-policy allkeys-lru`.
- **Healthcheck Command**:
  ```bash
  redis-cli -a $REDIS_PASSWORD ping
  ```
- **Key Inspection**:
  ```bash
  docker exec -it redis redis-cli -a $REDIS_PASSWORD INFO memory
  ```
