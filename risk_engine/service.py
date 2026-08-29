from typing import Optional, Set, List
from graph.models import BlastRadiusResult
from risk_engine.models import RiskReport
from risk_engine.rules import RiskRuleEvaluator
from risk_engine.scorer import RiskScorer

class RiskEngine:
    """
    High-level service interface for computing risk reports from impact analysis.
    """
    def __init__(self, critical_services: Optional[Set[str]] = None):
        self.evaluator = RiskRuleEvaluator(critical_services=critical_services)
        self.scorer = RiskScorer()

    def evaluate_risk(self, blast_radius: BlastRadiusResult, is_breaking_change: bool = False) -> RiskReport:
        factors, recommendations = self.evaluator.evaluate(blast_radius, is_breaking_change=is_breaking_change)
        total_score = self.scorer.compute_score(factors)
        risk_level = self.scorer.map_level(total_score)

        directly_changed_files = blast_radius.directly_changed_files
        directly_changed_nodes = [n.label for n in blast_radius.directly_changed_nodes]
        impacted_nodes = [n.node.label for n in blast_radius.impacted_nodes]
        affected_endpoints = [n.label for n in blast_radius.impacted_endpoints]

        # Extract affected services/directories from file paths
        affected_services = set()
        for fpath in directly_changed_files + [n.node.file_path for n in blast_radius.impacted_nodes if n.node.file_path]:
            parts = fpath.replace("\\", "/").split("/")
            if len(parts) > 1:
                affected_services.add(parts[0])

        return RiskReport(
            total_score=total_score,
            risk_level=risk_level,
            factors=factors,
            directly_changed_files=directly_changed_files,
            directly_changed_nodes=directly_changed_nodes,
            impacted_nodes=impacted_nodes,
            affected_services=sorted(list(affected_services)),
            affected_endpoints=affected_endpoints,
            recommendations=recommendations,
            is_breaking_change=is_breaking_change
        )
