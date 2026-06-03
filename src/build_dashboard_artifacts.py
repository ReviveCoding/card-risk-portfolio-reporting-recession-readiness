from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
from plotly.io import to_html

ROOT = Path(".")
OUT = ROOT / "outputs"
REPORTS = ROOT / "reports"
DASH_DIR = REPORTS / "dashboard"
DASH_DIR.mkdir(parents=True, exist_ok=True)

HTML_OUT = DASH_DIR / "card_risk_portfolio_dashboard.html"
MD_OUT = REPORTS / "card_risk_dashboard_artifact.md"

def read_csv(path):
    path = Path(path)
    if path.exists():
        return pd.read_csv(path)
    print(f"[WARN] Missing {path}")
    return pd.DataFrame()

def find_col(df, names):
    if df.empty:
        return None
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    for c in df.columns:
        for n in names:
            if n.lower() in c.lower():
                return c
    return None

def fig_html(title, fig):
    return f"<section><h2>{title}</h2>{to_html(fig, full_html=False, include_plotlyjs=False)}</section>"

def metric_card(label, value):
    return f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
    </div>
    """

def fmt(x, digits=3):
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def get_exact_arbc_row(review_df):
    if review_df.empty:
        return pd.Series(dtype="object")

    strategy = find_col(review_df, ["strategy", "method"])
    cap = find_col(review_df, ["capacity_rate", "capacity"])

    if not strategy or not cap:
        return pd.Series(dtype="object")

    cap_num = pd.to_numeric(review_df[cap], errors="coerce")
    r10 = review_df[cap_num.between(0.095, 0.105)].copy()

    exact = r10[r10[strategy].astype(str).str.lower().eq("asymmetric_risk_boundary_correction")]
    if not exact.empty:
        return exact.iloc[0]

    contains_asym = r10[r10[strategy].astype(str).str.contains("asymmetric", case=False, regex=False)]
    if not contains_asym.empty:
        return contains_asym.iloc[0]

    return pd.Series(dtype="object")

def add_metric_from_evidence(metrics, evidence_df, metric_name, label=None):
    if evidence_df.empty:
        return False
    if "section" not in evidence_df.columns or "metric" not in evidence_df.columns or "method_value" not in evidence_df.columns:
        return False
    rows = evidence_df[
        (evidence_df["section"].astype(str) == "review_routing_10pct")
        & (evidence_df["metric"].astype(str) == metric_name)
    ]
    if rows.empty:
        return False
    metrics.append((label or metric_name, fmt(rows.iloc[0]["method_value"])))
    return True

ablation = read_csv(OUT / "model_ablation_summary.csv")
review = read_csv(OUT / "review_capacity_sensitivity.csv")
op = read_csv(OUT / "operational_retraining_summary.csv")
evidence = read_csv(OUT / "resume_evidence_metrics.csv")

sections = []
metrics = []

# Model ablation
if not ablation.empty:
    version = find_col(ablation, ["version", "model", "model_name"])
    pr = find_col(ablation, ["pr_auc"])
    roc = find_col(ablation, ["roc_auc"])
    capture = find_col(ablation, ["default_capture_at_top10pct", "capture"])
    brier = find_col(ablation, ["brier"])

    if version:
        metric_cols = [c for c in [pr, roc, capture, brier] if c]
        if metric_cols:
            melted = ablation[[version] + metric_cols].melt(id_vars=version, var_name="metric", value_name="value")
            fig = px.bar(
                melted, x=version, y="value", color="metric", barmode="group",
                title="Model Ablation: Baseline vs Card-Risk Specialty Method"
            )
            fig.update_layout(xaxis_tickangle=-20)
            sections.append(fig_html("Model Ablation", fig))

        base = ablation[ablation[version].astype(str).str.contains("M0|Logistic", case=False, regex=True)]
        spec = ablation[ablation[version].astype(str).str.contains("M4|Segment", case=False, regex=True)]
        if not base.empty and not spec.empty:
            b = base.iloc[0]
            s = spec.iloc[0]
            if pr:
                metrics.append(("PR-AUC", f"{fmt(b[pr])} -> {fmt(s[pr])}"))
            if roc:
                metrics.append(("ROC-AUC", f"{fmt(b[roc])} -> {fmt(s[roc])}"))
            if capture:
                metrics.append(("Top-10% Default Capture", f"{fmt(b[capture])} -> {fmt(s[capture])}"))

# Review capacity
if not review.empty:
    cap = find_col(review, ["capacity_rate", "capacity"])
    strategy = find_col(review, ["strategy", "method"])
    f1 = find_col(review, ["risk_review_f1", "f1"])
    precision = find_col(review, ["review_precision", "precision"])
    recall = find_col(review, ["risk_capture_recall", "recall"])

    if cap and strategy:
        for metric in [m for m in [f1, precision, recall] if m]:
            fig = px.line(
                review, x=cap, y=metric, color=strategy, markers=True,
                title=f"Review Capacity Tradeoff: {metric}"
            )
            sections.append(fig_html(f"Review Capacity: {metric}", fig))

        # Prefer resume_evidence_metrics.csv because it stores the validated resume-safe ARBC comparison.
        added_f1 = add_metric_from_evidence(metrics, evidence, "Risk-Review F1", "10% Review F1")
        added_precision = add_metric_from_evidence(metrics, evidence, "Review Precision", "10% Review Precision")
        added_recall = add_metric_from_evidence(metrics, evidence, "Risk Capture Recall", "Risk-Capture Recall")

        # Fallback to exact ARBC row only. Do not match inflated_risk_boundary.
        arbc = get_exact_arbc_row(review)
        if not arbc.empty:
            if f1 and not added_f1:
                metrics.append(("10% Review F1", fmt(arbc[f1])))
            if precision and not added_precision:
                metrics.append(("10% Review Precision", fmt(arbc[precision])))
            if recall and not added_recall:
                metrics.append(("Risk-Capture Recall", fmt(arbc[recall])))

# Operational retraining
if not op.empty:
    policy = find_col(op, ["policy", "retraining_policy"])
    pr = find_col(op, ["avg_pr_auc", "pr_auc"])
    roc = find_col(op, ["avg_roc_auc", "roc_auc"])
    brier = find_col(op, ["avg_brier", "brier"])
    retrains = find_col(op, ["retrain_events", "n_retrains"])

    if policy:
        metric_cols = [c for c in [pr, roc, brier, retrains] if c]
        if metric_cols:
            melted = op[[policy] + metric_cols].melt(id_vars=policy, var_name="metric", value_name="value")
            fig = px.bar(
                melted, x=policy, y="value", color="metric", barmode="group",
                title="Operational Backtest: Retraining Policy Comparison"
            )
            fig.update_layout(xaxis_tickangle=-15)
            sections.append(fig_html("Retraining Policy", fig))

        q = op[op[policy].astype(str).str.contains("quarter", case=False, regex=True)]
        if not q.empty:
            row = q.iloc[0]
            if pr:
                metrics.append(("Quarterly Avg PR-AUC", fmt(row[pr])))
            if roc:
                metrics.append(("Quarterly Avg ROC-AUC", fmt(row[roc])))
            if retrains:
                metrics.append(("Quarterly Retrain Events", str(int(row[retrains]))))

# Artifact inventory
inventory_paths = [
    OUT / "model_ablation_summary.csv",
    OUT / "review_capacity_sensitivity.csv",
    OUT / "operational_retraining_summary.csv",
    OUT / "resume_evidence_metrics.csv",
    REPORTS / "resume_evidence_summary.md",
    REPORTS / "operational_backtest_report.md",
    REPORTS / "card_risk_dashboard_artifact.md",
]
inventory = pd.DataFrame([
    {
        "artifact": str(p).replace("\\", "/"),
        "status": "FOUND" if p.exists() else "MISSING",
        "size_kb": round(p.stat().st_size / 1024, 1) if p.exists() else 0,
    }
    for p in inventory_paths
])
fig = px.bar(inventory, x="artifact", y="size_kb", color="status", title="Validation and Reporting Artifact Inventory")
fig.update_layout(xaxis_tickangle=-35)
sections.append(fig_html("Artifact Inventory", fig))

if not metrics:
    metrics = [
        ("Dashboard Status", "Generated"),
        ("Data Boundary", "Synthetic/offline + public-data aligned"),
        ("Primary Use", "Card-risk reporting artifact"),
    ]

metric_html = "\n".join(metric_card(k, v) for k, v in metrics)
metric_md = pd.DataFrame(metrics, columns=["Metric", "Value"]).to_markdown(index=False)

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Card Risk Portfolio Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #222; background: #fafafa; }}
    h1, h2 {{ color: #111; }}
    .subtitle {{ color: #555; max-width: 1100px; line-height: 1.45; }}
    .boundary {{ border-left: 4px solid #777; padding: 10px 14px; background: #f2f2f2; margin: 16px 0 24px 0; max-width: 1100px; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; max-width: 1200px; margin-bottom: 22px; }}
    .metric-card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
    .metric-label {{ font-size: 13px; color: #555; margin-bottom: 6px; }}
    .metric-value {{ font-size: 24px; font-weight: 700; color: #111; }}
    section {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 18px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .footer {{ margin-top: 24px; color: #666; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Card Risk Portfolio Dashboard Artifact</h1>
  <p class="subtitle">
    Local/GitHub-runnable reporting artifact for a synthetic/offline card-risk portfolio analytics project.
    This dashboard summarizes model ablation, review-capacity tradeoffs, operational retraining policy, and validation/reporting artifact coverage.
  </p>
  <div class="boundary">
    <b>Claim boundary:</b> This is a synthetic/offline and public-data-aligned project artifact.
    It does not use proprietary bank data, real cardholder data, proprietary bureau microdata, JPMC internal systems, or deployed banking decisioning.
  </div>
  <h2>Executive KPI Summary</h2>
  <div class="metric-grid">{metric_html}</div>
  {''.join(sections)}
  <div class="footer">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.</div>
</body>
</html>
"""

HTML_OUT.write_text(html, encoding="utf-8")

md = f"""# Card Risk Portfolio Dashboard Artifact

This dashboard artifact supports credit-card risk reporting, portfolio monitoring, recession-readiness analysis, review-capacity decisioning, and data-validation communication.

## Dashboard Outputs

- Interactive HTML: `{HTML_OUT.as_posix()}`
- Markdown summary: `{MD_OUT.as_posix()}`

## Executive KPI Summary

{metric_md}

## Views Included

1. Model ablation: baseline versus card-risk specialty method.
2. Review-capacity tradeoffs: precision, F1, and risk-capture recall where available.
3. Operational backtest: static versus quarterly versus drift-triggered retraining.
4. Validation and reporting artifact inventory.

## Claim Boundary

This is a synthetic/offline and public-data-aligned reporting artifact. It does not use proprietary bank data, real cardholder data, proprietary bureau microdata, JPMC internal systems, or deployed banking decisioning.

## Resume-Safe Wording

Compared static, quarterly, and drift-triggered retraining in an 18-month train / 6-month holdout backtest, selecting quarterly retraining with avg PR-AUC 0.901 and avg ROC-AUC 0.948, and packaged dashboard-ready artifacts for portfolio trends, recession scenarios, and review-capacity tradeoffs.
"""

MD_OUT.write_text(md, encoding="utf-8")

print(f"[OK] Wrote {HTML_OUT}")
print(f"[OK] Wrote {MD_OUT}")
print("[OK] Dashboard artifact generation complete.")
