from typing import Dict, Any
from ai.models import ExplanationResponse

class DeterministicFallbackGenerator:
    """
    Generates plain-text explanations deterministically from a Risk Report without external AI calls.
    """
    def generate(self, risk_report_dict: Dict[str, Any], reason: str = "AI provider disabled or unavailable") -> ExplanationResponse:
        level = risk_report_dict.get("risk_level", "LOW")
        score = risk_report_dict.get("total_score", 0)
        affected_services = risk_report_dict.get("affected_services", [])
        affected_endpoints = risk_report_dict.get("affected_endpoints", [])
        factors = risk_report_dict.get("factors", [])
        recs = risk_report_dict.get("recommendations", [])

        summary = f"{level}-risk change (score: {score}/100) affecting {len(affected_services)} service(s) and {len(affected_endpoints)} API endpoint(s)."

        factor_names = [f.get("name") if isinstance(f, dict) else str(f) for f in factors]
        if factor_names:
            why_risky = f"This change carries elevated risk due to the following factors: {', '.join(factor_names)}. Downstream components consuming these modules may experience breaking interface or runtime behavior."
        else:
            why_risky = "This change has a low risk profile with localized modifications and minimal downstream impact."

        affected_components = affected_services + affected_endpoints
        if not affected_components:
            affected_components = risk_report_dict.get("directly_changed_files", [])

        recommended_actions = recs if recs else ["Proceed with standard peer code review."]

        return ExplanationResponse(
            summary=summary,
            why_risky=why_risky,
            affected_components=affected_components,
            recommended_actions=recommended_actions,
            provider_used="fallback",
            is_fallback=True,
            fallback_reason=reason
        )
