"""
EU AI Act Compliance Automation Agents — FinPulse NL B.V.

Five agentic tools built on the Anthropic Claude SDK to automate
high-effort compliance tasks under Regulation (EU) 2024/1689.

Agents:
    ClassifyBot      — Article 6 + Annex III risk-tier classification
    DocDraftAgent    — Annex IV technical documentation generation
    BiasWatchAgent   — Article 10 weekly demographic parity monitoring
    FRIAAgent        — Article 27 Fundamental Rights Impact Assessment
    ConformityBot    — Annex VI conformity assessment runner

Usage:
    from agents import classify_system, run_bias_watch, run_conformity_check
"""

from agents.classify_bot import classify_system
from agents.doc_draft_agent import draft_technical_documentation
from agents.bias_watch_agent import run_bias_watch, calculate_demographic_parity
from agents.fria_agent import generate_fria
from agents.conformity_bot import run_conformity_check

__all__ = [
    "classify_system",
    "draft_technical_documentation",
    "run_bias_watch",
    "calculate_demographic_parity",
    "generate_fria",
    "run_conformity_check",
]
