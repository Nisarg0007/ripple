from typing import List, Tuple, Set, Optional
from graph.models import BlastRadiusResult
from risk_engine.models import RiskFactor

DEFAULT_CRITICAL_KEYWORDS = {"payment", "auth", "billing", "checkout", "user", "security"}

class RiskRuleEvaluator:
    """
    Evaluates risk factors deterministically from a BlastRadiusResult.
    """
    def __init__(self, critical_services: Optional[Set[str]] = None):
        self.critical_services = critical_services if critical_services is not None else DEFAULT_CRITICAL_KEYWORDS

    def evaluate(self, blast_radius: BlastRadiusResult, is_breaking_change: bool = False) -> Tuple[List[RiskFactor], List[str]]:
        factors: List[RiskFactor] = []
        recommendations: List[str] = []

        # Rule 1: Impacted node count
        imp_count = blast_radius.total_impacted_count
        if imp_count > 10:
            factors.append(RiskFactor(
                name="High Downstream Impact",
                description=f"Affects {imp_count} downstream components across the repository",
                score=35,
                severity="high"
            ))
            recommendations.append("Review downstream dependencies before merging")
        elif imp_count >= 4:
            factors.append(RiskFactor(
                name="Moderate Downstream Impact",
                description=f"Affects {imp_count} downstream components",
                score=20,
                severity="medium"
            ))
            recommendations.append("Review downstream dependencies before merging")
        elif imp_count >= 1:
            factors.append(RiskFactor(
                name="Minor Downstream Impact",
                description=f"Affects {imp_count} downstream component(s)",
                score=10,
                severity="low"
            ))

        # Rule 2: Critical service impact
        affected_critical = set()
        all_paths = [node.file_path for node in blast_radius.directly_changed_nodes if node.file_path]
        for node in blast_radius.impacted_nodes:
            if node.node.file_path:
                all_paths.append(node.node.file_path)

        for path in all_paths:
            path_lower = path.lower()
            for crit in self.critical_services:
                if crit in path_lower:
                    affected_critical.add(crit)

        if affected_critical:
            crit_names = ", ".join(sorted(list(affected_critical)))
            factors.append(RiskFactor(
                name="Critical Service Affected",
                description=f"Changes propagate to critical module(s): {crit_names}",
                score=25,
                severity="high"
            ))
            recommendations.append("Run integration tests for affected critical services")

        # Rule 3: API Endpoint Impact
        ep_count = len(blast_radius.impacted_endpoints)
        if ep_count > 1:
            factors.append(RiskFactor(
                name="Multiple API Endpoints Affected",
                description=f"Changes affect {ep_count} exposed API endpoints",
                score=25,
                severity="high"
            ))
            recommendations.append("Run API and contract tests for affected endpoints")
        elif ep_count == 1:
            factors.append(RiskFactor(
                name="API Endpoint Affected",
                description="Changes affect 1 exposed API endpoint",
                score=15,
                severity="medium"
            ))
            recommendations.append("Run API contract tests")

        # Rule 4: Dependency Depth
        depth = blast_radius.max_depth
        if depth >= 3:
            factors.append(RiskFactor(
                name="Deep Dependency Propagation",
                description=f"Impact propagates across {depth} dependency layers",
                score=25,
                severity="high"
            ))
            recommendations.append("Review the full dependency impact graph before deployment")
        elif depth == 2:
            factors.append(RiskFactor(
                name="Multi-level Propagation",
                description="Impact propagates 2 dependency layers deep",
                score=15,
                severity="medium"
            ))

        # Rule 5: Directly Changed Nodes
        direct_count = len(blast_radius.directly_changed_nodes)
        if direct_count > 5:
            factors.append(RiskFactor(
                name="Large Direct Surface Change",
                description=f"{direct_count} components directly modified",
                score=20,
                severity="medium"
            ))
            recommendations.append("Consider breaking down large PR into smaller commits")
        elif direct_count >= 3:
            factors.append(RiskFactor(
                name="Direct Component Modifications",
                description=f"{direct_count} components directly modified",
                score=10,
                severity="low"
            ))

        # Rule 6: Breaking API Change (if passed explicitly or detected)
        if is_breaking_change:
            factors.append(RiskFactor(
                name="Breaking API Change Detected",
                description="Modification includes a breaking interface/schema change",
                score=30,
                severity="critical"
            ))
            recommendations.append("Notify downstream consumers before merging breaking change")

        # Deduplicate recommendations
        unique_recs = []
        for rec in recommendations:
            if rec not in unique_recs:
                unique_recs.append(rec)

        return factors, unique_recs
