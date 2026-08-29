# Ripple

> *"Git shows you the change. Ripple shows you the ripple effect."*

Ripple is a developer tool built for **BuildSprint 2026** that helps software engineers understand the real downstream impact and risk of a code change before it reaches production.

---

## 🚨 Problem Statement

When engineers create Pull Requests, standard git diffs show line-by-line modifications within a localized context. However, modern microservices, APIs, and shared libraries mean local code edits often trigger unseen breaking changes across other services, downstream endpoints, or dependent modules.

Code reviews today lack automated, cross-service dependency impact analysis, leading to unexpected outages and breaking changes reaching production environments.

---

## 💡 Solution Overview

Ripple analyzes modified code alongside system dependency metadata (services, APIs, schemas, and import trees) and OpenTelemetry runtime traces. It computes an impact graph and calculates a deterministic risk score for the change, presenting a visual ripple effect map directly in the developer workflow and CI pipeline.

Key principles:
1. **Deterministic & Explainable Core**: Risk scoring and impact traversal are mathematically sound and traceable via NetworkX graph traversal.
2. **Runtime Intelligence**: OpenTelemetry trace collection compares static code structure against actual runtime service traffic.
3. **Multi-Interface**: Supports local CLI commands, automated GitHub Actions checks, and an interactive React web dashboard.

---

## ⚡ CLI Quick Start

Ripple provides local developer CLI commands for repository inspection and risk evaluation:

```bash
# 1. Scan repository structure & AST symbols
python -m cli.main scan demo_services

# 2. Analyze change impact & blast radius
python -m cli.main impact demo_services

# 3. View live OpenTelemetry runtime service dependencies
python -m cli.main runtime demo_services

# 4. Detect architecture drift (Static Graph vs Runtime Reality)
python -m cli.main drift demo_services

# 5. Run CI/CD policy risk check
python -m cli.main check demo_services --fail-on high
```

### Risk Score Policy & Exit Codes
The `check` command evaluates the pull request change risk against a policy threshold:
- **Exit Code 0**: Risk is below threshold (PASS).
- **Exit Code 1**: Risk equals or exceeds threshold (e.g., `HIGH` or `CRITICAL`) — (FAIL).
- **Exit Code 2**: Execution error or invalid repository path.

Example CLI Check output:
```text
🌊 Ripple CI Check

Change Risk: HIGH — 75/100

Impact:
  5 components
  1 API
  3 dependency levels

Warnings / Risk Factors:
  - Critical Service Affected: Changes propagate to critical module(s): payment
  - API Endpoint Affected: Changes affect 1 exposed API endpoint

Policy Check (Threshold: HIGH): FAILED
```

---

## 🤖 GitHub Actions Integration

Automate change impact checks on every Pull Request using `.github/workflows/ripple-check.yml`:

```yaml
name: Ripple Change Impact Analysis

on:
  pull_request:
    branches: [ main, master ]

jobs:
  ripple-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run Ripple CI Check
        run: python -m cli.main check . --fail-on high --output-markdown ripple-report.md

      - name: Upload Report Artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ripple-report
          path: ripple-report.md
```

---

## 🏗️ Architecture

```text
                                 +------------------+
                                 |  GitHub PR / CLI |
                                 +--------+---------+
                                          |
                                          v
                                 +------------------+
                                 |    Analyzer      | (Extracts AST / diff metadata)
                                 +--------+---------+
                                          |
                                          v
                                 +------------------+
                                 |  Graph & Runtime | (NetworkX DAG + OTLP Telemetry)
                                 +--------+---------+
                                          |
                                          v
                                 +------------------+
                                 |   Risk Engine    | (Deterministic 0-100 risk scoring)
                                 +--------+---------+
                                          |
                                          v
                                 +------------------+
                                 |  FastAPI Backend | (Exposes REST API)
                                 +----+--------+----+
                                      |        |
                         +------------+        +------------+
                         v                                  v
                +-----------------+                +-----------------+
                | React Dashboard |                |   Ripple CLI    |
                +-----------------+                +-----------------+
```

---

## 📁 Repository Directory Structure

- `backend/`: FastAPI REST backend orchestrating analyzer, graph, risk, and runtime engines.
- `frontend/`: React + TypeScript + Vite web dashboard featuring React Flow graph visualizers.
- `cli/`: Developer CLI tool supporting `scan`, `impact`, `runtime`, `drift`, and `check`.
- `analyzer/`: AST parsing and git diff extraction module.
- `graph/`: NetworkX graph representation and blast-radius traversal engine.
- `risk_engine/`: Deterministic 0–100 risk scoring rules engine.
- `runtime/`: OpenTelemetry trace collector and architecture drift detector.
- `demo_services/`: Distributed microservice application (Gateway, Users, Orders, Payment, Inventory).
- `.github/workflows/`: GitHub Actions CI pipeline.
- `tests/`: Pytest suite (32+ unit & integration tests).

---

## 🚀 Running the Project

### 1. Run Backend API
```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. Run Dashboard
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Test Suite
```bash
python -m pytest
```
