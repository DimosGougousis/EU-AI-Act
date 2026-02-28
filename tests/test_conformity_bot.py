"""
Tests for ConformityBot — Annex VI conformity assessment runner.

Tests verify:
  1. Tool schema validity (no API required)
  2. OBLIGATIONS list covers all required articles
  3. Agent function returns dict with NCRs (mocked API)
  4. Tool handlers return correct status for known Feb 2026 state
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "agents" / "schemas"

REQUIRED_ARTICLES = {"Art. 9", "Art. 10", "Art. 11", "Art. 12", "Art. 14", "Art. 27"}


# ─── Schema validation ────────────────────────────────────────────────────────

class TestConformityBotToolSchemas:

    def test_schema_file_exists(self):
        assert (SCHEMAS_DIR / "conformity_tools.json").exists()

    def test_schema_is_valid_json(self):
        with open(SCHEMAS_DIR / "conformity_tools.json") as f:
            tools = json.load(f)
        assert isinstance(tools, list)

    def test_schema_has_minimum_tools(self):
        with open(SCHEMAS_DIR / "conformity_tools.json") as f:
            tools = json.load(f)
        assert len(tools) >= 3

    def test_each_tool_has_required_keys(self):
        with open(SCHEMAS_DIR / "conformity_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            assert tool.get("type") == "function", "Tool must have type 'function' (OpenAI format)"
            fn = tool.get("function", {})
            for key in ("name", "description", "parameters"):
                assert key in fn, f"tool['function'] missing key '{key}'"

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "conformity_tools.json") as f:
            tools = json.load(f)
        names = {t["function"]["name"] for t in tools}
        expected = {
            "check_document_exists",
            "check_log_retention",
            "generate_conformity_report",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"

    def test_document_type_enum_covers_key_docs(self):
        with open(SCHEMAS_DIR / "conformity_tools.json") as f:
            tools = json.load(f)
        check_tool = next(
            t for t in tools if t["function"]["name"] == "check_document_exists"
        )
        doc_type_enum = (
            check_tool["function"]["parameters"]["properties"]["document_type"].get("enum", [])
        )
        for doc in ["risk_management_system", "technical_documentation", "fria"]:
            assert doc in doc_type_enum, f"'{doc}' missing from document_type enum"


# ─── OBLIGATIONS checklist ────────────────────────────────────────────────────

class TestObligationsChecklist:

    def test_obligations_covers_required_articles(self):
        from agents.conformity_bot import OBLIGATIONS
        articles = {o["article"] for o in OBLIGATIONS}
        missing = REQUIRED_ARTICLES - articles
        assert not missing, f"OBLIGATIONS missing articles: {missing}"

    def test_each_obligation_has_article_and_text(self):
        from agents.conformity_bot import OBLIGATIONS
        for o in OBLIGATIONS:
            assert "article" in o, "Each obligation must have an 'article' key"
            assert "obligation" in o, "Each obligation must have an 'obligation' key"
            assert len(o["obligation"]) > 5, "Obligation text must be descriptive"

    def test_minimum_eight_obligations(self):
        from agents.conformity_bot import OBLIGATIONS
        assert len(OBLIGATIONS) >= 8, "Annex VI conformity check must cover ≥8 obligations"


# ─── Agent function tests ─────────────────────────────────────────────────────

class TestRunConformityCheck:

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
        from agents.conformity_bot import run_conformity_check

        mock_response = self._make_response({
            "status": "REPORT_GENERATED",
            "overall_score": 15.0,
            "ncr_count": 4,
            "ncrs": [{"id": "NCR-001", "article": "Art. 12", "status": "FAIL"}],
        })

        with patch("agents.conformity_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = run_conformity_check()

        assert isinstance(result, dict)
        assert result.get("status") == "REPORT_GENERATED"

    def test_ncr_count_reflects_gaps(self):
        from agents.conformity_bot import run_conformity_check

        mock_response = self._make_response({
            "status": "REPORT_GENERATED",
            "overall_score": 15.0,
            "ncr_count": 4,
            "ncrs": [
                {"id": "NCR-001", "article": "Art. 12", "obligation": "Logging retention", "status": "FAIL"},
                {"id": "NCR-002", "article": "Art. 11", "obligation": "Technical docs", "status": "PARTIAL"},
                {"id": "NCR-003", "article": "Art. 15", "obligation": "Robustness testing", "status": "FAIL"},
                {"id": "NCR-004", "article": "Art. 14", "obligation": "HITL deployed", "status": "FAIL"},
            ],
        })

        with patch("agents.conformity_bot.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = run_conformity_check()

        assert result.get("ncr_count") == 4, "Feb 2026 baseline should have 4 NCRs"
        assert result.get("overall_score") == 15.0, "Feb 2026 baseline score must be 15%"


# ─── Tool handler tests (no API) ─────────────────────────────────────────────

class TestConformityToolHandlers:

    def test_log_retention_check_fails_at_30_days(self):
        """Feb 2026 state: log retention is 30 days, minimum is 183 days."""
        from agents.conformity_bot import _process_tool_call
        result = json.loads(_process_tool_call("check_log_retention", {
            "log_endpoint": "https://logs.internal.finpulse.nl/",
            "system_id": "pulsecredit-v2.1",
        }))
        assert result["compliant"] is False
        assert result["configured_retention_days"] < result["required_retention_days"]

    def test_risk_management_system_absent(self):
        """Feb 2026 state: risk management system document does not exist."""
        from agents.conformity_bot import _process_tool_call
        result = json.loads(_process_tool_call("check_document_exists", {
            "document_type": "risk_management_system",
            "repository_path": "sharepoint://compliance/eu-ai-act/pulsecredit/",
        }))
        assert result["status"] == "FAIL"
        assert result["exists"] is False

    def test_technical_documentation_partial(self):
        """Feb 2026 state: Annex IV documentation is 50% complete."""
        from agents.conformity_bot import _process_tool_call
        result = json.loads(_process_tool_call("check_document_exists", {
            "document_type": "technical_documentation",
            "repository_path": "sharepoint://compliance/eu-ai-act/pulsecredit/",
        }))
        assert result["status"] == "PARTIAL"
        assert result["completeness"] < 80
