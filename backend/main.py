import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer import RepositoryAnalyzer, AnalysisResult
from graph import GraphEngine, BlastRadiusResult, NetworkGraphExport
from risk_engine import RiskEngine, RiskReport
from runtime import RuntimeEngine, RuntimeGraph, ArchitectureDriftReport

app = FastAPI(
    title="Ripple API",
    description="Backend API for code change impact analysis, dependency graphs, and runtime drift detection.",
    version="0.1.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PathRequest(BaseModel):
    path: str = Field(default="demo_services", description="Local repository path to analyze")
    base_ref: Optional[str] = Field(default=None, description="Optional git base ref")

class CombinedImpactResponse(BaseModel):
    analysis: AnalysisResult
    impact: BlastRadiusResult
    risk_report: RiskReport
    graph: NetworkGraphExport

class DriftResponse(BaseModel):
    static_graph: NetworkGraphExport
    runtime_graph: RuntimeGraph
    drift_report: ArchitectureDriftReport

@app.get("/")
def read_root():
    return {"service": "Ripple API", "status": "healthy", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "ripple-backend"}

@app.get("/api/projects")
def list_projects():
    # Return available local project paths for demo selection
    return {
        "projects": [
            {"name": "Demo Microservices", "path": "demo_services", "description": "Distributed microservice application"},
            {"name": "Ripple Core Repository", "path": ".", "description": "Ripple monorepo itself"}
        ]
    }

@app.post("/api/analyze", response_model=AnalysisResult)
def analyze_repository(req: PathRequest):
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail=f"Repository path '{req.path}' not found.")
    try:
        analyzer = RepositoryAnalyzer(req.path)
        return analyzer.analyze(base_ref=req.base_ref)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/impact", response_model=CombinedImpactResponse)
def analyze_impact(req: PathRequest):
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail=f"Repository path '{req.path}' not found.")
    try:
        analyzer = RepositoryAnalyzer(req.path)
        analysis = analyzer.analyze(base_ref=req.base_ref)

        graph_engine = GraphEngine()
        impact = graph_engine.analyze_repository_impact(analysis)
        static_graph = graph_engine.get_graph_export(analysis)

        risk_engine = RiskEngine()
        risk_report = risk_engine.evaluate_risk(impact)

        return CombinedImpactResponse(
            analysis=analysis,
            impact=impact,
            risk_report=risk_report,
            graph=static_graph
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impact calculation failed: {str(e)}")

@app.post("/api/runtime", response_model=RuntimeGraph)
def get_runtime_telemetry(req: PathRequest):
    try:
        runtime_engine = RuntimeEngine()
        return runtime_engine.get_runtime_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve runtime telemetry: {str(e)}")

@app.post("/api/drift", response_model=DriftResponse)
def get_architecture_drift(req: PathRequest):
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail=f"Repository path '{req.path}' not found.")
    try:
        analyzer = RepositoryAnalyzer(req.path)
        analysis = analyzer.analyze(base_ref=req.base_ref)

        graph_engine = GraphEngine()
        static_graph = graph_engine.get_graph_export(analysis)

        runtime_engine = RuntimeEngine()
        runtime_graph = runtime_engine.get_runtime_graph()
        drift_report = runtime_engine.detect_architecture_drift(static_graph)

        return DriftResponse(
            static_graph=static_graph,
            runtime_graph=runtime_graph,
            drift_report=drift_report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {str(e)}")

@app.get("/api/graph", response_model=NetworkGraphExport)
def get_repository_graph(path: str = Query("demo_services")):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Repository path '{path}' not found.")
    try:
        analyzer = RepositoryAnalyzer(path)
        analysis = analyzer.analyze()
        graph_engine = GraphEngine()
        return graph_engine.get_graph_export(analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph generation failed: {str(e)}")
