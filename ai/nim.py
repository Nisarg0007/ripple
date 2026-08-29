import os
import json
import httpx
from typing import Dict, Any
from ai.provider import AIProvider
from ai.models import ExplanationResponse
from ai.prompts import SYSTEM_PROMPT, build_user_prompt
from ai.fallback import DeterministicFallbackGenerator

NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

class NvidiaNimProvider(AIProvider):
    def __init__(self, api_key: str = None, model: str = "meta/llama-3.1-70b-instruct"):
        self.api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY")
        self.model = model
        self.fallback = DeterministicFallbackGenerator()

    def generate_explanation(self, risk_report_dict: Dict[str, Any]) -> ExplanationResponse:
        if not self.api_key:
            return self.fallback.generate(risk_report_dict, reason="NVIDIA_NIM_API_KEY environment variable is not set")

        user_prompt = build_user_prompt(risk_report_dict)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        try:
            resp = httpx.post(
                NVIDIA_NIM_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=10.0
            )

            if resp.status_code != 200:
                return self.fallback.generate(risk_report_dict, reason=f"NVIDIA NIM returned HTTP {resp.status_code}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON from response
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # Handle possible markdown backticks code blocks
                clean = content.strip().strip("```json").strip("```")
                parsed = json.loads(clean)

            return ExplanationResponse(
                summary=parsed.get("summary", ""),
                why_risky=parsed.get("why_risky", ""),
                affected_components=parsed.get("affected_components", []),
                recommended_actions=parsed.get("recommended_actions", []),
                provider_used="nvidia_nim",
                is_fallback=False
            )
        except Exception as e:
            return self.fallback.generate(risk_report_dict, reason=f"NVIDIA NIM request failed: {str(e)}")
