from typing import List
from risk_engine.models import RiskLevel, RiskFactor

class RiskScorer:
    """
    Computes total score and assigns RiskLevel.
    Formula: Total Score = Sum of Factor Scores, clamped to [0, 100].
    
    Level Mapping:
    - 0  to 30: LOW
    - 31 to 60: MEDIUM
    - 61 to 80: HIGH
    - 81 to 100: CRITICAL
    """
    def compute_score(self, factors: List[RiskFactor]) -> int:
        raw_score = sum(f.score for f in factors)
        return max(0, min(100, raw_score))

    def map_level(self, score: int) -> RiskLevel:
        if score <= 30:
            return RiskLevel.LOW
        elif score <= 60:
            return RiskLevel.MEDIUM
        elif score <= 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
