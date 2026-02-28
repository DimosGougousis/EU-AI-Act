"""
ClassifyBot — EU AI Act Risk-Tier Classification Agent

Classifies AI systems against the EU AI Act (Regulation 2024/1689) four-tier
risk framework using an agentic loop with tool use.

Regulatory basis:
    - Article 5   — Prohibited AI practices
    - Article 6   — Classification rules for high-risk systems
    - Annex III   — High-risk AI system categories
    - Recital 58  — Fraud detection exemption

Tools used:
    check_prohibited_practices  — Article 5 screen
    check_annex_iii             — Annex III matching
    check_fraud_exemption       — Recital 58 evaluation
    generate_classification_report — Final structured report

Usage:
    result = classify_system({
        "name": "PulseCredit v2.1",
        "purpose": "Evaluates creditworthiness of Dutch consumers...",
        "inputs": ["BKR credit history", "PSD2 transactions"],
        "outputs": ["credit score", "Approve/Refer/Decline recommendation"],
        "deployment_context": "Consumer Credit Provider (Wft licence)",
        "sole_purpose_fraud": False,
    })
"""

import json
import os
from pathlib import Path

import openai

SCHEMAS_DIR = Path(__file__).parent / "schemas"

SYSTEM_PROMPT = (
    "You are ClassifyBot, an EU AI Act risk-tier classification expert. "
    "Systematically classify AI systems using the four-tier risk framework "
    "(Prohibited → High-Risk → Limited-Risk → Minimal-Risk). "
    "Always cite specific articles and annexes. "
    "Screen for Article 5 prohibited practices first. "
    "Then check Annex III. "
    "Then evaluate Recital 58 fraud exemption if relevant. "
    "Return a structured JSON classification report."
)


def _load_tools() -> list:
    with open(SCHEMAS_DIR / "classify_bot_tools.json") as f:
        return json.load(f)


def _process_tool_call(tool_name: str, tool_input: dict) -> str:
    """
    Stub tool executor. In production, each tool connects to real data sources.
    Returns mock responses sufficient for demonstrating the agentic loop.
    """
    if tool_name == "check_prohibited_practices":
        return json.dumps({"result": "PASSED", "prohibited_matches": []})

    if tool_name == "check_annex_iii":
        purpose = tool_input.get("system_purpose", "").lower()
        context = tool_input.get("deployment_context", "").lower()
        if "credit" in purpose or "creditworthiness" in purpose or "loan" in purpose:
            return json.dumps({
                "match_found": True,
                "category": "Annex III, Point 5(b)",
                "citation": (
                    "AI systems intended to be used to evaluate the creditworthiness "
                    "of natural persons or establish their credit score"
                ),
                "confidence": 0.97,
            })
        if "fraud" in purpose and "credit" not in context:
            return json.dumps({
                "match_found": False,
                "note": "Possible Recital 58 fraud exemption — check_fraud_exemption",
            })
        return json.dumps({"match_found": False, "note": "No direct Annex III match"})

    if tool_name == "check_fraud_exemption":
        sole = tool_input.get("sole_purpose_fraud", False)
        return json.dumps({
            "exemption_applies": sole,
            "reasoning": (
                "Recital 58 exemption applies only when fraud/AML detection "
                "is the sole primary purpose."
            ) if not sole else (
                "Recital 58 exemption applies — system is solely for fraud detection."
            ),
        })

    if tool_name == "generate_classification_report":
        tier = tool_input.get("risk_tier", "UNKNOWN")
        basis = tool_input.get("legal_basis", "Unknown")
        return json.dumps({
            "risk_tier": tier,
            "legal_basis": basis,
            "confidence": tool_input.get("confidence", 0.9),
            "obligations": _obligations_for_tier(tier),
            "deadline": "2026-08-02",
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def _obligations_for_tier(tier: str) -> list:
    if tier == "HIGH_RISK":
        return [
            "Art. 9 — Risk Management System",
            "Art. 10 — Data Governance",
            "Art. 11 + Annex IV — Technical Documentation",
            "Art. 12 — Logging (min. 6 months)",
            "Art. 13 — Transparency / Instructions for Use",
            "Art. 14 — Human Oversight",
            "Art. 15 — Accuracy, Robustness, Cybersecurity",
            "Art. 43 — Conformity Assessment (Annex VI)",
            "Art. 27 — Fundamental Rights Impact Assessment",
        ]
    if tier == "LIMITED_RISK":
        return ["Art. 50 — Transparency obligations (chatbot disclosure)"]
    if tier == "PROHIBITED":
        return ["Art. 5 — System must not be deployed"]
    return []


def classify_system(system_description: dict) -> dict:
    """
    Classify an AI system under the EU AI Act risk-tier framework.

    Args:
        system_description: Dict with keys:
            name (str): System name and version
            purpose (str): Plain-language description of the system's purpose
            inputs (list[str]): Data inputs
            outputs (list[str]): System outputs and their use
            deployment_context (str): Regulatory/sector context
            sole_purpose_fraud (bool): Whether fraud detection is the sole purpose

    Returns:
        dict: Classification report with risk_tier, legal_basis, obligations, confidence
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "test"))
    tools = _load_tools()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Classify this AI system under EU AI Act (2024/1689): "
                f"{json.dumps(system_description, indent=2)}"
            ),
        },
    ]

    final_report = {}

    while True:
        response = client.chat.completions.create(
            model=os.environ.get("AI_MODEL", "gpt-4o"),
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            try:
                final_report = json.loads(msg.content)
            except (json.JSONDecodeError, TypeError):
                final_report = {"raw_output": msg.content}
            return final_report

        # Append assistant message (contains tool_calls)
        messages.append(msg)

        for tc in msg.tool_calls:
            result = _process_tool_call(tc.function.name, json.loads(tc.function.arguments))
            if tc.function.name == "generate_classification_report":
                try:
                    final_report = json.loads(result)
                except json.JSONDecodeError:
                    pass
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })


if __name__ == "__main__":
    sample = {
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

    print("Running ClassifyBot on PulseCredit v2.1...")
    result = classify_system(sample)
    print(json.dumps(result, indent=2))
