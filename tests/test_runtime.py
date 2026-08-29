import pytest
import tempfile
import os
from runtime import (
    RuntimeEngine,
    RuntimeObservation,
    TraceCollector,
    RuntimeAnalyzer,
    ArchitectureDriftDetector
)
from graph.models import NetworkGraphExport, GraphNode, GraphEdge, NodeType, EdgeType

def test_runtime_observation_representation_and_aggregation():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        engine = RuntimeEngine(collector_path=tmp_path)
        engine.clear_runtime_data()

        # Add observations
        obs1 = RuntimeObservation(
            trace_id="t1", span_id="s1", source_service="orders-service",
            destination_service="payment-service", operation="POST /payments",
            duration_ms=100.0, status_code=200, is_error=False
        )
        obs2 = RuntimeObservation(
            trace_id="t2", span_id="s2", source_service="orders-service",
            destination_service="payment-service", operation="POST /payments",
            duration_ms=200.0, status_code=500, is_error=True
        )

        engine.record_trace(obs1)
        engine.record_trace(obs2)

        graph = engine.get_runtime_graph()

        assert "orders-service" in graph.services
        assert "payment-service" in graph.services
        assert len(graph.edges) == 1

        edge = graph.edges[0]
        assert edge.source_service == "orders-service"
        assert edge.destination_service == "payment-service"
        assert edge.request_count == 2
        assert edge.error_count == 1
        assert edge.average_latency_ms == 150.0

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_otlp_json_ingestion():
    collector = TraceCollector(storage_path=":memory:")
    otlp_payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "orders-service"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "abc123trace",
                                "spanId": "span1",
                                "name": "POST /payments",
                                "startTimeUnixNano": "1700000000000000000",
                                "endTimeUnixNano": "1700000000050000000",
                                "status": {"code": "STATUS_CODE_UNSET"},
                                "attributes": [
                                    {"key": "peer.service", "value": {"stringValue": "payment-service"}},
                                    {"key": "http.status_code", "value": {"intValue": 200}}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    collector.ingest_otlp_json(otlp_payload)
    obs = collector.get_observations()

    assert len(obs) == 1
    assert obs[0].source_service == "orders-service"
    assert obs[0].destination_service == "payment-service"
    assert obs[0].duration_ms == 50.0

def test_architecture_drift_detection():
    detector = ArchitectureDriftDetector()

    # Static Graph Export
    static_export = NetworkGraphExport(
        nodes=[
            GraphNode(id="file:orders.py", label="orders.py", type=NodeType.FILE),
            GraphNode(id="file:payment.py", label="payment.py", type=NodeType.FILE)
        ],
        edges=[
            GraphEdge(source="file:orders.py", target="file:payment.py", type=EdgeType.IMPORTS)
        ]
    )

    # Runtime Graph with Drift (orders calls fraud service at runtime)
    analyzer = RuntimeAnalyzer()
    obs = [
        RuntimeObservation(
            trace_id="t1", span_id="s1", source_service="orders",
            destination_service="payment", operation="POST /payments", duration_ms=50.0
        ),
        RuntimeObservation(
            trace_id="t2", span_id="s2", source_service="orders",
            destination_service="fraud", operation="POST /check_fraud", duration_ms=30.0
        )
    ]
    runtime_graph = analyzer.aggregate_observations(obs)

    drift_report = detector.compare(static_export, runtime_graph)

    # Orders -> Payment is verified
    assert len(drift_report.verified_dependencies) == 1
    # Orders -> Fraud is runtime-only drift!
    assert len(drift_report.runtime_only_dependencies) == 1
    assert drift_report.runtime_only_dependencies[0].target == "fraud"
