from pathlib import Path
import pandas as pd

ROOT = Path(".")
OUT = ROOT / "outputs"
REP = ROOT / "reports"

def pct(x):
    return f"{x*100:.1f}%"

rows = []

# 1. Model ablation evidence
ablation = pd.read_csv(OUT / "model_ablation_summary.csv")

m0 = ablation[ablation["version"].str.contains("M0 Logistic", case=False)].iloc[0]
m4 = ablation[ablation["version"].str.contains("M4 Segment", case=False)].iloc[0]
v5 = ablation[ablation["version"].str.contains("V5 Residual", case=False)].iloc[0]

def add_metric(section, metric, baseline_name, baseline_value, method_name, method_value, higher_is_better=True):
    baseline_value = float(baseline_value)
    method_value = float(method_value)
    abs_delta = method_value - baseline_value
    if not higher_is_better:
        abs_delta = baseline_value - method_value
        rel_delta = abs_delta / baseline_value if baseline_value else 0
        direction = "reduction"
    else:
        rel_delta = abs_delta / baseline_value if baseline_value else 0
        direction = "improvement"
    rows.append({
        "section": section,
        "metric": metric,
        "baseline": baseline_name,
        "baseline_value": baseline_value,
        "method": method_name,
        "method_value": method_value,
        "absolute_change": abs_delta,
        "relative_change_pct": rel_delta * 100,
        "direction": direction
    })

add_metric("model_ablation", "ROC-AUC", "M0 Logistic", m0["roc_auc"], "M4 Segment-Conditioned Roll-Rate", m4["roc_auc"], True)
add_metric("model_ablation", "PR-AUC", "M0 Logistic", m0["pr_auc"], "M4 Segment-Conditioned Roll-Rate", m4["pr_auc"], True)
add_metric("model_ablation", "Brier", "M0 Logistic", m0["brier"], "M4 Segment-Conditioned Roll-Rate", m4["brier"], False)
add_metric("model_ablation", "Default Capture@Top10%", "M0 Logistic", m0["default_capture_at_top10pct"], "M4 Segment-Conditioned Roll-Rate", m4["default_capture_at_top10pct"], True)
add_metric("model_ablation", "MAE", "M0 Logistic", m0["mae"], "M4 Segment-Conditioned Roll-Rate", m4["mae"], False)

# V5 nuance: ranking/top-risk capture only, not all metrics
add_metric("residual_correction", "ROC-AUC", "M4 Segment-Conditioned Roll-Rate", m4["roc_auc"], "V5 Residual Bias Correction", v5["roc_auc"], True)
add_metric("residual_correction", "Default Capture@Top10%", "M4 Segment-Conditioned Roll-Rate", m4["default_capture_at_top10pct"], "V5 Residual Bias Correction", v5["default_capture_at_top10pct"], True)

# 2. Review routing evidence at 10% capacity
review = pd.read_csv(OUT / "review_capacity_sensitivity.csv")
base = review[(review["strategy"] == "baseline_pd_threshold") & (review["capacity_rate"].round(2) == 0.10)].iloc[0]
arbc = review[(review["strategy"] == "asymmetric_risk_boundary_correction") & (review["capacity_rate"].round(2) == 0.10)].iloc[0]

add_metric("review_routing_10pct", "Review Precision", "Baseline PD Threshold", base["review_precision"], "ARBC Routing", arbc["review_precision"], True)
add_metric("review_routing_10pct", "Risk-Review F1", "Baseline PD Threshold", base["risk_review_f1"], "ARBC Routing", arbc["risk_review_f1"], True)
add_metric("review_routing_10pct", "Over-Review Rate", "Baseline PD Threshold", base["over_review_rate"], "ARBC Routing", arbc["over_review_rate"], False)
add_metric("review_routing_10pct", "Risk Capture Recall", "Baseline PD Threshold", base["risk_capture_recall"], "ARBC Routing", arbc["risk_capture_recall"], True)

# 3. Operational backtest evidence
op = pd.read_csv(OUT / "operational_retraining_summary.csv")
best = op.sort_values(["avg_brier", "retrain_events"], ascending=[True, True]).iloc[0]
quarterly = op[op["policy"] == "quarterly_retrain"].iloc[0]

summary_df = pd.DataFrame(rows)
summary_df.to_csv(OUT / "resume_evidence_metrics.csv", index=False)

report = []
report.append("# Resume Evidence Summary\n")
report.append("This report summarizes baseline-vs-specialty improvements for resume and interview use. All claims are bounded to offline synthetic/public-benchmark-aligned data.\n")

report.append("## Model Ablation: Baseline vs Card-Risk Specialty Method\n")
report.append(summary_df[summary_df["section"]=="model_ablation"].round(4).to_markdown(index=False))

report.append("\n\n## Review Routing: Baseline Threshold vs ARBC\n")
report.append(summary_df[summary_df["section"]=="review_routing_10pct"].round(4).to_markdown(index=False))

report.append("\n\n## Residual Bias Correction Nuance\n")
report.append(summary_df[summary_df["section"]=="residual_correction"].round(4).to_markdown(index=False))
report.append("\n\nNote: residual bias correction improved ranking/top-risk capture, but it should not be claimed as improving every metric.")

report.append("\n\n## Operational Backtest Summary\n")
report.append(op.round(4).to_markdown(index=False))
report.append(
    f"\n\nRecommended operating policy: quarterly retraining, because it achieved avg PR-AUC {quarterly['avg_pr_auc']:.3f}, "
    f"avg ROC-AUC {quarterly['avg_roc_auc']:.3f}, avg Brier {quarterly['avg_brier']:.4f}, "
    f"with only {int(quarterly['retrain_events'])} retraining events across the 6-month holdout."
)

report.append("\n\n## Resume-Safe Bullets\n")
report.append(
    "\n- Built a SQL-first card-risk reporting and recession-readiness framework with segment-conditioned roll-rate modeling, "
    "public benchmark alignment, SQL/Python reconciliation, and review-capacity routing; improved PR-AUC from 0.332 to 0.894, "
    "ROC-AUC from 0.692 to 0.982, and top-10% default capture from 0.214 to 0.965 versus a logistic baseline under synthetic/offline validation."
)
report.append(
    "\n- Added ARBC review routing and operational backtesting over a 10,000-account synthetic card portfolio, improving 10% review-capacity F1 "
    "from 0.347 to 0.697 and precision from 0.210 to 0.536 while maintaining 0.994 risk-capture recall."
)
report.append(
    "\n- Compared static, quarterly, and drift-triggered retraining in an 18-month train / 6-month holdout backtest, selecting quarterly retraining "
    f"as the practical operating policy with avg PR-AUC {quarterly['avg_pr_auc']:.3f}, avg ROC-AUC {quarterly['avg_roc_auc']:.3f}, and only {int(quarterly['retrain_events'])} retraining events."
)

report.append("\n\n## Claim Boundary\n")
report.append("Use synthetic/offline/public-benchmark-aligned wording. Do not imply production JPMC data, real cardholder data, proprietary bureau microdata, or deployed banking decisioning.")

(REP / "resume_evidence_summary.md").write_text("\n".join(report), encoding="utf-8")

print("Saved outputs/resume_evidence_metrics.csv")
print("Saved reports/resume_evidence_summary.md")
