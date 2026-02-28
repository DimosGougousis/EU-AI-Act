# Agents User Guide

> **EU AI Act Compliance Automation — FinPulse NL B.V.**
> Five agentic tools that automate the highest-effort compliance tasks under Regulation (EU) 2024/1689.

---

## Prerequisites

```bash
# Install the package and dependencies
pip install -e ".[dev]"

# Set your LLM API key
export OPENAI_API_KEY=your_key_here      # required for live runs
# AI_MODEL defaults to "gpt-4o"; override with:
export AI_MODEL=gpt-4o-mini              # optional — any OpenAI-compatible model
```

> **No API key needed to run the tests.** All tests mock the LLM client.
> ```bash
> pytest tests/ -v
> ```

---

## Agent 1 — ClassifyBot

**Purpose:** Classifies any AI system into the EU AI Act four-tier risk framework (Prohibited → High-Risk → Limited-Risk → Minimal-Risk).

**Regulatory basis:** Article 5, Article 6, Annex III, Recital 58

**When to use:** When onboarding a new AI system, after a major system update, or as part of an annual AI inventory review.

### Quick Start

```python
from agents import classify_system

result = classify_system({
    "name": "PulseCredit v2.1",
    "purpose": "Evaluates creditworthiness of Dutch consumers for consumer loan decisions",
    "inputs": ["BKR credit history", "PSD2 transaction data", "Loan application form"],
    "outputs": ["Credit score 0-100", "Approve / Refer / Decline recommendation"],
    "deployment_context": "Consumer Credit Provider (Wft licence), Netherlands",
    "sole_purpose_fraud": False,
})

print(result["risk_tier"])      # "HIGH_RISK"
print(result["legal_basis"])    # "Annex III, Point 5(b)"
print(result["obligations"])    # list of applicable articles
```

### Run from CLI

```bash
python -m agents.classify_bot
```

### Tool Call Sequence

```
1. check_prohibited_practices(system_description)
      └─> PASSED — no Article 5 matches
2. check_annex_iii(system_purpose, deployment_context)
      └─> match_found: true, category: "Annex III, Point 5(b)"
3. generate_classification_report(risk_tier, legal_basis, confidence)
      └─> {risk_tier, legal_basis, obligations, deadline}
```

### Output Schema

```json
{
  "risk_tier":    "HIGH_RISK",
  "legal_basis":  "Annex III, Point 5(b)",
  "confidence":   0.97,
  "obligations":  ["Art. 9 — Risk Management System", "..."],
  "deadline":     "2026-08-02"
}
```

---

## Agent 2 — DocDraftAgent

**Purpose:** Auto-generates an Annex IV technical documentation draft by querying the MLflow model registry and data catalog. Returns a completion percentage and action items for human sign-off.

**Regulatory basis:** Article 11, Annex IV, Article 12

**When to use:** After a model release, before a conformity assessment, or when Annex IV completeness falls below 80%.

### Quick Start

```python
from agents import draft_technical_documentation

result = draft_technical_documentation(
    registry_uri="mlflow://pulsecredit/v2.1.3",
    catalog_ref="datahub://credit/training-2024-q4",
    risk_tier="HIGH_RISK",
    system_owner="Dr. Elena Visser, CTO",
    target_date="2026-07-31",
    additional_context="XGBoost ensemble introduced January 2025.",
)

print(f"Completeness: {result['completeness_pct']}%")
print("Action items:", result["missing_fields"])
```

### Run from CLI

```bash
python -m agents.doc_draft_agent
```

### Tool Call Sequence

```
1. fetch_model_metadata(registry_uri)
      └─> AUC, GINI, KS, PSI, architecture, training date
2. fetch_data_catalog(catalog_ref)
      └─> data sources, GDPR basis, bias assessment reference
3. populate_annex_iv_template(model_metadata, data_catalog)
      └─> populated_fields (dict), missing_fields (list)
4. export_documentation_draft(populated_fields, missing_fields)
      └─> {status, completeness_pct, fields_requiring_human_input}
```

### Output Schema

```json
{
  "status":                        "DRAFT_SAVED",
  "output_path":                   "compliance/artifacts/pulsecredit-v2.1.3-annex-iv-draft.json",
  "completeness_pct":              50.0,
  "fields_populated":              6,
  "fields_requiring_human_input":  6,
  "missing_fields":                ["Section 2.3 — Known failure modes", "..."]
}
```

---

## Agent 3 — BiasWatchAgent

**Purpose:** Weekly automated bias monitoring for PulseCredit decisions. Computes Demographic Parity Difference, Equalized Odds, and PSI across gender, age bracket, and nationality groups. Creates incident tickets for threshold breaches.

**Regulatory basis:** Article 10(4), Article 9(5), Article 12

**When to use:** Run on a weekly cron schedule (built-in APScheduler) or on-demand after a model update.

### Quick Start

```python
from agents import run_bias_watch

# Run immediately
result = run_bias_watch()
print(result["status"])       # "PUBLISHED"
print(result["report_path"])  # "compliance/fairness-reports/bias-watch-2026-W09.json"
```

### Scheduled Execution (Monday 07:00 Amsterdam)

```python
from agents.bias_watch_agent import start_scheduler
start_scheduler()   # blocks — run in a background process or Docker container
```

### Pure Python Helper (no API required)

```python
from agents.bias_watch_agent import calculate_demographic_parity

diff = calculate_demographic_parity(
    approvals_group_a=198, total_group_a=282,   # Dutch applicants
    approvals_group_b=28,  total_group_b=65,    # Non-Dutch applicants
)
print(f"Demographic parity difference: {diff:.4f}")  # 0.2716 — breach!
```

### Alert Thresholds

| Metric | Threshold | Breach triggers |
|--------|-----------|----------------|
| Demographic Parity Difference | > 0.05 | `create_incident_ticket(severity=HIGH)` |
| Equalized Odds Difference | > 0.08 | `create_incident_ticket(severity=HIGH)` |
| Population Stability Index | > 0.25 | `create_incident_ticket(severity=CRITICAL)` |

### Tool Call Sequence

```
1. query_decision_log(start_date, end_date)
      └─> 347 decisions, demographics breakdown by gender/age/nationality
2. compute_fairness_metrics(data, metrics)
      └─> {metrics: {...}, breaches: [...]}
3. [if breaches] create_incident_ticket(severity, metric, value, threshold)
      └─> {ticket_id, status, notified}
4. publish_fairness_report(report_data, week)
      └─> {status: PUBLISHED, report_path}
```

---

## Agent 4 — FRIAAgent

**Purpose:** Generates a structured Article 27 Fundamental Rights Impact Assessment (FRIA). Assesses all six EUCFR rights, proposes mitigations, determines residual risk, and cross-references the GDPR DPIA.

**Regulatory basis:** Article 27, EU Charter of Fundamental Rights, GDPR Article 35

**When to use:** Before deploying a high-risk AI system, after significant system changes, or when the GDPR DPIA is updated.

### Quick Start

```python
from agents import generate_fria

result = generate_fria(
    system_name="PulseCredit v2.1",
    affected_population="Dutch consumers aged 18-75, ~18,000 applications/year",
    risk_tier="HIGH_RISK",
    dpia_reference="DPIA-2025-003",
    sensitive_groups=["ethnic_minorities", "thin_file_applicants", "young_adults_18_25"],
)

print(f"Rights assessed: {result['rights_assessed']}")   # 6
print(result["overall_assessment"])
```

### Run from CLI

```bash
python -m agents.fria_agent
```

### Rights Assessed

| Right | EUCFR Basis | Key Risk for PulseCredit |
|-------|------------|--------------------------|
| Non-discrimination | Art. 21 | Proxy discrimination via historical data |
| Privacy & Data Protection | Art. 8 / GDPR | Extensive PSD2 + BKR processing |
| Access to Financial Services | Art. 34 | Thin-file applicant exclusion |
| Right to Explanation | Art. 47 | GDPR Art. 22 automated decision |
| Human Dignity | Art. 1 | Fully automated decline |
| Freedom from Manipulation | Art. 1 & 8 | Credit eligibility nudges |

### Tool Call Sequence

```
Per right (×6):
  1. assess_fundamental_right(right, legal_basis, system_description, affected_population)
  2. propose_mitigation_measures(right, impact, likelihood, severity)
Then:
  3. cross_reference_dpia(dpia_reference, fria_findings)
  4. generate_fria_report(system_name, rights_assessments, dpia_alignment)
```

### Output Schema

```json
{
  "status":              "DRAFT_GENERATED",
  "system":              "PulseCredit v2.1",
  "rights_assessed":     6,
  "residual_risks":      {"non_discrimination": "LOW-MEDIUM", "...": "..."},
  "overall_assessment":  "Residual risks assessed as acceptable subject to conditions",
  "conditions":          ["Q2 2026 age group (18-30) remediation review...", "..."],
  "output_path":         "compliance/artifacts/pulsecredit-v2.1-fria.json"
}
```

---

## Agent 5 — ConformityBot

**Purpose:** Runs an automated Annex VI conformity assessment. Checks all eight Article 16 obligations, queries document repositories and logging systems, and generates a structured report with Non-Conformity Reports (NCRs) and an overall compliance score.

**Regulatory basis:** Article 43, Article 16, Annex VI, Article 12, Article 14

**When to use:** Monthly spot checks, pre-audit preparation, or after remediation to verify NCR closure.

### Quick Start

```python
from agents import run_conformity_check

# Full Annex VI assessment
result = run_conformity_check(
    system_id="pulsecredit-v2.1",
    repository_path="sharepoint://compliance/eu-ai-act/pulsecredit/",
    log_endpoint="https://logs.internal.finpulse.nl/api/ai-decisions/",
    assessment_type="Full Annex VI Assessment",
)

print(f"Overall score: {result['overall_score']}%")
print(f"NCRs: {result['ncr_count']}")
for ncr in result["ncrs"]:
    print(f"  {ncr['id']} — {ncr['article']}: {ncr['status']}")
```

### Run from CLI

```bash
python -m agents.conformity_bot
```

### Spot Check (Single Article)

```python
result = run_conformity_check(
    assessment_type="Spot Check",
    articles=["Art. 12"],   # check only logging compliance
)
```

### Tool Call Sequence

```
Per obligation (×8):
  1. check_document_exists(document_type, repository_path)
  2. check_log_retention(log_endpoint, system_id)
  3. verify_oversight_implementation(system_id, checks)
Then:
  4. generate_conformity_report(check_results, overall_score)
```

### Obligations Checklist

| Article | Obligation | Feb 2026 State |
|---------|-----------|----------------|
| Art. 9  | Risk Management System | ❌ FAIL |
| Art. 10 | Data governance + bias assessment | ❌ FAIL |
| Art. 11 | Annex IV documentation (>80%) | ⚠️ PARTIAL (50%) |
| Art. 12 | Logging ≥6-month retention | ❌ FAIL (30 days) |
| Art. 13 | Instructions for use | ⚠️ PARTIAL |
| Art. 14 | HITL oversight deployed | ❌ FAIL |
| Art. 15 | Robustness testing | ❌ FAIL |
| Art. 27 | FRIA completed | ❌ FAIL |

> Open NCRs are tracked as GitHub Issues #1–#4.

---

## Running All Agents Together

```python
from agents import (
    classify_system,
    draft_technical_documentation,
    run_bias_watch,
    generate_fria,
    run_conformity_check,
)

system = {
    "name": "PulseCredit v2.1",
    "purpose": "AI credit scoring for Dutch consumer loans",
    "inputs": ["BKR", "PSD2", "application form"],
    "outputs": ["credit score", "Approve/Refer/Decline"],
    "deployment_context": "Consumer Credit Provider (Wft), Netherlands",
    "sole_purpose_fraud": False,
}

# Step 1 — Classify
classification = classify_system(system)
assert classification["risk_tier"] == "HIGH_RISK"

# Step 2 — Document
doc_draft = draft_technical_documentation(
    registry_uri="mlflow://pulsecredit/v2.1.3",
    catalog_ref="datahub://credit/training-2024-q4",
)

# Step 3 — Monitor bias
bias_report = run_bias_watch()

# Step 4 — FRIA
fria = generate_fria(
    system_name="PulseCredit v2.1",
    affected_population="~18,000 Dutch consumers/year",
    dpia_reference="DPIA-2025-003",
)

# Step 5 — Conformity check
conformity = run_conformity_check(assessment_type="Full Annex VI Assessment")

print(f"Classification: {classification['risk_tier']}")
print(f"Documentation: {doc_draft.get('completeness_pct', 'N/A')}% complete")
print(f"Bias report: {bias_report.get('status', 'N/A')}")
print(f"FRIA: {fria.get('rights_assessed', 0)} rights assessed")
print(f"Conformity: {conformity.get('overall_score', 0)}% — {conformity.get('ncr_count', 0)} NCRs")
```

---

## Architecture Overview

```
User / Orchestrator
        │
        ├── classify_system()       ──► ClassifyBot       ──► Tool: check_annex_iii
        ├── draft_technical_docs()  ──► DocDraftAgent     ──► Tool: fetch_model_metadata
        ├── run_bias_watch()        ──► BiasWatchAgent     ──► Tool: query_decision_log
        ├── generate_fria()         ──► FRIAAgent          ──► Tool: assess_fundamental_right
        └── run_conformity_check()  ──► ConformityBot      ──► Tool: check_document_exists
                                             │
                                    [Tool results fed back]
                                             │
                                    [Agent continues loop]
                                             │
                                    [stop_reason=stop → return dict]
```

Each agent follows the standard **agentic loop** pattern:
1. Send user message + tool definitions to LLM
2. LLM calls tools → results fed back as `role: tool` messages
3. Loop continues until LLM returns no more tool calls
4. Final JSON response captured and returned to caller

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes (live runs) | `"test"` (mocked in CI) | LLM API key |
| `AI_MODEL` | No | `"gpt-4o"` | Model to use for all agents |

---

## Testing Without an API Key

All agents can be tested without a live API key. The test suite mocks the LLM client:

```bash
pytest tests/ -v
# Expected: all tests pass in < 5 seconds
```

Pure Python helpers (`calculate_demographic_parity`) and tool handlers (`_process_tool_call`) are tested directly — no mocking required for those.
