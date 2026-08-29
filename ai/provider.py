from abc import ABC, abstractmethod
from typing import Dict, Any
from ai.models import ExplanationResponse

class AIProvider(ABC):
    """
    Abstract Base Class for Ripple AI Explanation Providers.
    """
    @abstractmethod
    def generate_explanation(self, risk_report_dict: Dict[str, Any]) -> ExplanationResponse:
        pass
