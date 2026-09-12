---
name: jenkins-pipeline-audit
description: "Use when auditing Jenkins declarative pipelines, validating Jenkinsfile stage healthchecks for false-green suppression, or diagnosing remote Jenkins job configuration and build history drift"
tier: local
target-stacks: ["jenkins", "groovy", "pipeline", "ci-cd", "bash", "powershell", "docker-compose"]
metadata:
  origin: auto-extracted
---

# Jenkins Pipeline & Continuous Deployment Audit

**Extracted:** 2026-09-12  
**Context:** Auditing Jenkins declarative pipelines (`Jenkinsfile`), job XML definitions, and remote build executions to eliminate false-green builds, parameter drift, credential desynchronization, and silent deployment failures.

---

## Problem

1. **False-Green Builds**: Pipeline stages masking runtime failures with `|| true`, unhandled exit codes, or non-blocking health checks, marking Jenkins builds as `SUCCESS` even when services fail to start or crash immediately.
2. **Health Check Timing Flaws**: Checking endpoints immediately after `docker compose up -d` with a single probe instead of an active polling retry loop, causing either false failures during warm-up or false positives due to premature check bypass.
3. **Parameter Drift & Partial Deployments**: Pipeline parameters defaulting to selective microservices (e.g. `SERVICES="gateway user-service"`) with `--no-deps`. When automated triggers (webhooks, upstream builds) run without parameters, persistent datastores and networks are bypassed, causing credential and network drift.
4. **Secret Lifecycle & Leak Risks**: Injected secrets (`.env`) left lingering in workspace directories when post-actions fail, or leaked into console output during debugging.
5. **Remote Job Drift**: Job configuration in remote Jenkins drifting out of sync with repository SCM definitions (`jenkins/job-config.xml`).

---

## Audit Checklist & Patterns

### 1. Static Pipeline Code Audit (`Jenkinsfile`)

Inspect `Jenkinsfile` for the following anti-patterns:

| Check | Anti-Pattern | Correct Pattern |
|---|---|---|
| **Error Suppression** | `wget ... \|\| true`<br>`curl ... \|\| true` | Fail-fast: remove `\|\| true` and evaluate explicit exit status. |
| **Healthcheck Loop** | Single probe after `sleep 10` | 15–20 iteration polling loop with 2s sleep interval; verify HTTP 200/healthy status. |
| **Diagnostic Dump** | Exiting failure with no logs | Dump `docker compose ps` and `docker compose logs --tail 50 <services>` before `exit 1`. |
| **Parameter Default** | `defaultValue: 'gateway ...'` with `--no-deps` | `defaultValue: 'all'` so automated webhooks synchronize datastores & network. |
| **Secret Purge** | `sh 'rm -f .env'` in `success {}` only | Place secret cleanup inside `post { always { sh 'rm -f .env \|\| true' } }`. |
| **Image Pull Resilience** | Unhandled pull error on local/private images | Use `pull --ignore-pull-failures` and set `pull_policy: missing` in Compose. |

### 2. Automated Static Audit Script

Run this PowerShell command to audit local `Jenkinsfile` and `docker-compose.prod.yml`:

```powershell
# 1. Check for false-green error suppression in pipeline
$falseGreens = Select-String -Path "Jenkinsfile" -Pattern "(\|\|\s*true|exit\s+0)"
if ($falseGreens) {
    Write-Warning "Potential False-Green detected in Jenkinsfile:"
    $falseGreens | ForEach-Object { Write-Host "  Line $($_.LineNumber): $($_.Line.Trim())" -ForegroundColor Yellow }
} else {
    Write-Host "[PASS] No false-green suppression found." -ForegroundColor Green
}

# 2. Check SERVICES parameter default
$servicesParam = Select-String -Path "Jenkinsfile" -Pattern "name:\s*'SERVICES'.*defaultValue:\s*'([^']+)'"
if ($servicesParam -and $servicesParam.Matches.Groups[1].Value -ne 'all') {
    Write-Warning "SERVICES parameter does not default to 'all' (found: '$($servicesParam.Matches.Groups[1].Value)')"
} else {
    Write-Host "[PASS] SERVICES defaults to 'all' for full stack synchronization." -ForegroundColor Green
}

# 3. Check secret purge in post { always }
$content = Get-Content "Jenkinsfile" -Raw
if ($content -match "post\s*\{[\s\S]*?always") {
    Write-Host "[PASS] Secret purge verified in post always block." -ForegroundColor Green
} else {
    Write-Warning "Jenkinsfile does not guarantee secret cleanup in 'post { always }'."
}
```

### 3. Remote Jenkins Job & Build Health Audit via REST API

Execute remote audit against Jenkins host using machine-stored credentials:

```powershell
$u = if ($env:JENKINS_USER) { $env:JENKINS_USER } else { [Environment]::GetEnvironmentVariable("JENKINS_USER", "User") }
$t = if ($env:JENKINS_API_TOKEN) { $env:JENKINS_API_TOKEN } else { [Environment]::GetEnvironmentVariable("JENKINS_API_TOKEN", "User") }
$url = if ($env:JENKINS_LOCAL_URL) { $env:JENKINS_LOCAL_URL } else { [Environment]::GetEnvironmentVariable("JENKINS_LOCAL_URL", "User") }
if (-not $url) { $url = "http://172.16.254.2:8080" }

# A. Audit Job SCM & Parameter Configuration
$jobInfo = curl.exe -s -u "$($u):$($t)" "$url/job/fullstack-infrastructure/api/json" | ConvertFrom-Json
Write-Host "Job Name: $($jobInfo.name)"
Write-Host "Color/Health: $($jobInfo.color)"

# B. Audit Last Build Status & Execution Details
$lastBuild = curl.exe -s -u "$($u):$($t)" "$url/job/fullstack-infrastructure/lastBuild/api/json" | ConvertFrom-Json
Write-Host "Last Build Number: #$($lastBuild.number)"
Write-Host "Result: $($lastBuild.result)"
Write-Host "Duration: $([math]::Round($lastBuild.duration / 1000, 1))s"

# C. Inspect Console Tail for Suppressed Errors
$consoleTail = curl.exe -s -u "$($u):$($t)" "$url/job/fullstack-infrastructure/lastBuild/consoleText" | Select-Object -Last 40
if ($consoleTail -match "Connection refused|Authentication failed|WRONGPASS|error|fatal") {
    Write-Warning "Detected suspicious error patterns in last build console output!"
}
```

### 4. Live Production Container Health Cross-Verification

Always cross-verify Jenkins `SUCCESS` status with actual container runtime health on the deployment host:

```powershell
# Query runtime container status via remote Docker context
docker.exe --context prod-server ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Networks}}"

# Verify internal services have zero external port exposure
@(27017, 6379, 5672, 3011, 3012) | ForEach-Object {
    $port = $_
    $res = Test-NetConnection -ComputerName 172.16.254.2 -Port $port -WarningAction SilentlyContinue
    if ($res.TcpTestSucceeded) {
        Write-Error "CRITICAL: Internal port $port is exposed on host interface!"
    } else {
        Write-Host "[SECURE] Port $port is closed to external host." -ForegroundColor Green
    }
}
```

---

## When to Use

- When reviewing or authoring changes to `Jenkinsfile` or `jenkins/job-config.xml`.
- When diagnosing a deployment pipeline that reports `SUCCESS` while production containers report `unhealthy` or crash.
- When validating that automated webhook triggers synchronize datastores, networks, and secrets without manual parameter intervention.
- Before merging PRs modifying CI/CD orchestration, healthcheck probe routes, or secret injection stages.
