# Ripple

> *"Git shows you the change. Ripple shows you the ripple effect."*

Ripple is a developer tool built for **BuildSprint 2026** that helps software engineers understand the real downstream impact and risk of a code change before it reaches production.

---

## 🚨 Problem Statement

When engineers create Pull Requests, standard git diffs show line-by-line modifications within a localized context. However, modern microservices, APIs, and shared libraries mean local code edits often trigger unseen breaking changes across other services, downstream endpoints, or dependent modules.

Code reviews today lack automated, cross-service dependency impact analysis, leading to unexpected outages and breaking changes reaching production environments.

---

## 💡 Solution Overview

Ripple analyzes modified code alongside system dependency metadata (services, APIs, schemas, and import trees). It computes an impact graph and calculates a deterministic risk score for the change, presenting a visual ripple effect map directly in the developer workflow.

Key principles:
1. **Deterministic & Explainable Core**: Risk scoring and impact traversal are mathematically sound and traceable via NetworkX graph traversal.
2. **AI Explanation Layer**: Generates plain-language summaries and impact insights based on deterministic graph findings.
3. **Multi-Interface**: Supports CLI execution locally and interactive web visualizations on the dashboard.

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
                                 |      Graph       | (Builds & traverses NetworkX DAG)
                                 +--------+---------+
                                          |
                                          v
                                 +------------------+
                                 |   Risk Engine    | (Computes deterministic risk score)
                                 +--------+---------+
                                          |
                                          v
                                 +------------------+
                                 |  FastAPI Backend | (Exposes REST API & Data Store)
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

- `backend/`: FastAPI application hosting REST endpoints, database access models, and API logic.
- `frontend/`: React + TypeScript + Vite web dashboard for interactive visual graph rendering and risk summaries.
- `cli/`: Command Line Interface for local developer workflow execution and CI integration.
- `analyzer/`: Engine responsible for parsing code, diffs, ASTs, schema definitions, and API interfaces.
- `graph/`: NetworkX graph representation, traversal engines, and downstream blast-radius calculator.
- `risk-engine/`: Deterministic rules engine that outputs numerical risk scores based on blast radius, criticality, and breaking change flags.
- `demo-services/`: Sample microservice codebase used to demonstrate Ripple's detection capabilities during testing and judging.
- `tests/`: Automated unit and integration test suite (using Pytest).
- `docs/`: Technical documentation, API specs, and Architecture Decision Records (ADRs).

---

## ⚡ 48-Hour Hackathon MVP Scope

For BuildSprint 2026, the MVP will deliver:
1. **Static AST & Dependency Graph Extraction**: Parse demo microservice ASTs and schemas into a NetworkX dependency graph.
2. **Diff Blast Radius Traversal**: Evaluate changed lines/files against the dependency graph to find downstream affected services/endpoints.
3. **Deterministic Scoring**: Calculate risk score (Low / Medium / High / Critical) based on direct & indirect impact paths.
4. **Interactive Graph UI**: Display the ripple map and blast radius visually on the React dashboard.
5. **CLI Command**: Run `ripple analyze` locally against git diffs.

---

## 🚀 Running the Project Skeleton

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)

### Backend Setup
1. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the backend development server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   Access API Docs at `http://localhost:8000/docs`

### CLI Execution
Run the CLI skeleton:
```bash
python -m cli.main --version
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Docker Setup
Run the infrastructure and backend:
```bash
docker-compose up --build
```
