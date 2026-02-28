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
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "fria_tools.json") as f:
            tools = json.load(f)
        names = {t["name"] for t in tools}
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
        assess_tool = next(t for t in tools if t["name"] == "assess_fundamental_right")
        right_enum = assess_tool["input_schema"]["properties"]["right"].get("enum", [])
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

    def test_returns_dict(self):
        from agents.fria_agent import generate_fria

        payload = {
            "status": "DRAFT_GENERATED",
            "system": "PulseCredit v2.1",
            "rights_assessed": 6,
            "residual_risks": {
                "non_discrimination": "LOW-MEDIUM",
                "privacy_data_protection": "LOW",
                "access_to_financial_services": "MEDIUM",
                "right_to_explanation": "LOW",
                "human_dignity": "LOW",
                "freedom_from_manipulation": "LOW",
            },
        }
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(payload)
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [mock_block]

        with patch("agents.fria_agent.anthropic.Anthropic") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
            result = generate_fria(
                system_name="PulseCredit v2.1",
                affected_population="Dutch consumers aged 18-75",
            )

        assert isinstance(result, dict)

    def test_fria_covers_six_rights(self):
        from agents.fria_agent import generate_fria

        payload = {
            "status": "DRAFT_GENERATED",
            "rights_assessed": 6,
            "residual_risks": {r: "LOW" for r in EXPECTED_RIGHTS},
        }
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(payload)
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [mock_block]

        with patch("agents.fria_agent.anthropic.Anthropic") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
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
