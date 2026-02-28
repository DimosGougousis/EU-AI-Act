"""
Shared pytest fixtures for EU AI Act compliance agent tests.

All fixtures are designed to work WITHOUT a live ANTHROPIC_API_KEY.
The Anthropic client is mocked to return pre-canned tool call responses.
"""

import json
from unittest.mock import MagicMock, patch

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


@pytest.fixture
def mock_anthropic_end_turn_response():
    """
    Factory fixture: returns a mock Anthropic response with stop_reason='end_turn'
    and a JSON text block.
    """
    def _make_response(json_payload: dict):
        block = MagicMock()
        block.type = "text"
        block.text = json.dumps(json_payload)
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [block]
        return response
    return _make_response


@pytest.fixture
def mock_anthropic_client(mock_anthropic_end_turn_response):
    """
    Mock anthropic.Anthropic() client that immediately returns end_turn
    with a minimal valid payload. Patches the client at the module level.
    """
    client = MagicMock()
    client.messages.create.return_value = mock_anthropic_end_turn_response(
        {"risk_tier": "HIGH_RISK", "legal_basis": "Annex III, Point 5(b)"}
    )
    return client
