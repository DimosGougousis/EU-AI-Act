# EU AI Act Compliance Assessment — FinPulse NL B.V.

> **Hypothetical compliance portfolio** for a Dutch multi-product FinTech under Regulation (EU) 2024/1689 (EU AI Act). Educational and illustrative purposes only.

---

## Overview

This repository contains a complete EU AI Act compliance assessment and hypothetical implementation portfolio for **FinPulse NL B.V.**, a fictional Dutch FinTech company. The portfolio covers all three AI risk tiers:

| Risk Tier | System | Basis |
|-----------|--------|-------|
| **HIGH-RISK** | PulseCredit (credit scoring) | Annex III §5(b) |
| **HIGH-RISK** | PulseConnect (open banking PFM + credit eligibility) | Annex III §5(b) by proxy |
| **EXEMPT** | PulseGuard (fraud detection & AML) | Recital 58 exemption |
| **LIMITED-RISK** | PulseBot (customer chatbot) | Article 50(1) |

---

## Live Site

> Open `index.html` in a browser — no server required.
> GitHub Pages: [https://dimosGougousis.github.io/EU-AI-Act](https://dimosGougousis.github.io/EU-AI-Act)

---

## Portfolio Structure

```
EU-AI-Act/
├── index.html                     Executive summary & compliance dashboard
├── 01-company-profile.html        FinPulse NL B.V. profile, products, licences
├── 02-ai-inventory.html           AI inventory with full risk-tier classification rationale
├── 03-gap-analysis.html           Per-article gap analysis (Art. 9, 10, 11, 12, 13, 14, 15, 26, 27, 43)
├── 04-roadmap.html                Phased implementation plan → August 2, 2026
├── 05-agents.html                 AI Agent use cases: ClassifyBot, DocDraftAgent, BiasWatchAgent, FRIAAgent, ConformityBot
├── artifacts/
│   ├── 06-technical-doc.html      Annex IV technical file — PulseCredit v2.1
│   ├── 07-risk-management.html    Article 9 risk management system & risk register
│   ├── 08-data-governance.html    Article 10 data governance & bias assessment results
│   ├── 09-human-oversight.html    Article 14 human oversight design (HITL + HIC)
│   ├── 10-fria.html               Article 27 Fundamental Rights Impact Assessment
│   └── 11-conformity.html         Annex VI conformity assessment + EU Declaration of Conformity
├── css/
│   └── style.css                  EU-themed stylesheet (EU blue #003399, pure HTML/CSS/JS)
└── README.md                      This file
```

---

## Key Regulatory Dates

| Date | Milestone |
|------|-----------|
| August 1, 2024 | EU AI Act enters force |
| February 2, 2025 | Prohibited AI practices banned |
| **August 2, 2026** | **High-risk AI obligations enforceable** |
| December 31, 2030 | Legacy system compliance deadline |

---

## AI Agents Demonstrated

The `05-agents.html` page demonstrates 5 compliance automation agents built on the **Anthropic Claude Agent SDK** (`claude-opus-4-6`):

1. **ClassifyBot** — Risk-tier classification via Annex III analysis
2. **DocDraftAgent** — Annex IV documentation generation from MLflow metadata
3. **BiasWatchAgent** — Weekly demographic parity monitoring (scheduled agentic task)
4. **FRIAAgent** — Fundamental Rights Impact Assessment generator
5. **ConformityBot** — Automated Annex VI conformity checklist runner

Each agent includes: tool definitions (JSON), agentic loop code (Python), HTML input form templates, and sample outputs.

---

## Regulatory Basis

- [Regulation (EU) 2024/1689 — EU AI Act](https://artificialintelligenceact.eu/)
- Articles: 5, 9, 10, 11, 12, 13, 14, 15, 16, 22, 26, 27, 43, 50, 99
- Annexes: III (high-risk list), IV (technical documentation), V (declaration), VI (internal control)
- Recital 58 — Fraud detection exemption
- DNB SAFEST Framework (2019) | DNB/AFM Joint AI Report (2024)
- GDPR (2016/679) | DORA (2022/2554) | PSD2

---

## Disclaimer

FinPulse NL B.V. is a **fictional company**. This portfolio is a hypothetical educational exercise illustrating how a Dutch FinTech might approach EU AI Act compliance. It does not constitute legal advice. Regulatory interpretations reflect the EU AI Act as in force in February 2026.

---

*EU AI Act Compliance Portfolio — February 2026*
