---
name: jenkins-pre-authenticated-docker
description: "Use when configuring docker push steps in a Jenkinsfile, or when a user explicitly states the host is already authenticated — rely on host Docker daemon auth instead of Jenkins credentials to prevent pipeline crashes."
tier: parent
target-stacks: ["jenkins", "docker", "bash"]
metadata:
  origin: auto-extracted
---

# Jenkins Pre-Authenticated Docker Pattern

**Extracted:** 2026-09-20
**Context:** When setting up a Jenkins pipeline (Jenkinsfile) that builds and pushes Docker images, and the user has already executed `docker login` manually on the Jenkins host.

## Problem
When an AI assistant tries to "harden" a CI/CD pipeline, it often assumes it needs to securely inject registry credentials using Jenkins `withCredentials`. However, if the Jenkins host is already manually authenticated with Docker, adding a `withCredentials` block with an undeclared `credentialsId` (e.g., `docker-hub-credentials`) will cause an instant pipeline crash: `ERROR: Could not find credentials entry with ID...`.

## Solution
When a host is pre-authenticated, **do not** inject `withCredentials` blocks or explicit `docker login` commands. Simply run `docker push` directly within the `sh` block. It will natively inherit the host daemon's authenticated session (from `~/.docker/config.json`).

```groovy
// DO NOT do this if the host is pre-authenticated (will crash if ID is missing):
withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
    sh '''
        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
        docker push my-repo/my-image:latest
    '''
}

// DO this instead (relies on host auth):
sh '''
    echo 'Pushing Docker images to Docker Hub registry...'
    docker push my-repo/my-image:latest
'''
```

## When to Use
- When the user explicitly states they have already logged into Docker manually ("saya sudah perintahkan docker login").
- When modifying an existing Jenkinsfile that already uses `docker push` without explicit credentials. Do not "fix" it by adding credentials unless explicitly asked.
