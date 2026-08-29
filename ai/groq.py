import os
import json
import httpx
from typing import Dict, Any
from ai.provider import AIProvider
from ai.models import ExplanationResponse
from ai.prompts import SYSTEM_PROMPT, build_user_prompt
from ai.fallback import DeterministicFallbackGenerator

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqProvider(AIProvider):
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.fallback = DeterministicFallbackGenerator()

    def generate_explanation(self, risk_report_dict: Dict[str, Any]) -> ExplanationResponse:
        if not self.api_key:
            return self.fallback.generate(risk_report_dict, reason="GROQ_API_KEY environment variable is not set")

        user_prompt = build_user_prompt(risk_report_dict)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            resp = httpx.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=10.0
            )

            if resp.status_code != 200:
                return self.fallback.generate(risk_report_dict, reason=f"Groq API returned HTTP {resp.status_code}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            return ExplanationResponse(
                summary=parsed.get("summary", ""),
                why_risky=parsed.get("why_risky", ""),
                affected_components=parsed.get("affected_components", []),
                recommended_actions=parsed.get("recommended_actions", []),
                provider_used="groq",
                is_fallback=False
            )
        except Exception as e:
            return self.fallback.generate(risk_report_dict, reason=f"Groq request failed: {str(e)}")
