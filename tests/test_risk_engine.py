import pytest
from graph.models import BlastRadiusResult, GraphNode, ImpactedNode, NodeType
from risk_engine import RiskEngine, RiskLevel, RiskScorer

def test_empty_impact_analysis_handled_safely():
    engine = RiskEngine()
    empty_br = BlastRadiusResult()
    report = engine.evaluate_risk(empty_br)

    assert report.total_score == 0
    assert report.risk_level == RiskLevel.LOW
    assert len(report.factors) == 0
    assert len(report.recommendations) == 0

def test_small_isolated_change():
    engine = RiskEngine()
    node = GraphNode(id="file:utils/helpers.py", label="helpers.py", type=NodeType.FILE, file_path="utils/helpers.py")
    br = BlastRadiusResult(
        directly_changed_files=["utils/helpers.py"],
        directly_changed_nodes=[node],
        impacted_nodes=[],
        total_impacted_count=0
    )
    report = engine.evaluate_risk(br)

    assert report.total_score <= 30
    assert report.risk_level == RiskLevel.LOW

def test_downstream_impact_and_score():
    engine = RiskEngine()
    direct_node = GraphNode(id="file:common/base.py", label="base.py", type=NodeType.FILE, file_path="common/base.py")
    impacted = [
        ImpactedNode(node=GraphNode(id=f"file:svc_{i}.py", label=f"svc_{i}.py", type=NodeType.FILE, file_path=f"svc_{i}.py"), distance=1, impact_type="dependent")
        for i in range(5)
    ]
    br = BlastRadiusResult(
        directly_changed_files=["common/base.py"],
        directly_changed_nodes=[direct_node],
        impacted_nodes=impacted,
        total_impacted_count=5
    )
    report = engine.evaluate_risk(br)

    assert report.total_score > 0
    assert any("Downstream Impact" in f.name for f in report.factors)

def test_critical_service_impact():
    engine = RiskEngine(critical_services={"payment"})
    payment_node = GraphNode(id="file:services/payment/service.py", label="payment/service.py", type=NodeType.FILE, file_path="services/payment/service.py")
    br = BlastRadiusResult(
        directly_changed_files=["services/payment/service.py"],
        directly_changed_nodes=[payment_node],
        total_impacted_count=1
    )
    report = engine.evaluate_risk(br)

    assert any(f.name == "Critical Service Affected" for f in report.factors)
    assert "Run integration tests for affected critical services" in report.recommendations

def test_api_endpoint_impact():
    engine = RiskEngine()
    ep = GraphNode(id="endpoint:POST:/payments", label="POST /payments", type=NodeType.ENDPOINT, file_path="api/payment.py")
    br = BlastRadiusResult(
        directly_changed_files=["api/payment.py"],
        impacted_endpoints=[ep],
        total_impacted_count=1
    )
    report = engine.evaluate_risk(br)

    assert any("API Endpoint" in f.name for f in report.factors)
    assert any("contract tests" in r for r in report.recommendations)

def test_deep_dependency_chain():
    engine = RiskEngine()
    br = BlastRadiusResult(
        max_depth=3,
        total_impacted_count=2
    )
    report = engine.evaluate_risk(br)

    assert any("Deep Dependency" in f.name for f in report.factors)

def test_combining_multiple_risk_factors():
    engine = RiskEngine(critical_services={"payment"})
    ep1 = GraphNode(id="endpoint:POST:/checkout", label="POST /checkout", type=NodeType.ENDPOINT, file_path="services/payment/checkout.py")
    ep2 = GraphNode(id="endpoint:GET:/history", label="GET /history", type=NodeType.ENDPOINT, file_path="services/payment/history.py")

    node = GraphNode(id="file:services/payment/core.py", label="core.py", type=NodeType.FILE, file_path="services/payment/core.py")
    
    impacted = [
        ImpactedNode(node=GraphNode(id=f"file:dep_{i}.py", label=f"dep_{i}.py", type=NodeType.FILE, file_path=f"dep_{i}.py"), distance=1, impact_type="dependent")
        for i in range(12)
    ]

    br = BlastRadiusResult(
        directly_changed_files=["services/payment/core.py"],
        directly_changed_nodes=[node],
        impacted_nodes=impacted,
        impacted_endpoints=[ep1, ep2],
        total_impacted_count=12,
        max_depth=3
    )
    report = engine.evaluate_risk(br, is_breaking_change=True)

    assert report.total_score >= 81
    assert report.risk_level == RiskLevel.CRITICAL
    assert len(report.factors) >= 4

def test_score_clamping_to_100():
    scorer = RiskScorer()
    from risk_engine.models import RiskFactor
    factors = [RiskFactor(name="Huge Factor", description="test", score=150, severity="critical")]
    score = scorer.compute_score(factors)
    assert score == 100

def test_risk_level_mapping():
    scorer = RiskScorer()
    assert scorer.map_level(15) == RiskLevel.LOW
    assert scorer.map_level(30) == RiskLevel.LOW
    assert scorer.map_level(45) == RiskLevel.MEDIUM
    assert scorer.map_level(60) == RiskLevel.MEDIUM
    assert scorer.map_level(75) == RiskLevel.HIGH
    assert scorer.map_level(80) == RiskLevel.HIGH
    assert scorer.map_level(85) == RiskLevel.CRITICAL
