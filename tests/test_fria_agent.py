"""
Tests for FRIAAgent — Article 27 Fundamental Rights Impact Assessment generator.

Tests verify:
  1. Tool schema validity (no API required)
  2. Agent covers all 6 required fundamental rights (mocked API)
  3. REQUIRED_RIGHTS constant is complete
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "agents" / "schemas"

EXPECTED_RIGHTS = {
    "non_discrimination",
    "privacy_data_protection",
    "access_to_financial_services",
    "right_to_explanation",
    "human_dignity",
    "freedom_from_manipulation",
}


# ─── Schema validation ────────────────────────────────────────────────────────

class TestFRIAToolSchemas:

    def test_schema_file_exists(self):
        assert (SCHEMAS_DIR / "fria_tools.json").exists()

    def test_schema_is_valid_json(self):
        with open(SCHEMAS_DIR / "fria_tools.json") as f:
            tools = json.load(f)
        assert isinstance(tools, list)

    def test_schema_has_minimum_tools(self):
        with open(SCHEMAS_DIR / "fria_tools.json") as f:
            tools = json.load(f)
        assert len(tools) >= 3

    def test_each_tool_has_required_keys(self):
        with open(SCHEMAS_DIR / "fria_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            assert tool.get("type") == "function", "Tool must have type 'function' (OpenAI format)"
            fn = tool.get("function", {})
            for key in ("name", "description", "parameters"):
                assert key in fn, f"tool['function'] missing key '{key}'"

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "fria_tools.json") as f:
            tools = json.load(f)
        names = {t["function"]["name"] for t in tools}
        expected = {
            "assess_fundamental_right",
            "propose_mitigation_measures",
            "generate_fria_report",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"

    def test_assess_right_enum_covers_required_rights(self):
        """assess_fundamental_right tool must accept all 6 required EUCFR rights."""
        with open(SCHEMAS_DIR / "fria_tools.json") as f:
            tools = json.load(f)
        assess_tool = next(
            t for t in tools if t["function"]["name"] == "assess_fundamental_right"
        )
        right_enum = (
            assess_tool["function"]["parameters"]["properties"]["right"].get("enum", [])
        )
        assert set(right_enum) >= EXPECTED_RIGHTS, \
            f"Missing rights in enum: {EXPECTED_RIGHTS - set(right_enum)}"


# ─── REQUIRED_RIGHTS constant ────────────────────────────────────────────────

class TestRequiredRightsConstant:

    def test_required_rights_covers_all_eucfr_rights(self):
        from agents.fria_agent import REQUIRED_RIGHTS
        assert set(REQUIRED_RIGHTS) >= EXPECTED_RIGHTS, \
            f"REQUIRED_RIGHTS missing: {EXPECTED_RIGHTS - set(REQUIRED_RIGHTS)}"

    def test_required_rights_has_six_entries(self):
        from agents.fria_agent import REQUIRED_RIGHTS
        assert len(REQUIRED_RIGHTS) == 6, "FRIA must assess exactly 6 fundamental rights"


# ─── Agent function tests ─────────────────────────────────────────────────────

class TestGenerateFRIA:

    def _make_response(self, payload: dict):
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = json.dumps(payload)
        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    def test_returns_dict(self):
        from agents.fria_agent import generate_fria

        mock_response = self._make_response({
            "status": "DRAFT_GENERATED",
            "system": "PulseCredit v2.1",
            "rights_assessed": 6,
            "residual_risks": {r: "LOW" for r in EXPECTED_RIGHTS},
        })

        with patch("agents.fria_agent.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = generate_fria(
                system_name="PulseCredit v2.1",
                affected_population="Dutch consumers aged 18-75",
            )

        assert isinstance(result, dict)
        assert result.get("status") == "DRAFT_GENERATED"

    def test_fria_covers_six_rights(self):
        from agents.fria_agent import generate_fria

        mock_response = self._make_response({
            "status": "DRAFT_GENERATED",
            "rights_assessed": 6,
            "residual_risks": {r: "LOW" for r in EXPECTED_RIGHTS},
        })

        with patch("agents.fria_agent.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = generate_fria(
                system_name="PulseCredit v2.1",
                affected_population="Dutch consumers",
            )

        assert result.get("rights_assessed") == 6, \
            "FRIA must cover all 6 fundamental rights"


# ─── Tool handler tests (no API) ─────────────────────────────────────────────

class TestFRIAToolHandlers:

    def test_assess_non_discrimination_returns_impact(self):
        from agents.fria_agent import _process_tool_call
        result = json.loads(_process_tool_call("assess_fundamental_right", {
            "right": "non_discrimination",
            "legal_basis": "Art. 21 EUCFR",
            "system_description": {},
            "affected_population": "Dutch consumers",
        }))
        assert result["right"] == "non_discrimination"
        assert "impact" in result["potential_impact"].lower() or len(result["potential_impact"]) > 0

    def test_propose_mitigations_for_non_discrimination(self):
        from agents.fria_agent import _process_tool_call
        result = json.loads(_process_tool_call("propose_mitigation_measures", {
            "right": "non_discrimination",
            "impact_description": "Proxy discrimination via postcode",
            "likelihood": "MEDIUM",
            "severity": "HIGH",
        }))
        assert len(result["mitigation_measures"]) > 0
