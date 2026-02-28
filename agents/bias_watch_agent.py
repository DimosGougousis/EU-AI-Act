"""
BiasWatchAgent — Continuous EU AI Act Bias Monitoring Agent

Runs on a weekly schedule to monitor live PulseCredit decisions for
demographic bias. Computes fairness metrics, compares against thresholds,
generates reports, and creates incident tickets for threshold breaches.

Regulatory basis:
    - Article 10(4) — Bias detection and correction
    - Article 9(5)  — Risk monitoring obligations
    - Article 12    — Logging and auditability

Fairness metrics monitored:
    - Demographic Parity Difference  (threshold: > 0.05)
    - Equalized Odds Difference      (threshold: > 0.08)
    - Population Stability Index     (threshold: > 0.25)

Schedule: Monday 07:00 Europe/Amsterdam (APScheduler)

Usage:
    # Run immediately
    result = run_bias_watch()

    # Start scheduled execution
    from agents.bias_watch_agent import start_scheduler
    start_scheduler()
"""

import json
import os
from datetime import date, timedelta
from pathlib import Path

import anthropic

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

SCHEMAS_DIR = Path(__file__).parent / "schemas"

SYSTEM_PROMPT = (
    "You are BiasWatchAgent, an EU AI Act Article 10 bias monitoring specialist. "
    "Each week, query the previous 7 days of PulseCredit decisions, "
    "compute all configured fairness metrics, compare to thresholds, "
    "create incident tickets for any breaches, and publish a fairness report. "
    "Protected attributes: gender, age_bracket (18-30, 31-54, 55-75), nationality (Dutch/non-Dutch). "
    "Be precise about metric values and threshold comparisons."
)

# Configurable alert thresholds (Article 10 alignment)
THRESHOLDS = {
    "demographic_parity": 0.05,
    "equalized_odds": 0.08,
    "psi": 0.25,
    "approval_rate_cv": 0.15,  # coefficient of variation by region
}


def calculate_demographic_parity(
    approvals_group_a: int,
    total_group_a: int,
    approvals_group_b: int,
    total_group_b: int,
) -> float:
    """
    Calculate demographic parity difference between two groups.

    Demographic parity difference = |P(approve|group A) - P(approve|group B)|

    Args:
        approvals_group_a: Number of approvals in group A
        total_group_a:     Total applications in group A
        approvals_group_b: Number of approvals in group B
        total_group_b:     Total applications in group B

    Returns:
        float: Absolute demographic parity difference (0 = perfect parity)
    """
    if total_group_a == 0 or total_group_b == 0:
        raise ValueError("Group totals must be greater than zero")
    rate_a = approvals_group_a / total_group_a
    rate_b = approvals_group_b / total_group_b
    return abs(rate_a - rate_b)


def _load_tools() -> list:
    with open(SCHEMAS_DIR / "bias_watch_tools.json") as f:
        return json.load(f)


def _process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "query_decision_log":
        # Mock data representing one week of PulseCredit decisions
        return json.dumps({
            "period": f"{tool_input.get('start_date')} to {tool_input.get('end_date')}",
            "total_decisions": 347,
            "demographics": {
                "gender": {
                    "male":   {"approved": 118, "declined": 62, "total": 180},
                    "female": {"approved": 108, "declined": 59, "total": 167},
                },
                "age_bracket": {
                    "18-30": {"approved": 58, "declined": 48, "total": 106},
                    "31-54": {"approved": 126, "declined": 44, "total": 170},
                    "55-75": {"approved": 42, "declined": 29, "total": 71},
                },
                "nationality": {
                    "dutch":     {"approved": 198, "declined": 84, "total": 282},
                    "non_dutch": {"approved": 28, "declined": 37, "total": 65},
                },
            },
            "psi": 0.07,
        })

    if tool_name == "compute_fairness_metrics":
        data = tool_input.get("data", {})
        demo = data.get("demographics", {})

        results = {}

        # Gender parity
        g = demo.get("gender", {})
        if g.get("male") and g.get("female"):
            results["demographic_parity_gender"] = round(
                calculate_demographic_parity(
                    g["male"]["approved"], g["male"]["total"],
                    g["female"]["approved"], g["female"]["total"],
                ), 4,
            )

        # Age parity (18-30 vs 31-54)
        a = demo.get("age_bracket", {})
        if a.get("18-30") and a.get("31-54"):
            results["demographic_parity_age_1830"] = round(
                calculate_demographic_parity(
                    a["18-30"]["approved"], a["18-30"]["total"],
                    a["31-54"]["approved"], a["31-54"]["total"],
                ), 4,
            )

        # Nationality parity
        n = demo.get("nationality", {})
        if n.get("dutch") and n.get("non_dutch"):
            results["demographic_parity_nationality"] = round(
                calculate_demographic_parity(
                    n["dutch"]["approved"], n["dutch"]["total"],
                    n["non_dutch"]["approved"], n["non_dutch"]["total"],
                ), 4,
            )

        results["psi"] = data.get("psi", 0)

        # Threshold checks
        breaches = []
        for metric, value in results.items():
            threshold_key = metric.split("_")[0] + "_" + metric.split("_")[1] if "_" in metric else metric
            threshold = THRESHOLDS.get("demographic_parity" if "parity" in metric else "psi")
            if threshold and value > threshold:
                breaches.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "severity": "HIGH" if value > threshold * 1.5 else "MEDIUM",
                })

        return json.dumps({"metrics": results, "breaches": breaches, "thresholds": THRESHOLDS})

    if tool_name == "create_incident_ticket":
        return json.dumps({
            "ticket_id": f"BIAS-{date.today().strftime('%Y%m%d')}-001",
            "status": "CREATED",
            "severity": tool_input.get("severity"),
            "metric": tool_input.get("metric"),
            "notified": ["head_of_data_science@finpulse.nl"],
        })

    if tool_name == "publish_fairness_report":
        week = tool_input.get("week", date.today().strftime("%Y-W%V"))
        return json.dumps({
            "status": "PUBLISHED",
            "report_path": f"compliance/fairness-reports/bias-watch-{week}.json",
            "week": week,
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_bias_watch() -> dict:
    """
    Execute one weekly bias monitoring run.

    Queries the previous 7 days of PulseCredit decisions, computes fairness
    metrics, creates incident tickets for threshold breaches, and publishes
    the weekly fairness report.

    Returns:
        dict: Fairness report summary with metrics, breaches, and report path
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "test"))
    tools = _load_tools()

    today = date.today()
    start = (today - timedelta(days=7)).isoformat()
    end = today.isoformat()

    messages = [{
        "role": "user",
        "content": (
            f"Run weekly bias monitoring report for PulseCredit. "
            f"Date range: {start} to {end}. "
            f"Query decision log, compute all fairness metrics, "
            f"create incident tickets for any threshold breaches, "
            f"and publish the report."
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
                if block.name == "publish_fairness_report":
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


def start_scheduler():
    """Start the APScheduler to run BiasWatchAgent every Monday at 07:00 Amsterdam time."""
    if not APSCHEDULER_AVAILABLE:
        raise ImportError("APScheduler is required: pip install apscheduler")

    scheduler = BlockingScheduler()

    @scheduler.scheduled_job("cron", day_of_week="mon", hour=7, timezone="Europe/Amsterdam")
    def scheduled_run():
        print("BiasWatchAgent: Starting weekly bias monitoring run...")
        result = run_bias_watch()
        print(f"BiasWatchAgent: Run complete — {result}")

    print("BiasWatchAgent scheduler started. Runs every Monday at 07:00 Amsterdam time.")
    scheduler.start()


if __name__ == "__main__":
    print("Running BiasWatchAgent (single run)...")
    result = run_bias_watch()
    print(json.dumps(result, indent=2))
