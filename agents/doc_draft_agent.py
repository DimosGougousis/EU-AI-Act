"""
DocDraftAgent — Annex IV Technical Documentation Generator

Connects to FinPulse's internal systems (MLflow model registry, data catalog)
and auto-generates a compliant Annex IV technical documentation draft.

Regulatory basis:
    - Article 11 — Technical documentation obligation
    - Annex IV   — Required content for technical documentation
    - Article 12 — Logging requirements (referenced in output)

Tools used:
    fetch_model_metadata       — MLflow registry query
    fetch_data_catalog         — Data catalog/lineage query
    populate_annex_iv_template — Maps metadata to Annex IV fields
    export_documentation_draft — Outputs draft with completion % and action items

Usage:
    result = draft_technical_documentation(
        registry_uri="mlflow://pulsecredit/v2.1.3",
        catalog_ref="datahub://credit/training-2024-q4",
        risk_tier="HIGH_RISK",
        system_owner="Dr. Elena Visser, CTO",
        target_date="2026-07-31",
        additional_context="XGBoost ensemble introduced January 2025...",
    )
"""

import json
import os
from pathlib import Path

import openai

SCHEMAS_DIR = Path(__file__).parent / "schemas"

SYSTEM_PROMPT = (
    "You are DocDraftAgent, an EU AI Act Annex IV documentation specialist. "
    "Your task is to generate a structured technical documentation draft "
    "by querying model registry and data catalog systems. "
    "Map all retrieved metadata to the corresponding Annex IV sections. "
    "Clearly flag any fields that require human completion. "
    "Aim for maximum automation — the fewer fields left for humans, the better."
)

# Mock metadata returned by internal systems in a real deployment
_MOCK_MLFLOW_METADATA = {
    "model_id": "pulsecredit-v2.1.3",
    "architecture": "XGBoost ensemble (500 trees) + Logistic Regression calibration layer",
    "framework": "XGBoost 2.0.3 + scikit-learn 1.4.0",
    "training_date": "2025-09-15",
    "auc_roc": 0.799,
    "gini": 0.598,
    "ks_statistic": 0.411,
    "psi": 0.09,
    "hyperparameters": {
        "n_estimators": 500,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
    },
    "training_records": 380000,
    "train_val_test_split": "70/15/15",
}

_MOCK_DATA_CATALOG = {
    "catalog_ref": "datahub://credit/training-2024-q4",
    "sources": [
        {"name": "BKR", "type": "credit_bureau", "records": 380000, "period": "2018-2024"},
        {"name": "PSD2 transaction feed", "type": "open_banking", "records": 247000, "period": "2022-2024"},
        {"name": "Loan application forms", "type": "user_input", "records": 380000},
    ],
    "bias_assessment": "Fairlearn v0.10 — September 2025",
    "postcode_removed": True,
    "gdpr_basis": "Art. 6(1)(b) contract necessity; Art. 9(2)(g) substantial public interest (bias testing)",
}


def _load_tools() -> list:
    with open(SCHEMAS_DIR / "doc_draft_tools.json") as f:
        return json.load(f)


def _process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "fetch_model_metadata":
        return json.dumps(_MOCK_MLFLOW_METADATA)

    if tool_name == "fetch_data_catalog":
        return json.dumps(_MOCK_DATA_CATALOG)

    if tool_name == "populate_annex_iv_template":
        populated = {
            "1_general_description": "PulseCredit v2.1 — AI credit scoring and loan origination",
            "2_system_description": "XGBoost ensemble + LR calibration for creditworthiness assessment",
            "3_training_data": "380,000 records, 2018–2024, BKR + PSD2 + application forms",
            "4_performance_metrics": (
                f"AUC-ROC: {_MOCK_MLFLOW_METADATA['auc_roc']} | "
                f"GINI: {_MOCK_MLFLOW_METADATA['gini']} | "
                f"KS: {_MOCK_MLFLOW_METADATA['ks_statistic']} | "
                f"PSI: {_MOCK_MLFLOW_METADATA['psi']}"
            ),
            "5_bias_assessment": "Fairlearn v0.10 — September 2025. Postcode feature removed.",
            "6_logging_config": "6-month retention — pending engineering implementation",
        }
        missing = [
            "Section 2.3 — Known failure modes and edge cases",
            "Section 3.4 — Post-market monitoring plan",
            "Section 4.1 — Instructions for deployers",
            "Section 5.2 — Residual risk justification",
            "Section 6.1 — Cybersecurity test results",
            "Section 7.0 — Signatory and declaration",
        ]
        return json.dumps({
            "populated_fields": populated,
            "missing_fields": missing,
            "completeness_pct": round(100 * len(populated) / (len(populated) + len(missing)), 1),
        })

    if tool_name == "export_documentation_draft":
        populated = tool_input.get("populated_fields", {})
        missing = tool_input.get("missing_fields", [])
        total = len(populated) + len(missing)
        pct = round(100 * len(populated) / total, 1) if total > 0 else 0
        return json.dumps({
            "status": "DRAFT_SAVED",
            "output_path": tool_input.get("output_path", "compliance/artifacts/pulsecredit-v2.1.3-annex-iv-draft.json"),
            "completeness_pct": pct,
            "fields_populated": len(populated),
            "fields_requiring_human_input": len(missing),
            "missing_fields": missing,
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def draft_technical_documentation(
    registry_uri: str,
    catalog_ref: str,
    risk_tier: str = "HIGH_RISK",
    system_owner: str = "",
    target_date: str = "2026-07-31",
    additional_context: str = "",
) -> dict:
    """
    Generate an Annex IV technical documentation draft for an AI system.

    Args:
        registry_uri:       MLflow model registry URI
        catalog_ref:        Data catalog reference
        risk_tier:          EU AI Act risk tier (default HIGH_RISK)
        system_owner:       Signatory name and title
        target_date:        Compliance sign-off target date (ISO 8601)
        additional_context: Free-text additional context

    Returns:
        dict: Documentation draft summary with completeness % and action items
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "test"))
    tools = _load_tools()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Generate an EU AI Act Annex IV technical documentation draft.\n"
                f"Model Registry: {registry_uri}\n"
                f"Data Catalog: {catalog_ref}\n"
                f"Risk Tier: {risk_tier}\n"
                f"System Owner: {system_owner}\n"
                f"Target Date: {target_date}\n"
                f"Additional Context: {additional_context or 'None'}"
            ),
        },
    ]

    final_result = {}

    while True:
        response = client.chat.completions.create(
            model=os.environ.get("AI_MODEL", "gpt-4o"),
            max_tokens=8096,
            tools=tools,
            messages=messages,
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            try:
                final_result = json.loads(msg.content)
            except (json.JSONDecodeError, TypeError):
                final_result = {"summary": msg.content}
            return final_result

        messages.append(msg)

        for tc in msg.tool_calls:
            result = _process_tool_call(tc.function.name, json.loads(tc.function.arguments))
            if tc.function.name == "export_documentation_draft":
                try:
                    final_result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })


if __name__ == "__main__":
    print("Running DocDraftAgent for PulseCredit v2.1.3...")
    result = draft_technical_documentation(
        registry_uri="mlflow://pulsecredit/v2.1.3",
        catalog_ref="datahub://credit/training-2024-q4",
        system_owner="Dr. Elena Visser, CTO",
        additional_context=(
            "XGBoost ensemble introduced January 2025 to improve AUC. "
            "Bias remediation applied Q4 2024 following internal audit."
        ),
    )
    print(json.dumps(result, indent=2))
