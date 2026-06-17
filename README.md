# Managed Service Infra Orchestration

This repository contains a multi-service system to orchestrate build and deployment flows for frontend projects.

## Project Structure

- `apiServer/` — FastAPI service that accepts project requests, triggers build tasks, and streams logs.
- `buildServer/` — build worker service that installs dependencies, builds project output, and uploads artifacts to S3.
- `reverseProxyServer/` — FastAPI reverse proxy for serving built artifacts by subdomain/path routing.
- `frontend/` — Vite + React UI for submitting deployments and viewing logs/results.

## High-Level Flow

1. A deployment request is submitted through the frontend/API.
2. The API server starts a build task with project metadata.
3. The build server builds artifacts and uploads output to S3.
4. Build logs are published via Redis and streamed back to clients.
5. The reverse proxy serves generated artifacts from S3 paths.

## Local Development

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Architecture Design

> TODO: Add architecture diagram and detailed architecture design here.
