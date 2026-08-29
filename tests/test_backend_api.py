import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_backend_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["service"] == "ripple-backend"

def test_backend_projects_list():
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    projects = resp.json()["projects"]
    assert len(projects) >= 2
    paths = [p["path"] for p in projects]
    assert "demo_services" in paths

def test_backend_analyze_endpoint():
    resp = client.post("/api/analyze", json={"path": "demo_services"})
    assert resp.status_code == 200
    data = resp.json()
    assert "repository" in data
    assert "files" in data
    assert data["summary"]["python_files"] > 0

def test_backend_impact_endpoint():
    resp = client.post("/api/impact", json={"path": "demo_services"})
    assert resp.status_code == 200
    data = resp.json()
    assert "impact" in data
    assert "risk_report" in data
    assert "total_score" in data["risk_report"]
    assert "risk_level" in data["risk_report"]

def test_backend_runtime_endpoint():
    resp = client.post("/api/runtime", json={"path": "demo_services"})
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert "edges" in data

def test_backend_drift_endpoint():
    resp = client.post("/api/drift", json={"path": "demo_services"})
    assert resp.status_code == 200
    data = resp.json()
    assert "static_graph" in data
    assert "runtime_graph" in data
    assert "drift_report" in data

def test_backend_graph_endpoint():
    resp = client.get("/api/graph?path=demo_services")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data

def test_backend_invalid_path_404():
    resp = client.post("/api/analyze", json={"path": "non_existent_folder_xyz"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
