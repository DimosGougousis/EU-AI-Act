# Key Product Decisions — EU AI Act Compliance Programme

> This log captures the five hardest judgment calls made during programme design.
> For each: the decision, alternatives considered, the trade-off accepted, and the reasoning.

---

## Decision 1 — Should PulseConnect be classified as High-Risk?

**Context:** PulseConnect is FinPulse's account aggregation platform (open banking). Its stated purpose is personal finance management — not credit scoring. Annex III Point 5(b) explicitly names "creditworthiness evaluation" as high-risk. Does PulseConnect fall under that?

**The problem:** PulseConnect's spending category data (rent/utilities ratio, gambling transactions, income stability signals) is used as a feature input to PulseCredit's scoring model. The platforms are operationally separate, but one feeds the other.

**Options considered:**

| Option | Classification | Risk |
|--------|---------------|------|
| A — Classify by stated purpose only | LIMITED_RISK (Art. 50 chatbot disclosure) | Regulator finds the data pipeline and re-classifies post-enforcement |
| B — Classify by actual data use | HIGH_RISK (Annex III §5b proxy) | Higher compliance cost, earlier obligation trigger |
| C — Separate the data pipeline entirely | Either, depending on architecture | 6-9 month engineering effort, disrupts credit product roadmap |

**Decision: Option B — HIGH_RISK via proxy classification.**

**Reasoning:** The DNB/AFM Joint AI Report (2024) explicitly warns against "purpose-washing" — classifying systems by their label rather than their functional role in an automated decision. PulseConnect's transaction categorisation directly influences creditworthiness determinations made downstream. A regulator examining the data lineage would find the pipeline. The cost of re-classification after enforcement begins (August 2026) far exceeds the cost of compliance obligations now.

**Trade-off accepted:** PulseConnect now carries Articles 9–15 obligations despite not making credit decisions directly. This creates ~40 additional FTE-days of compliance work (see roadmap Phase B). Accepted as the lower-risk option vs. regulatory re-classification under enforcement.

---

## Decision 2 — Should PulseGuard claim the Recital 58 Fraud Detection Exemption?

**Context:** PulseGuard is FinPulse's transaction fraud and AML monitoring system. Annex III Point 5(b) names AI systems for credit scoring as high-risk, but Recital 58 of the EU AI Act carves out an exemption for systems whose "sole purpose" is fraud or AML detection, even if deployed in a financial services context.

**The problem:** PulseGuard generates a "risk profile" that includes a fraud likelihood score. The legal team flagged that this risk profile is occasionally referenced by human underwriters during manual loan reviews — which could be argued to make it an indirect input to creditworthiness determinations, potentially voiding the exemption.

**Options considered:**

| Option | Classification | Risk |
|--------|---------------|------|
| A — Claim Recital 58 exemption in full | MINIMAL_RISK | Exemption challenged if underwriters continue referencing fraud score in credit decisions |
| B — Re-classify as HIGH_RISK immediately | HIGH_RISK | Full obligations triggered; significant over-compliance for a fraud-only system |
| C — Claim exemption + implement architectural guardrail | MINIMAL_RISK with guardrail | Defensible position with documented evidence of sole-purpose design |

**Decision: Option C — Claim exemption, implement architectural guardrail.**

**Reasoning:** Recital 58 exemption is valid if the system is *designed* for sole-purpose fraud detection and operational controls prevent dual use. The solution is to formally prohibit fraud score access during credit underwriting workflows (documented in the Instructions for Use, Art. 13) and add an audit log entry whenever the fraud score is accessed, flagging any access during an active credit application. This creates a defensible evidentiary record.

**Trade-off accepted:** If the guardrail is ever bypassed in production — even informally — the exemption becomes contestable. Accepted on the basis that the guardrail is enforceable via system access controls, not just policy. Exemption claim is documented in the AI Inventory with explicit reference to Recital 58 conditions.

**Review trigger:** If PulseGuard's fraud score is ever formally integrated into the PulseCredit feature set, re-classification to HIGH_RISK is mandatory.

---

## Decision 3 — Why 5 Separate Agents Instead of 1 Orchestrator?

**Context:** The compliance programme requires five distinct automated tasks: risk classification, document drafting, bias monitoring, FRIA generation, and conformity assessment. The initial design proposal was a single "ComplianceOrchestrator" agent that handled all five.

**The problem:** A monolithic agent creates tight coupling across tasks with very different:
- Trigger events (one-time vs. weekly scheduled vs. deployment-triggered)
- Failure modes (a bias monitoring failure should not block conformity assessment)
- Tool schemas and context windows (bias monitoring needs 7 days of decision logs; FRIA needs population data)
- Testing complexity (impossible to unit-test individual compliance logic in a monolith)

**Options considered:**

| Option | Architecture | Trade-off |
|--------|-------------|-----------|
| A — Single orchestrator agent | 1 agent, 1 system prompt, 1 tool schema | Simple deployment, high coupling, untestable individual logic |
| B — 5 independent agents | 5 agents, separate schemas, independent failure domains | More files, more maintenance, but testable and independently deployable |
| C — 3 agents (combine related) | Classification+FRIA in one; Draft+Conformity in one; standalone Bias | Middle ground |

**Decision: Option B — 5 independent agents.**

**Reasoning:** Compliance tasks have fundamentally different operational profiles. BiasWatchAgent runs on a weekly APScheduler cron — it must be deployable as a standalone service without triggering document drafting. ConformityBot runs before key milestones — triggering it should not require a live bias monitoring result. Each agent also has a single, auditable system prompt scoped to one Article obligation, making it easier to update when regulatory guidance evolves.

**Trade-off accepted:** 5 separate Python files and 5 JSON schema files instead of one. Accepted: the additional surface area is offset by full pytest coverage (68 tests), independent deployability, and clear Article-to-agent mapping that non-engineering stakeholders can understand.

---

## Decision 4 — Weekly Bias Monitoring vs. Real-Time

**Context:** Article 10(4) requires providers to address bias "on an ongoing basis." BiasWatchAgent is configured to run weekly (Monday 07:00 CET). The data science team initially proposed real-time monitoring with immediate alerting on every decision batch.

**The problem:** Real-time bias monitoring on individual lending decisions creates several issues:
1. **Statistical noise:** Demographic parity measured on 50 decisions is meaningless — confidence intervals are enormous at small N. A single anomalous hour would generate false-positive incidents.
2. **Operational cost:** Real-time inference monitoring at FinPulse's decision volume (~3,800 decisions/week) requires streaming infrastructure not currently in the architecture.
3. **Regulatory minimum:** The EU AI Act does not require real-time monitoring — "ongoing" is interpreted as regular, documented, and actionable.

**Options considered:**

| Option | Frequency | Statistical validity | Infrastructure cost |
|--------|-----------|---------------------|---------------------|
| Real-time | Continuous | Low (small N per window) | High (streaming pipeline) |
| Daily | 24h rolling | Moderate (~540 decisions) | Medium |
| **Weekly** | **7-day rolling** | **High (~3,800 decisions)** | **Low (scheduled job)** |
| Monthly | 30-day rolling | Very high | Very low |

**Decision: Weekly (7-day rolling window).**

**Reasoning:** Weekly provides statistically valid samples (~3,800 decisions) while meeting "ongoing" regulatory intent. The 7-day window aligns with PulseCredit's natural credit cycle patterns and gives the data science team a Monday morning report in time for the Tuesday model review meeting. Monthly monitoring would delay detection of a real bias event by up to 4 weeks — unacceptable given Art. 10 obligations.

**Trade-off accepted:** A bias event occurring on a Tuesday would not be detected until the following Monday (6-day lag). Accepted: the risk is mitigated by setting the demographic parity threshold at 0.05 (tighter than many frameworks recommend) to provide early warning before a breach becomes severe.

---

## Decision 5 — 12-Month Log Retention vs. 6-Month Minimum

**Context:** Article 12 of the EU AI Act requires high-risk AI systems to maintain logs for a minimum of 6 months. The programme proposal specifies 12-month log retention for PulseCredit.

**The problem:** NCR-001 (the most critical open non-conformity) is that current log retention is only 30 days — well below the 6-month minimum. In remediating NCR-001, the question was whether to target exactly 6 months (183 days) or set a higher standard.

**Options considered:**

| Option | Retention | Rationale |
|--------|-----------|-----------|
| 6 months | 183 days | Meets Art. 12 minimum exactly |
| 12 months | 365 days | Exceeds minimum; aligns with DORA + consumer credit obligations |
| 24 months | 730 days | Maximum legal certainty; significant storage cost |

**Decision: 12-month retention.**

**Reasoning:** FinPulse operates under DORA (Article 15 ICT risk management), which requires ICT-related operational logs to be retained for a minimum of 1 year. PulseCredit's decision logs are simultaneously EU AI Act logs (Art. 12) and DORA ICT logs. Maintaining two different retention policies for the same log data is operationally fragile and a compliance risk in itself. Aligning at 12 months satisfies both frameworks with a single policy.

Additionally, Dutch consumer credit regulations (Wft) allow borrowers to dispute credit decisions up to 12 months after the fact. A 6-month log retention policy would leave FinPulse unable to reconstruct the exact model inputs and version used in a disputed decision during months 7–12.

**Trade-off accepted:** ~2× storage cost vs. the 6-month minimum. Accepted: the cost is marginal (structured logs, not raw data), and the regulatory risk of underretention across multiple frameworks is asymmetric — the downside is significant.

---

*Last updated: February 2026 | Questions: raise as GitHub Issue or PR comment*
