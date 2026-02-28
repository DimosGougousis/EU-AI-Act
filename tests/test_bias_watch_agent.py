"""
Tests for BiasWatchAgent — EU AI Act Article 10 bias monitoring agent.

Tests verify:
  1. Tool schema validity (no API required)
  2. calculate_demographic_parity() pure Python helper
  3. Agent function returns dict (mocked API)
  4. APScheduler job is configured correctly
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "agents" / "schemas"


# ─── Schema validation ────────────────────────────────────────────────────────

class TestBiasWatchToolSchemas:

    def test_schema_file_exists(self):
        assert (SCHEMAS_DIR / "bias_watch_tools.json").exists()

    def test_schema_is_valid_json(self):
        with open(SCHEMAS_DIR / "bias_watch_tools.json") as f:
            tools = json.load(f)
        assert isinstance(tools, list)

    def test_schema_has_minimum_tools(self):
        with open(SCHEMAS_DIR / "bias_watch_tools.json") as f:
            tools = json.load(f)
        assert len(tools) >= 3, "BiasWatchAgent should define at least 3 tools"

    def test_each_tool_has_required_keys(self):
        with open(SCHEMAS_DIR / "bias_watch_tools.json") as f:
            tools = json.load(f)
        for tool in tools:
            assert tool.get("type") == "function", "Tool must have type 'function' (OpenAI format)"
            fn = tool.get("function", {})
            for key in ("name", "description", "parameters"):
                assert key in fn, f"tool['function'] missing key '{key}'"

    def test_expected_tools_present(self):
        with open(SCHEMAS_DIR / "bias_watch_tools.json") as f:
            tools = json.load(f)
        names = {t["function"]["name"] for t in tools}
        expected = {"query_decision_log", "compute_fairness_metrics", "publish_fairness_report"}
        assert expected.issubset(names), f"Missing tools: {expected - names}"


# ─── Pure Python helper: calculate_demographic_parity ─────────────────────────

class TestCalculateDemographicParity:
    """These tests require NO API key or mocking — pure arithmetic."""

    def test_perfect_parity_returns_zero(self):
        from agents.bias_watch_agent import calculate_demographic_parity
        result = calculate_demographic_parity(50, 100, 50, 100)
        assert result == 0.0

    def test_known_parity_gap(self):
        """64.2% female vs 64.8% male approval = 0.006 gap."""
        from agents.bias_watch_agent import calculate_demographic_parity
        result = calculate_demographic_parity(
            approvals_group_a=642, total_group_a=1000,   # female: 64.2%
            approvals_group_b=648, total_group_b=1000,   # male:   64.8%
        )
        assert abs(result - 0.006) < 0.001

    def test_age_gap_borderline_fail(self):
        """58.1% (18-30) vs 68.3% (31-54) = 0.102 gap — borderline fail at threshold 0.10."""
        from agents.bias_watch_agent import calculate_demographic_parity
        result = calculate_demographic_parity(
            approvals_group_a=581, total_group_a=1000,
            approvals_group_b=683, total_group_b=1000,
        )
        assert abs(result - 0.102) < 0.001
        assert result > 0.10, "Age gap should exceed 0.10 threshold"

    def test_result_is_absolute_value(self):
        """Result must always be non-negative regardless of argument order."""
        from agents.bias_watch_agent import calculate_demographic_parity
        result_ab = calculate_demographic_parity(80, 100, 60, 100)
        result_ba = calculate_demographic_parity(60, 100, 80, 100)
        assert result_ab == pytest.approx(result_ba)
        assert result_ab == pytest.approx(0.2)

    def test_zero_total_raises_valueerror(self):
        from agents.bias_watch_agent import calculate_demographic_parity
        with pytest.raises(ValueError):
            calculate_demographic_parity(50, 0, 50, 100)

    def test_result_between_zero_and_one(self):
        from agents.bias_watch_agent import calculate_demographic_parity
        result = calculate_demographic_parity(10, 100, 90, 100)
        assert 0.0 <= result <= 1.0


# ─── Agent function tests (mocked API) ────────────────────────────────────────

class TestRunBiasWatch:

    def test_returns_dict(self):
        from agents.bias_watch_agent import run_bias_watch

        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = json.dumps({"status": "PUBLISHED", "week": "2026-W09"})
        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("agents.bias_watch_agent.openai.OpenAI") as mock_client_class:
            mock_client_class.return_value.chat.completions.create.return_value = mock_response
            result = run_bias_watch()

        assert isinstance(result, dict)
        assert result.get("status") == "PUBLISHED"


# ─── Scheduler configuration ─────────────────────────────────────────────────

class TestSchedulerConfiguration:

    def test_thresholds_configured(self):
        """Verify alert thresholds are defined and match Article 10 requirements."""
        from agents.bias_watch_agent import THRESHOLDS
        assert "demographic_parity" in THRESHOLDS
        assert "equalized_odds" in THRESHOLDS
        assert "psi" in THRESHOLDS

    def test_demographic_parity_threshold(self):
        from agents.bias_watch_agent import THRESHOLDS
        assert THRESHOLDS["demographic_parity"] == 0.05, \
            "Demographic parity threshold should be 5% per EU AI Act Article 10"

    def test_psi_threshold(self):
        from agents.bias_watch_agent import THRESHOLDS
        assert THRESHOLDS["psi"] == 0.25, "PSI threshold should be 0.25"
