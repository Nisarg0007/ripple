import pytest
from analyzer import parse_python_file, RepositoryAnalyzer
from graph import DependencyGraphBuilder, ImpactAnalyzer, GraphEngine
from risk_engine import RiskEngine
from runtime import RuntimeEngine
from ai import AIService

def test_fastapi_endpoint_and_http_client_extraction():
    server_code = """
from fastapi import FastAPI
app = FastAPI()

@app.post("/payments")
def create_payment():
    return {"status": "ok"}
"""
    client_code = """
import httpx

def pay():
    url = f"{PAYMENT_URL}/payments"
    return httpx.post(url, json={"amount": 100})
"""
    sf_server = parse_python_file("services/payment/main.py", server_code, "services.payment.main")
    sf_client = parse_python_file("services/orders/client.py", client_code, "services.orders.client")

    # 1. FastAPI endpoint extracted
    assert len(sf_server.endpoints) == 1
    assert sf_server.endpoints[0].method == "POST"
    assert sf_server.endpoints[0].path == "/payments"

    # 2. HTTP client call extracted
    assert len(sf_client.http_calls) == 1
    assert sf_client.http_calls[0].method == "POST"
    assert sf_client.http_calls[0].path == "/payments"

def test_demo_services_http_service_dependencies():
    analyzer = RepositoryAnalyzer("demo_services")
    analysis = analyzer.analyze()

    builder = DependencyGraphBuilder()
    graph = builder.build_graph(analysis)

    # 3 & 4. orders_service -> payment_service
    assert graph.has_edge("file:orders_service/clients.py", "endpoint:POST:/payments") or \
           graph.has_edge("file:orders_service/clients.py", "file:payment_service/main.py") or \
           graph.has_edge("file:orders_service/main.py", "file:payment_service/main.py")

    # 5. orders_service -> inventory_service
    assert graph.has_edge("file:orders_service/clients.py", "endpoint:POST:/inventory/reserve") or \
           graph.has_edge("file:orders_service/clients.py", "file:inventory_service/main.py") or \
           graph.has_edge("file:orders_service/main.py", "file:inventory_service/main.py")

    # 6. orders_service -> users_service
    assert graph.has_edge("file:orders_service/clients.py", "endpoint:GET:/users/{user_id}") or \
           graph.has_edge("file:orders_service/clients.py", "file:users_service/main.py") or \
           graph.has_edge("file:orders_service/main.py", "file:users_service/main.py")

    # 7. api_gateway -> orders_service
    assert graph.has_edge("file:api_gateway/main.py", "endpoint:POST:/orders") or \
           graph.has_edge("file:api_gateway/main.py", "file:orders_service/main.py")

def test_telemetry_file_ignored():
    analyzer = RepositoryAnalyzer("demo_services")
    analysis = analyzer.analyze()
    file_paths = [f.path for f in analysis.files]

    assert ".ripple_telemetry.json" not in file_paths
    assert "ripple-report.md" not in file_paths

def test_all_existing_engines_unaffected():
    analyzer = RepositoryAnalyzer("demo_services")
    analysis = analyzer.analyze()

    graph_engine = GraphEngine()
    impact = graph_engine.analyze_repository_impact(analysis)

    risk_engine = RiskEngine()
    risk_report = risk_engine.evaluate_risk(impact)

    runtime_engine = RuntimeEngine()
    runtime_graph = runtime_engine.get_runtime_graph()

    ai_service = AIService()
    explanation = ai_service.generate_explanation(risk_report.model_dump())

    assert risk_report is not None
    assert runtime_graph is not None
    assert explanation is not None
