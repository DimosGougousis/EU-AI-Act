"""
Tests for ClassifyBot — EU AI Act risk-tier classification agent.

Tests verify:
  1. Tool schema validity (no API required)
  2. Agent function returns dict with expected keys (mocked API)
  3. Prohibited AI system is handled correctly
  4. Tool helper functions work correctly
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "agents" / "schemas"


# ─── Schema validation ────────────────────────────────────────────────────────

class TestClassifyBotToolSchemas:
    """Tool schema tests require no API key and no imports of openai."""

    def test_schema_file_exists(self):
        assert (SCHEMAS_DIR / "classify_bot_tools.json").exists(), \
            "classify_bot_tools.json not found in agents/schemas/"

    def test_schema_is_valid_json(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        assert isinstance(tools, list), "Tools schema must be a JSON array"

    def test_schema_has_minimum_tools(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        assert len(tools) >= 3, "ClassifyBot should define at least 3 tools"

    def test_each_tool_has_required_keys(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            assert tool.get("type") == "function", \
                f"Tool must have type 'function' (OpenAI format)"
            fn = tool.get("function", {})
            for key in ("name", "description", "parameters"):
                assert key in fn, \
                    f"tool['function'] missing key '{key}' in tool '{fn.get('name', '?')}'"

    def test_input_schema_is_object_type(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            params = tool["function"].get("parameters", {})
            assert params.get("type") == "object", \
                f"Tool '{tool['function']['name']}' parameters.type must be 'object'"

    def test_tool_names_are_unique(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        names = [t["function"]["name"] for t in tools]
        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        names = {t["function"]["name"] for t in tools}
        expected = {"check_annex_iii", "check_fraud_exemption", "generate_classification_report"}
        missing = expected - names
        assert not missing, f"Expected tools not found: {missing}"


# ─── Agent function tests (mocked API) ────────────────────────────────────────

class TestClassifySystemFunction:

    def _make_response(self, payload: dict):
        """Build a valid mock chat.completions response (no tool calls, JSON content)."""
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = json.dumps(payload)
        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    def test_returns_dict(self, sample_ai_system_description):
        """classify_system() must return a dict even with mocked API."""
        from agents.classify_bot import classify_system

        mock_response = self._make_response({
            "risk_tier": "HIGH_RISK",
            "legal_basis": "Annex III, Point 5(b)",
            "confidence": 0.97,
        })

        with patch("agents.classify_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = classify_system(sample_ai_system_description)

        assert isinstance(result, dict), "classify_system must return a dict"

    def test_high_risk_system_classified_correctly(self, sample_ai_system_description):
        """PulseCredit should be classified as HIGH_RISK."""
        from agents.classify_bot import classify_system

        mock_response = self._make_response({
            "risk_tier": "HIGH_RISK",
            "legal_basis": "Annex III, Point 5(b)",
            "confidence": 0.97,
        })

        with patch("agents.classify_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = classify_system(sample_ai_system_description)

        assert result.get("risk_tier") == "HIGH_RISK"
        assert "legal_basis" in result, "Result must include legal_basis"

    def test_fraud_system_exemption_handling(self, sample_fraud_system_description):
        """Fraud-only system should not be HIGH_RISK (Recital 58 exemption)."""
        from agents.classify_bot import classify_system

        mock_response = self._make_response({
            "risk_tier": "MINIMAL_RISK",
            "legal_basis": "Recital 58 — Fraud detection exemption",
            "confidence": 0.90,
        })

        with patch("agents.classify_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = classify_system(sample_fraud_system_description)

        assert result.get("risk_tier") != "HIGH_RISK", \
            "Fraud-only systems should not be classified as HIGH_RISK (Recital 58)"
        assert result.get("risk_tier") == "MINIMAL_RISK"


# ─── Internal helper tests ────────────────────────────────────────────────────

class TestObligationsHelper:

    def test_high_risk_obligations_list(self):
        from agents.classify_bot import _obligations_for_tier
        obligations = _obligations_for_tier("HIGH_RISK")
        assert len(obligations) >= 7, "HIGH_RISK systems have at least 7 obligations"

    def test_high_risk_includes_art9(self):
        from agents.classify_bot import _obligations_for_tier
        obligations = _obligations_for_tier("HIGH_RISK")
        assert any("Art. 9" in o for o in obligations), "Art. 9 must be in HIGH_RISK obligations"

    def test_high_risk_includes_art14(self):
        from agents.classify_bot import _obligations_for_tier
        obligations = _obligations_for_tier("HIGH_RISK")
        assert any("Art. 14" in o for o in obligations), "Art. 14 must be in HIGH_RISK obligations"

    def test_limited_risk_obligations_list(self):
        from agents.classify_bot import _obligations_for_tier
        obligations = _obligations_for_tier("LIMITED_RISK")
        assert any("Art. 50" in o for o in obligations), "LIMITED_RISK must include Art. 50"

    def test_prohibited_obligations_list(self):
        from agents.classify_bot import _obligations_for_tier
        obligations = _obligations_for_tier("PROHIBITED")
        assert any("Art. 5" in o for o in obligations), "PROHIBITED must include Art. 5"
