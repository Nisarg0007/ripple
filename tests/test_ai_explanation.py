import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from ai import (
    AIService,
    GroqProvider,
    NvidiaNimProvider,
    DeterministicFallbackGenerator,
    ExplanationResponse
)
from backend.main import app
from cli.main import main

client = TestClient(app)

MOCK_RISK_REPORT = {
    "total_score": 75,
    "risk_level": "HIGH",
    "factors": [
        {"name": "Critical Service Affected", "description": "Changes propagate to payment module", "score": 25, "severity": "high"}
    ],
    "directly_changed_files": ["services/payment/core.py"],
    "affected_services": ["payment-service", "orders-service"],
    "affected_endpoints": ["POST /payments"],
    "recommendations": ["Run payment integration tests", "Run API contract tests"]
}

def test_deterministic_fallback_generator():
    generator = DeterministicFallbackGenerator()
    res = generator.generate(MOCK_RISK_REPORT, reason="Test fallback")

    assert res.is_fallback is True
    assert res.fallback_reason == "Test fallback"
    assert "High" in res.summary or "HIGH" in res.summary
    assert "payment-service" in res.affected_components or "POST /payments" in res.affected_components
    assert len(res.recommended_actions) > 0

def test_missing_api_keys_falls_back_gracefully():
    with patch.dict(os.environ, {"GROQ_API_KEY": "", "NVIDIA_NIM_API_KEY": ""}, clear=True):
        service = AIService()
        res = service.generate_explanation(MOCK_RISK_REPORT)

        assert res.is_fallback is True
        assert "No active AI provider" in res.fallback_reason

def test_groq_provider_mock_response():
    mock_json = {
        "choices": [
            {
                "message": {
                    "content": '{"summary": "High risk payment change", "why_risky": "Modifies core payment logic", "affected_components": ["payment-service"], "recommended_actions": ["Run contract tests"]}'
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_json

    with patch("httpx.post", return_value=mock_resp):
        provider = GroqProvider(api_key="mock_groq_key")
        res = provider.generate_explanation(MOCK_RISK_REPORT)

        assert res.is_fallback is False
        assert res.provider_used == "groq"
        assert res.summary == "High risk payment change"
        assert "payment-service" in res.affected_components

def test_nvidia_nim_provider_mock_response():
    mock_json = {
        "choices": [
            {
                "message": {
                    "content": '{"summary": "NVIDIA explanation", "why_risky": "Downstream impact detected", "affected_components": ["orders-service"], "recommended_actions": ["Run integration tests"]}'
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_json

    with patch("httpx.post", return_value=mock_resp):
        provider = NvidiaNimProvider(api_key="mock_nim_key")
        res = provider.generate_explanation(MOCK_RISK_REPORT)

        assert res.is_fallback is False
        assert res.provider_used == "nvidia_nim"
        assert res.summary == "NVIDIA explanation"

def test_groq_provider_http_failure_falls_back():
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.post", return_value=mock_resp):
        provider = GroqProvider(api_key="mock_key")
        res = provider.generate_explanation(MOCK_RISK_REPORT)

        assert res.is_fallback is True
        assert "HTTP 500" in res.fallback_reason

def test_malformed_ai_json_response_falls_back():
    mock_json = {
        "choices": [
            {
                "message": {
                    "content": "INVALID NON-JSON TEXT"
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_json

    with patch("httpx.post", return_value=mock_resp):
        provider = GroqProvider(api_key="mock_key")
        res = provider.generate_explanation(MOCK_RISK_REPORT)

        assert res.is_fallback is True

def test_backend_impact_api_with_explain_true():
    resp = client.post("/api/impact", json={"path": "demo_services", "explain": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "explanation" in data
    assert data["explanation"] is not None
    assert "summary" in data["explanation"]

def test_backend_impact_api_with_explain_false():
    resp = client.post("/api/impact", json={"path": "demo_services", "explain": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("explanation") is None

def test_cli_impact_explain_flag(capsys):
    with patch("sys.argv", ["cli.main", "impact", "demo_services", "--explain"]):
        main()
    captured = capsys.readouterr()
    assert "Why This Matters (AI Explanation)" in captured.out
    assert "Ripple Impact Analysis" in captured.out
