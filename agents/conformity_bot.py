"""
ConformityBot — Annex VI Conformity Assessment Runner

Automated conformity assessment agent. Queries internal systems,
documentation repositories, and operational logs to verify that all
Article 16 EU AI Act obligations are met.

Regulatory basis:
    - Article 43    — Conformity assessment procedure
    - Article 16    — Obligations of providers of high-risk AI systems
    - Annex VI      — Internal control conformity assessment
    - Article 12    — Logging obligations (6-month minimum)
    - Article 14    — Human oversight obligations

Articles checked:
    Art. 9  — Risk Management System
    Art. 10 — Data Governance (bias assessment)
    Art. 11 — Technical Documentation (Annex IV)
    Art. 12 — Logging and record-keeping
    Art. 13 — Transparency and instructions for use
    Art. 14 — Human oversight mechanisms
    Art. 15 — Accuracy, robustness, cybersecurity
    Art. 27 — Fundamental Rights Impact Assessment

Usage:
    result = run_conformity_check(
        system_id="pulsecredit-v2.1",
        repository_path="sharepoint://compliance/eu-ai-act/pulsecredit/",
        log_endpoint="https://logs.internal.finpulse.nl/api/ai-decisions/",
        assessment_type="Full Annex VI Assessment",
    )
"""

import json
import os
from pathlib import Path

import anthropic

SCHEMAS_DIR = Path(__file__).parent / "schemas"

SYSTEM_PROMPT = (
    "You are ConformityBot, an EU AI Act Annex VI conformity assessment specialist. "
    "Systematically verify each Article 16 obligation by checking document existence, "
    "log retention, and oversight implementation. "
    "For each check: document the evidence found, assign status (PASS/PARTIAL/FAIL), "
    "and record notes. "
    "Calculate the overall conformity score as percentage of obligations met. "
    "Generate a structured conformity report with all Non-Conformity Reports (NCRs)."
)

# Article obligations checklist (Annex VI scope)
OBLIGATIONS = [
    {"article": "Art. 9", "obligation": "Risk Management System documented and operational"},
    {"article": "Art. 10", "obligation": "Data governance policy and bias assessment completed"},
    {"article": "Art. 11", "obligation": "Annex IV technical documentation complete (>80%)"},
    {"article": "Art. 12", "obligation": "Logging configured with ≥6-month retention"},
    {"article": "Art. 13", "obligation": "Instructions for use provided to deployers"},
    {"article": "Art. 14", "obligation": "Human oversight (HITL) mechanism deployed"},
    {"article": "Art. 15", "obligation": "Accuracy and robustness testing conducted"},
    {"article": "Art. 27", "obligation": "Fundamental Rights Impact Assessment completed"},
]


def _load_tools() -> list:
    with open(SCHEMAS_DIR / "conformity_tools.json") as f:
        return json.load(f)


def _process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "check_document_exists":
        doc_type = tool_input.get("document_type", "")
        # Simulate Feb 2026 baseline state from conformity assessment (Artifact 11)
        states = {
            "risk_management_system": {
                "exists": False,
                "completeness": 0,
                "status": "FAIL",
                "notes": "No risk register located in repository. Action required immediately.",
            },
            "technical_documentation": {
                "exists": True,
                "completeness": 50,
                "status": "PARTIAL",
                "notes": "14/28 Annex IV items populated. Missing: failure modes, instructions for use.",
            },
            "bias_assessment": {
                "exists": False,
                "completeness": 0,
                "status": "FAIL",
                "notes": "No formal bias test report found in repository.",
            },
            "fria": {
                "exists": False,
                "completeness": 0,
                "status": "FAIL",
                "notes": "FRIA not initiated. Required before deployment.",
            },
            "conformity_declaration": {
                "exists": False,
                "completeness": 0,
                "status": "FAIL",
                "notes": "Declaration of Conformity not yet issued.",
            },
            "human_oversight_procedure": {
                "exists": True,
                "completeness": 40,
                "status": "PARTIAL",
                "notes": "Loans >€5k reviewed by loan officers. Override logging absent.",
            },
            "logging_configuration": {
                "exists": True,
                "completeness": 100,
                "status": "FAIL",
                "notes": "Logging active but retention configured at 30 days (minimum: 183 days).",
            },
        }
        result = states.get(doc_type, {
            "exists": False, "completeness": 0,
            "status": "FAIL", "notes": "Document type not recognised",
        })
        return json.dumps(result)

    if tool_name == "check_log_retention":
        return json.dumps({
            "configured_retention_days": 30,
            "required_retention_days": tool_input.get("required_retention_days", 183),
            "compliant": False,
            "gap_days": 153,
            "status": "FAIL",
            "notes": "Retention 5x below minimum. Engineering ticket NCR-001 raised.",
        })

    if tool_name == "verify_oversight_implementation":
        checks = tool_input.get("checks", [])
        results = {}
        check_states = {
            "override_mechanism_present": True,
            "override_logging_active": False,
            "shap_explanation_displayed": False,
            "training_records_complete": False,
            "hitl_workflow_deployed": False,
        }
        for check in checks:
            results[check] = check_states.get(check, False)
        passed = sum(1 for v in results.values() if v)
        return json.dumps({
            "checks": results,
            "passed": passed,
            "total": len(checks),
            "status": "PARTIAL" if passed > 0 else "FAIL",
        })

    if tool_name == "generate_conformity_report":
        check_results = tool_input.get("check_results", [])
        overall_score = tool_input.get("overall_score", 15)
        ncrs = [r for r in check_results if r.get("status") in ("FAIL", "PARTIAL")]
        return json.dumps({
            "status": "REPORT_GENERATED",
            "output_path": tool_input.get("output_path", "compliance/reports/conformity-check.json"),
            "overall_score": overall_score,
            "total_obligations": len(check_results),
            "obligations_met": sum(1 for r in check_results if r.get("status") == "PASS"),
            "ncr_count": len(ncrs),
            "ncrs": [
                {
                    "id": f"NCR-{str(i+1).zfill(3)}",
                    "article": r.get("article"),
                    "obligation": r.get("obligation"),
                    "status": r.get("status"),
                    "notes": r.get("notes", ""),
                }
                for i, r in enumerate(ncrs)
            ],
            "assessment_date": "2026-02-28",
            "next_assessment": "2026-04-01",
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_conformity_check(
    system_id: str = "pulsecredit-v2.1",
    repository_path: str = "sharepoint://compliance/eu-ai-act/pulsecredit/",
    log_endpoint: str = "https://logs.internal.finpulse.nl/api/ai-decisions/",
    assessment_type: str = "Monthly Spot Check",
    articles: list | None = None,
) -> dict:
    """
    Run an Annex VI conformity assessment for a high-risk AI system.

    Args:
        system_id:        AI system identifier
        repository_path:  Compliance document repository path
        log_endpoint:     Logging system API endpoint
        assessment_type:  Type of assessment (Monthly Spot Check / Full Annex VI / etc.)
        articles:         List of articles to check (default: all)

    Returns:
        dict: Conformity report with per-article status, NCRs, and overall score
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "test"))
    tools = _load_tools()

    target_articles = articles or [o["article"] for o in OBLIGATIONS]
    obligations_str = "\n".join(
        f"  - {o['article']}: {o['obligation']}"
        for o in OBLIGATIONS
        if o["article"] in target_articles
    )

    messages = [{
        "role": "user",
        "content": (
            f"Run a {assessment_type} conformity assessment for {system_id}.\n"
            f"Repository: {repository_path}\n"
            f"Logging system: {log_endpoint}\n\n"
            f"Check all of the following obligations:\n{obligations_str}\n\n"
            f"For each obligation: check if the required document/evidence exists, "
            f"verify log retention, verify oversight implementation. "
            f"Then generate a complete conformity report with NCRs and overall score."
        ),
    }]

    final_result = {}

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8096,
            tools=tools,
            messages=messages,
            system=SYSTEM_PROMPT,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    try:
                        final_result = json.loads(block.text)
                    except (json.JSONDecodeError, AttributeError):
                        final_result = {"summary": block.text}
            return final_result

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _process_tool_call(block.name, block.input)
                if block.name == "generate_conformity_report":
                    try:
                        final_result = json.loads(result)
                    except json.JSONDecodeError:
                        pass
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    print("Running ConformityBot — Full Annex VI Assessment — PulseCredit v2.1...")
    result = run_conformity_check(assessment_type="Full Annex VI Assessment")
    print(json.dumps(result, indent=2))
