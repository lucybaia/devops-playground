# DevStation — DevOps Playground

A personal learning project covering a full DevOps toolchain, end to end, in a single repository.

The application itself is a small FastAPI service (a snippet manager) — the real focus of this repo is everything built around it: containerization, CI, Kubernetes, GitOps, observability, infrastructure as code, and configuration management.

## What's implemented

| Phase | Tooling | Status |
|---|---|---|
| 1 — Containers | Docker, Docker Compose (multi-stage builds, health checks, volumes) | ✅ |
| 2 — CI | GitHub Actions (ruff lint + pytest) | ✅ |
| 3 — Orchestration | Kubernetes via kind (Deployments, Services, kubectl) | ✅ |
| 4 — GitOps / CD | ArgoCD (automated sync, self-heal, prune) | ✅ |
| 5 — Observability | Prometheus + Grafana (kube-prometheus-stack via Helm, custom ServiceMonitor) | ✅ |
| 6 — IaC | Terraform (Docker provider — init/plan/apply/destroy workflow) | ✅ |
| 7 — Config management | Ansible (playbooks, roles, containerized execution) | ✅ |

Every phase is documented in [`docs/glossary.md`](docs/glossary.md) — a running write-up of every tool, command, and error encountered along the way.

## Architecture

```
┌─────────────┐
│     API     │   FastAPI + SQLAlchemy + PostgreSQL
│  (FastAPI)  │   Snippet manager — CRUD over /api/snippets
└──────┬──────┘
       │
       ├── Dockerfile (multi-stage) ──► Docker Compose (local dev)
       │
       ├── GitHub Actions ──► lint → test → build
       │
       └── Kubernetes (kind) ──► Deployment + Service
                │
                ├── ArgoCD ──► GitOps sync from this repo
                │
                └── Prometheus + Grafana ──► /metrics scraping + dashboards

Terraform (Docker provider) ──► provisions a standalone copy of the stack
Ansible ──► bootstraps a server (common tools, Docker, K3s-ready)
```

## Repository structure

```
devops-playground/
├── apps/
│   └── api/                 # FastAPI service — snippets CRUD, /health, /metrics
├── .github/workflows/        # CI pipeline (lint, test)
├── infra/
│   ├── terraform/            # IaC — Docker provider, containers as resources
│   └── ansible/               # Playbooks — common/docker/k3s roles
├── k8s/base/                 # Kubernetes manifests (Deployment, Service, ServiceMonitor)
├── argocd/                   # ArgoCD Application manifest
├── monitoring/                # Prometheus + Grafana install notes (Helm-based)
├── docs/glossary.md          # Full write-up of every concept covered
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Running it locally

```bash
git clone https://github.com/lucybaia/devops-playground.git
cd devops-playground
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## Running it on Kubernetes

```bash
kind create cluster --name devstation
docker build -t devstation-api:latest ./apps/api
kind load docker-image devstation-api:latest --name devstation
kubectl apply -f k8s/base/api/deployment.yaml
kubectl apply -f k8s/base/database/deployment.yaml
kubectl port-forward service/api 8000:8000
```

ArgoCD and the monitoring stack (Prometheus/Grafana via Helm) are installed separately — see `docs/glossary.md` for the full install commands.

## Infrastructure as Code

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

Uses the Docker provider to provision a standalone network + containers, demonstrating the IaC workflow without requiring a cloud account.

## Configuration management

```bash
cd infra/ansible
docker build -t devstation-ansible .
docker run --rm devstation-ansible -i inventories/hosts.yml playbook.yml
```

## Status

Only the API service was implemented — the frontend and worker scaffolding exist in the repo history but weren't completed, since the API alone was enough to exercise all seven DevOps phases. This is a learning project, not a production app.

## License

MIT