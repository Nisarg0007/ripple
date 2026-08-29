import os
from typing import Dict, Any, Optional
from ai.models import ExplanationResponse
from ai.groq import GroqProvider
from ai.nim import NvidiaNimProvider
from ai.fallback import DeterministicFallbackGenerator

class AIService:
    """
    Manager service for selecting AI provider (Groq / NVIDIA NIM / Fallback).
    Gracefully cascades on missing keys or HTTP failures.
    """
    def __init__(self, preferred_provider: Optional[str] = None):
        self.preferred_provider = preferred_provider or os.getenv("RIPPLE_AI_PROVIDER", "groq").lower()
        self.fallback = DeterministicFallbackGenerator()

    def generate_explanation(self, risk_report_dict: Dict[str, Any]) -> ExplanationResponse:
        groq_key = os.getenv("GROQ_API_KEY")
        nim_key = os.getenv("NVIDIA_NIM_API_KEY")

        # Preferred provider route
        if self.preferred_provider == "groq" and groq_key:
            res = GroqProvider(api_key=groq_key).generate_explanation(risk_report_dict)
            if not res.is_fallback:
                return res

        if self.preferred_provider == "nvidia_nim" and nim_key:
            res = NvidiaNimProvider(api_key=nim_key).generate_explanation(risk_report_dict)
            if not res.is_fallback:
                return res

        # Secondary fallback route
        if groq_key:
            res = GroqProvider(api_key=groq_key).generate_explanation(risk_report_dict)
            if not res.is_fallback:
                return res

        if nim_key:
            res = NvidiaNimProvider(api_key=nim_key).generate_explanation(risk_report_dict)
            if not res.is_fallback:
                return res

        # Final deterministic fallback
        return self.fallback.generate(risk_report_dict, reason="No active AI provider API key found (GROQ_API_KEY or NVIDIA_NIM_API_KEY)")
