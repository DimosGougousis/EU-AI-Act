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
        required_keys = {"name", "description", "input_schema"}
        for tool in tools:
            missing = required_keys - set(tool.keys())
            assert not missing, f"Tool '{tool.get('name', '?')}' missing keys: {missing}"

    def test_input_schema_is_object_type(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            schema = tool.get("input_schema", {})
            assert schema.get("type") == "object", \
                f"Tool '{tool['name']}' input_schema.type must be 'object'"

    def test_tool_names_are_unique(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        names = [t["name"] for t in tools]
        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
            tools = json.load(f)
        names = {t["name"] for t in tools}
        expected = {"check_annex_iii", "check_fraud_exemption", "generate_classification_report"}
        missing = expected - names
        assert not missing, f"Expected tools not found: {missing}"


# ─── Agent function tests (mocked API) ────────────────────────────────────────

class TestClassifySystemFunction:

    def test_returns_dict(self, sample_ai_system_description):
        """classify_system() must return a dict even with mocked API."""
        from agents.classify_bot import classify_system

        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps({
            "risk_tier": "HIGH_RISK",
            "legal_basis": "Annex III, Point 5(b)",
            "confidence": 0.97,
        })
        mock_response = MagicMock()
        mock_message = MagicMock(); message.tool_calls = None; message.content = json.dumps(payload); choice = MagicMock(); choice.finish_reason = "stop"; choice.message = message; mock_response.choices = [choice]
        mock_response.content = [mock_block]

        with patch("agents.classify_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
            result = classify_system(sample_ai_system_description)

        assert isinstance(result, dict), "classify_system must return a dict"

    def test_high_risk_system_classified_correctly(self, sample_ai_system_description):
        """PulseCredit should be classified as HIGH_RISK."""
        from agents.classify_bot import classify_system

        expected_payload = {
            "risk_tier": "HIGH_RISK",
            "legal_basis": "Annex III, Point 5(b)",
            "confidence": 0.97,
        }
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(expected_payload)
        mock_response = MagicMock()
        mock_message = MagicMock(); message.tool_calls = None; message.content = json.dumps(payload); choice = MagicMock(); choice.finish_reason = "stop"; choice.message = message; mock_response.choices = [choice]
        mock_response.content = [mock_block]

        with patch("agents.classify_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
            result = classify_system(sample_ai_system_description)

        assert result.get("risk_tier") == "HIGH_RISK"

    def test_fraud_system_exemption_handling(self, sample_fraud_system_description):
        """Fraud-only system should not be HIGH_RISK (Recital 58 exemption)."""
        from agents.classify_bot import classify_system

        expected_payload = {
            "risk_tier": "MINIMAL_RISK",
            "legal_basis": "Recital 58 — Fraud detection exemption",
            "confidence": 0.90,
        }
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(expected_payload)
        mock_response = MagicMock()
        mock_message = MagicMock(); message.tool_calls = None; message.content = json.dumps(payload); choice = MagicMock(); choice.finish_reason = "stop"; choice.message = message; mock_response.choices = [choice]
        mock_response.content = [mock_block]

        with patch("agents.classify_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
            result = classify_system(sample_fraud_system_description)

        assert result.get("risk_tier") != "HIGH_RISK", \
            "Fraud-only systems should not be classified as HIGH_RISK (Recital 58)"


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
