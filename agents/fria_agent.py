"""
FRIAAgent — Fundamental Rights Impact Assessment Generator

Generates structured Article 27 FRIA drafts for new AI system deployments
or significant updates. Cross-references GDPR DPIA findings.

Regulatory basis:
    - Article 27     — Fundamental Rights Impact Assessment
    - EU Charter of Fundamental Rights (EUCFR)
    - GDPR Article 35 — DPIA (cross-referenced)

Fundamental rights assessed:
    1. Non-discrimination & Equality (Art. 21 EUCFR)
    2. Privacy & Data Protection (Art. 8 EUCFR / GDPR)
    3. Access to Essential Services / Financial Inclusion (Art. 34 EUCFR)
    4. Right to Explanation & Effective Remedy (Art. 47 EUCFR; GDPR Art. 22)
    5. Human Dignity (Art. 1 EUCFR)
    6. Freedom from Manipulation (Art. 1 & 8 EUCFR)

Usage:
    result = generate_fria(
        system_name="PulseCredit v2.1",
        affected_population="Dutch consumers aged 18-75, ~18,000 applications/year",
        risk_tier="HIGH_RISK",
        dpia_reference="DPIA-2025-003",
        sensitive_groups=["ethnic_minorities", "thin_file", "young_adults"],
    )
"""

import json
import os
from pathlib import Path

import anthropic

SCHEMAS_DIR = Path(__file__).parent / "schemas"

SYSTEM_PROMPT = (
    "You are FRIAAgent, an EU AI Act Article 27 Fundamental Rights Impact Assessment specialist. "
    "Systematically assess each fundamental right under the EU Charter of Fundamental Rights. "
    "For each right: identify potential impacts, assess likelihood and severity, "
    "propose proportionate mitigations, and determine residual risk. "
    "Always cross-reference with the GDPR DPIA where provided. "
    "Required rights to assess: non_discrimination, privacy_data_protection, "
    "access_to_financial_services, right_to_explanation, human_dignity, freedom_from_manipulation."
)

REQUIRED_RIGHTS = [
    "non_discrimination",
    "privacy_data_protection",
    "access_to_financial_services",
    "right_to_explanation",
    "human_dignity",
    "freedom_from_manipulation",
]


def _load_tools() -> list:
    with open(SCHEMAS_DIR / "fria_tools.json") as f:
        return json.load(f)


def _process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "assess_fundamental_right":
        right = tool_input.get("right", "")
        impacts = {
            "non_discrimination": {
                "impact": "Proxy discrimination via historical credit data encoding past lending bias",
                "likelihood": "MEDIUM",
                "severity": "HIGH",
            },
            "privacy_data_protection": {
                "impact": "Extensive personal data processing (BKR, PSD2, income) for automated credit decision",
                "likelihood": "LOW",
                "severity": "MEDIUM",
            },
            "access_to_financial_services": {
                "impact": "Thin-file applicants may be systematically excluded regardless of actual creditworthiness",
                "likelihood": "HIGH",
                "severity": "MEDIUM",
            },
            "right_to_explanation": {
                "impact": "Applicants receiving AI-influenced decisions have a legal right to explanation",
                "likelihood": "HIGH",
                "severity": "HIGH",
            },
            "human_dignity": {
                "impact": "Fully automated decline without human consideration may be experienced as dehumanising",
                "likelihood": "LOW",
                "severity": "MEDIUM",
            },
            "freedom_from_manipulation": {
                "impact": "Credit eligibility nudges may push applicants toward credit they would not otherwise seek",
                "likelihood": "MEDIUM",
                "severity": "MEDIUM",
            },
        }
        assessment = impacts.get(right, {"impact": "Unknown right", "likelihood": "UNKNOWN", "severity": "UNKNOWN"})
        return json.dumps({
            "right": right,
            "legal_basis": tool_input.get("legal_basis"),
            "potential_impact": assessment["impact"],
            "likelihood": assessment["likelihood"],
            "severity": assessment["severity"],
        })

    if tool_name == "propose_mitigation_measures":
        right = tool_input.get("right", "")
        mitigations = {
            "non_discrimination": [
                "Postcode feature removed (v2.1 bias remediation)",
                "Weekly BiasWatchAgent demographic parity monitoring",
                "Fairness constraint in training (exponentiated gradient)",
                "Mandatory manual review for applicants aged 18-25",
            ],
            "privacy_data_protection": [
                "GDPR DPIA-2025-003 safeguards applied",
                "Data minimisation: only necessary features used",
                "6-year retention aligned to consumer credit legal minimum",
                "PSD2 data used only with explicit user consent",
            ],
            "access_to_financial_services": [
                "Thin-file routing to mandatory manual review (senior loan officer)",
                "Supplementary documentation accepted (employment contract, payslips)",
                "Minimum data threshold: insufficient data defaults to manual review, not automatic decline",
            ],
            "right_to_explanation": [
                "SHAP-based reason codes: top 3 factors communicated to loan officer",
                "Plain-language rejection letter templates with factor-based explanation",
                "Disclosure of AI use in all credit decision communications",
                "Human review available on request for all automated decisions",
            ],
            "human_dignity": [
                "Automated declines include plain-language explanation and invitation to contact human advisor",
                "Any applicant can request human review of automated decision",
                "Vulnerable customer protocol: flagging for enhanced review",
            ],
            "freedom_from_manipulation": [
                "PulseConnect nudges include affordability warnings and responsible lending disclosures",
                "Over-indebtedness risk assessment integrated into PulseCredit (DTI ratio threshold)",
                "AFM consumer protection principles applied to all nudge communications",
            ],
        }
        return json.dumps({
            "right": right,
            "mitigation_measures": mitigations.get(right, ["No specific mitigations identified"]),
        })

    if tool_name == "cross_reference_dpia":
        dpia_ref = tool_input.get("dpia_reference", "")
        return json.dumps({
            "dpia_reference": dpia_ref,
            "key_findings": [
                f"{dpia_ref}: PulseCredit constitutes automated decision-making under GDPR Art. 22 for loans ≤€5k",
                f"{dpia_ref}: Art. 22(2)(a) applies — automated decision necessary for contract performance",
                f"{dpia_ref}: Ethnic origin data (nationality as proxy) processed under Art. 9(2)(g) for bias testing",
                f"{dpia_ref}: 6-year retention policy confirmed proportionate",
            ],
            "fria_extensions": [
                "FRIA extends DPIA to non-data-protection fundamental rights",
                "Art. 22(3) safeguards documented in Human Oversight Design (Artifact 09)",
            ],
        })

    if tool_name == "generate_fria_report":
        assessments = tool_input.get("rights_assessments", [])
        residual_risks = {
            "non_discrimination": "LOW-MEDIUM",
            "privacy_data_protection": "LOW",
            "access_to_financial_services": "MEDIUM",
            "right_to_explanation": "LOW",
            "human_dignity": "LOW",
            "freedom_from_manipulation": "LOW",
        }
        return json.dumps({
            "status": "DRAFT_GENERATED",
            "system": tool_input.get("system_name"),
            "rights_assessed": len(assessments),
            "residual_risks": residual_risks,
            "overall_assessment": "Residual risks assessed as acceptable subject to conditions noted",
            "conditions": [
                "Q2 2026 age group (18-30) remediation review must be completed",
                "Thin-file manual review must remain mandatory and not be bypassed",
                "PulseConnect FRIA must also be completed",
                "Vulnerable customer protocol must be maintained",
            ],
            "output_path": f"compliance/artifacts/{tool_input.get('system_name', 'system').lower().replace(' ', '-')}-fria.json",
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def generate_fria(
    system_name: str,
    affected_population: str,
    risk_tier: str = "HIGH_RISK",
    dpia_reference: str = "",
    sensitive_groups: list | None = None,
) -> dict:
    """
    Generate an Article 27 Fundamental Rights Impact Assessment.

    Args:
        system_name:         AI system name and version
        affected_population: Description of affected persons and scale
        risk_tier:           EU AI Act risk tier
        dpia_reference:      Existing GDPR DPIA reference number
        sensitive_groups:    List of sensitive groups at risk

    Returns:
        dict: FRIA report with rights assessments, mitigations, and residual risks
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "test"))
    tools = _load_tools()

    messages = [{
        "role": "user",
        "content": (
            f"Generate an Article 27 Fundamental Rights Impact Assessment.\n"
            f"System: {system_name}\n"
            f"Affected Population: {affected_population}\n"
            f"Risk Tier: {risk_tier}\n"
            f"GDPR DPIA Reference: {dpia_reference or 'None'}\n"
            f"Sensitive Groups: {', '.join(sensitive_groups or [])}\n\n"
            f"Assess all required rights: {', '.join(REQUIRED_RIGHTS)}. "
            f"For each right: assess impact, propose mitigations, determine residual risk. "
            f"Cross-reference with GDPR DPIA if provided. "
            f"Then generate the complete FRIA report."
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
                if block.name == "generate_fria_report":
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
    print("Running FRIAAgent for PulseCredit v2.1...")
    result = generate_fria(
        system_name="PulseCredit v2.1",
        affected_population="Dutch consumers aged 18-75, approximately 18,000 applications/year",
        risk_tier="HIGH_RISK",
        dpia_reference="DPIA-2025-003",
        sensitive_groups=["ethnic_minorities", "thin_file_applicants", "young_adults_18_25"],
    )
    print(json.dumps(result, indent=2))
