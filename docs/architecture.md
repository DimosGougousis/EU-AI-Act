# Agent Architecture — EU AI Act Compliance Platform

## Overview

FinPulse's compliance automation platform consists of five specialised agents built on the **Anthropic Claude Agent SDK** (`claude-opus-4-6`). Each agent handles a specific EU AI Act obligation, connects to internal systems via tool use, and produces structured outputs for human review.

---

## Agent Interaction Pattern

All agents follow the standard **tool-use agentic loop**:

```
User / Trigger
      │
      ▼
┌─────────────────────────────────────────┐
│         claude-opus-4-6                 │
│                                         │
│  1. Receive task description            │
│  2. Select tool(s) to call              │
│  3. Process tool results                │
│  4. Repeat until stop_reason=end_turn   │
│  5. Return structured JSON output       │
└─────────────────────────────────────────┘
      │
      ▼
Human Review & Sign-off
      │
      ▼
Compliance Repository (SharePoint / S3)
```

---

## Agent Specifications

### ClassifyBot (Event-Triggered)

**Trigger:** New AI system registered in AI inventory
**Article:** Art. 6 + Annex III
**Model:** `claude-opus-4-6`

```
System Description
      │
      ├──► check_prohibited_practices (Art. 5 screen)
      │
      ├──► check_annex_iii (Annex III matching)
      │
      ├──► check_fraud_exemption (Recital 58 evaluation)
      │
      └──► generate_classification_report (structured JSON)
                │
                └── AI Inventory + Obligations list
```

**Output:** `{ risk_tier, legal_basis, obligations[], confidence, deadline }`

---

### DocDraftAgent (Event-Triggered)

**Trigger:** Model deployed or significant update
**Article:** Art. 11, Annex IV
**Model:** `claude-opus-4-6`

```
MLflow Registry URI + DataHub Catalog Ref
      │
      ├──► fetch_model_metadata (AUC, GINI, KS, PSI, architecture)
      │
      ├──► fetch_data_catalog (sources, lineage, GDPR basis)
      │
      ├──► populate_annex_iv_template (22/28 fields auto-populated)
      │
      └──► export_documentation_draft (78% completeness + action list)
                │
                └── compliance/artifacts/pulsecredit-v*.annex-iv-draft.json
```

**Output:** Draft with completeness %, list of 6 fields requiring human completion

---

### BiasWatchAgent (Scheduled — Weekly)

**Trigger:** Every Monday 07:00 Europe/Amsterdam (APScheduler)
**Article:** Art. 10(4)
**Model:** `claude-opus-4-6`

```
Weekly Cron (Mon 07:00 CET)
      │
      ├──► query_decision_log (previous 7 days, pseudonymised)
      │
      ├──► compute_fairness_metrics
      │         ├── Demographic Parity Difference (threshold: 0.05)
      │         ├── Equalized Odds Difference (threshold: 0.08)
      │         └── Population Stability Index (threshold: 0.25)
      │
      ├──► create_incident_ticket (if threshold breached)
      │         └── Notifies: Head of Data Science
      │
      └──► publish_fairness_report
                └── compliance/fairness-reports/bias-watch-{week}.json
```

**Protected attributes:** gender, age bracket (18-30/31-54/55-75), nationality (Dutch/non-Dutch)

---

### FRIAAgent (Event-Triggered)

**Trigger:** New AI system deployment or significant update
**Article:** Art. 27
**Model:** `claude-opus-4-6`

```
System Description + Affected Population + DPIA Reference
      │
      ├──► assess_fundamental_right × 6
      │         ├── non_discrimination (Art. 21 EUCFR)
      │         ├── privacy_data_protection (Art. 8 EUCFR / GDPR)
      │         ├── access_to_financial_services (Art. 34 EUCFR)
      │         ├── right_to_explanation (Art. 47 EUCFR; GDPR Art. 22)
      │         ├── human_dignity (Art. 1 EUCFR)
      │         └── freedom_from_manipulation (Art. 1 & 8 EUCFR)
      │
      ├──► propose_mitigation_measures (per right)
      │
      ├──► cross_reference_dpia (GDPR DPIA alignment)
      │
      └──► generate_fria_report (residual risks + conditions)
                └── compliance/artifacts/{system}-fria.json
```

**Output:** Rights assessment table + residual risk levels + sign-off requirements

---

### ConformityBot (Scheduled — Monthly)

**Trigger:** 1st of each month + pre-milestone reviews
**Article:** Art. 43, Annex VI
**Model:** `claude-opus-4-6`

```
System ID + Repository Path + Log Endpoint
      │
      ├──► check_document_exists × 7 document types
      │         ├── risk_management_system
      │         ├── technical_documentation
      │         ├── bias_assessment
      │         ├── fria
      │         ├── conformity_declaration
      │         ├── human_oversight_procedure
      │         └── logging_configuration
      │
      ├──► check_log_retention (Art. 12 — 6-month minimum)
      │
      ├──► verify_oversight_implementation (Art. 14 — HITL checks)
      │
      └──► generate_conformity_report
                ├── Per-article status (PASS/PARTIAL/FAIL)
                ├── NCR list with IDs
                ├── Overall score (%)
                └── compliance/reports/conformity-check-{date}.json
```

**February 2026 baseline score: 15%** | Target August 2, 2026: 100%

---

## Integration Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FINPULSE COMPLIANCE AGENT PLATFORM               │
│                                                                     │
│  Triggers:                                                          │
│  ├── Event: New AI system registered   → ClassifyBot               │
│  ├── Event: Model deployed/updated     → DocDraftAgent             │
│  ├── Schedule: Weekly Monday 07:00     → BiasWatchAgent            │
│  ├── Schedule: Monthly 1st             → ConformityBot             │
│  └── Event: New deployment             → FRIAAgent                 │
│                                                                     │
│  Agents (claude-opus-4-6):                                          │
│  ├── ClassifyBot  ──► AI Inventory + EU AI Act Regulation DB       │
│  ├── DocDraftAgent ─► MLflow Registry + DataHub Catalog            │
│  ├── BiasWatchAgent → Decision Log DB + Incident Ticketing (Jira)  │
│  ├── FRIAAgent ─────► System Description + GDPR DPIA Store         │
│  └── ConformityBot ─► SharePoint Docs + Log API + Report Store     │
│                                                                     │
│  Outputs:                                                           │
│  ├── Compliance Repository (SharePoint / S3)                        │
│  ├── Compliance Dashboard (internal web app)                        │
│  ├── Incident Tickets (Jira)                                        │
│  └── Audit Trail (immutable log store)                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### Human-in-the-Loop by Design
All agent outputs are **advisory** — they require human review and sign-off before becoming authoritative compliance records. This aligns with Article 14 (human oversight) and ensures FinPulse retains legal accountability for its compliance programme.

### No Hallucination in Regulatory Context
Each agent uses **structured tool calls** rather than free-form generation for regulatory determinations. The tools constrain outputs to defined schemas (risk tier enums, article citation formats) reducing the risk of fabricated regulatory citations.

### Testability Without API Keys
All agent tool handlers are implemented as pure Python stubs that return mock responses. The pytest suite covers schema validation, helper function logic, and mocked agentic loop execution — enabling CI/CD without live API credentials.

---

## Files

```
agents/
├── __init__.py                 # Package exports
├── classify_bot.py             # ClassifyBot (Art. 6 + Annex III)
├── doc_draft_agent.py          # DocDraftAgent (Art. 11, Annex IV)
├── bias_watch_agent.py         # BiasWatchAgent (Art. 10)
├── fria_agent.py               # FRIAAgent (Art. 27)
├── conformity_bot.py           # ConformityBot (Art. 43, Annex VI)
└── schemas/
    ├── classify_bot_tools.json
    ├── doc_draft_tools.json
    ├── bias_watch_tools.json
    ├── fria_tools.json
    └── conformity_tools.json
```
