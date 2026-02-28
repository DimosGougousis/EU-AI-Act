"""
Tests for DocDraftAgent — Annex IV technical documentation generator.

Tests verify:
  1. Tool schema validity (no API required)
  2. Agent function returns dict with expected keys (mocked API)
  3. Mock metadata structures are internally consistent
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "agents" / "schemas"


# ─── Schema validation ────────────────────────────────────────────────────────

class TestDocDraftToolSchemas:

    def test_schema_file_exists(self):
        assert (SCHEMAS_DIR / "doc_draft_tools.json").exists()

    def test_schema_is_valid_json(self):
        with open(SCHEMAS_DIR / "doc_draft_tools.json") as f:
            tools = json.load(f)
        assert isinstance(tools, list)

    def test_schema_has_minimum_tools(self):
        with open(SCHEMAS_DIR / "doc_draft_tools.json") as f:
            tools = json.load(f)
        assert len(tools) >= 3

    def test_each_tool_has_required_keys(self):
        with open(SCHEMAS_DIR / "doc_draft_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "doc_draft_tools.json") as f:
            tools = json.load(f)
        names = {t["name"] for t in tools}
        expected = {
            "fetch_model_metadata",
            "fetch_data_catalog",
            "populate_annex_iv_template",
            "export_documentation_draft",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"


# ─── Agent function tests ─────────────────────────────────────────────────────

class TestDraftTechnicalDocumentation:

    def test_returns_dict(self, sample_model_card):
        from agents.doc_draft_agent import draft_technical_documentation

        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps({
            "status": "DRAFT_SAVED",
            "completeness_pct": 78.0,
            "fields_populated": 22,
            "fields_requiring_human_input": 6,
        })
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [mock_block]

        with patch("agents.doc_draft_agent.anthropic.Anthropic") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
            result = draft_technical_documentation(**sample_model_card)

        assert isinstance(result, dict)

    def test_returns_completeness_pct(self, sample_model_card):
        from agents.doc_draft_agent import draft_technical_documentation

        payload = {
            "status": "DRAFT_SAVED",
            "completeness_pct": 78.0,
            "fields_populated": 22,
            "fields_requiring_human_input": 6,
        }
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(payload)
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [mock_block]

        with patch("agents.doc_draft_agent.anthropic.Anthropic") as mock_client_class:
            mock_client_class.return_value.messages.create.return_value = mock_response
            result = draft_technical_documentation(**sample_model_card)

        assert "completeness_pct" in result
        assert 0 <= result["completeness_pct"] <= 100


# ─── Mock metadata consistency ─────────────────────────────────────────────────

class TestMockMetadata:
    """Verify internal mock metadata is self-consistent (no API required)."""

    def test_mlflow_metadata_has_performance_metrics(self):
        from agents.doc_draft_agent import _MOCK_MLFLOW_METADATA
        assert "auc_roc" in _MOCK_MLFLOW_METADATA
        assert "gini" in _MOCK_MLFLOW_METADATA
        assert "ks_statistic" in _MOCK_MLFLOW_METADATA
        assert "psi" in _MOCK_MLFLOW_METADATA

    def test_auc_roc_in_valid_range(self):
        from agents.doc_draft_agent import _MOCK_MLFLOW_METADATA
        auc = _MOCK_MLFLOW_METADATA["auc_roc"]
        assert 0.5 <= auc <= 1.0, "AUC-ROC must be between 0.5 and 1.0"

    def test_training_records_positive(self):
        from agents.doc_draft_agent import _MOCK_MLFLOW_METADATA
        assert _MOCK_MLFLOW_METADATA["training_records"] > 0

    def test_data_catalog_has_gdpr_basis(self):
        from agents.doc_draft_agent import _MOCK_DATA_CATALOG
        assert "gdpr_basis" in _MOCK_DATA_CATALOG

    def test_postcode_removed_in_v2(self):
        from agents.doc_draft_agent import _MOCK_DATA_CATALOG
        assert _MOCK_DATA_CATALOG["postcode_removed"] is True, \
            "Postcode feature should be removed in v2.1 bias remediation"
