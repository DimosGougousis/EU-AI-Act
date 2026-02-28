"""
Shared pytest fixtures for EU AI Act compliance agent tests.

All fixtures are designed to work WITHOUT a live OPENAI_API_KEY.
The LLM client is mocked to return pre-canned responses.
"""

import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_ai_system_description():
    """Realistic PulseCredit system description for ClassifyBot tests."""
    return {
        "name": "PulseCredit v2.1",
        "purpose": (
            "Evaluates the creditworthiness of Dutch consumers and produces "
            "a credit score (0-100) and a recommended lending decision "
            "(Approve/Refer/Decline) for consumer loan applications."
        ),
        "inputs": [
            "BKR credit history",
            "PSD2 bank transaction data (24 months)",
            "Loan application form data (income, employment)",
        ],
        "outputs": [
            "Credit score 0-100",
            "Approve / Refer / Decline recommendation",
        ],
        "deployment_context": "Consumer Credit Provider (Wft licence), Netherlands",
        "sole_purpose_fraud": False,
    }


@pytest.fixture
def sample_fraud_system_description():
    """Fraud-only system that should qualify for Recital 58 exemption."""
    return {
        "name": "FraudShield v1.0",
        "purpose": "Detects fraudulent payment transactions in real-time to prevent financial crime.",
        "inputs": ["Transaction data", "Device fingerprint", "Behavioural signals"],
        "outputs": ["Fraud probability score", "Block/Allow/Review decision"],
        "deployment_context": "Payment Institution (PSD2), Netherlands",
        "sole_purpose_fraud": True,
    }


@pytest.fixture
def sample_model_card():
    """MLflow model card for DocDraftAgent tests."""
    return {
        "registry_uri": "mlflow://pulsecredit/v2.1.3",
        "catalog_ref": "datahub://credit/training-2024-q4",
        "system_owner": "Dr. Elena Visser, CTO",
        "target_date": "2026-07-31",
        "additional_context": "XGBoost ensemble introduced January 2025.",
    }


def _make_llm_response(json_payload: dict):
    """
    Build a mock chat.completions response that returns no tool calls
    and a JSON content string — simulating a final answer turn.
    """
    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = json.dumps(json_payload)

    mock_choice = MagicMock()
    mock_choice.finish_reason = "stop"
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def mock_llm_final_response():
    """
    Factory fixture: returns a mock LLM response with no tool_calls
    and a JSON content string (final answer, no further tool use).
    """
    return _make_llm_response


@pytest.fixture
def mock_llm_client():
    """
    Mock LLM client (openai.OpenAI()) that immediately returns a final
    answer with a minimal valid payload. Patches at the module level.
    """
    client = MagicMock()
    client.chat.completions.create.return_value = _make_llm_response(
        {"risk_tier": "HIGH_RISK", "legal_basis": "Annex III, Point 5(b)"}
    )
    return client
