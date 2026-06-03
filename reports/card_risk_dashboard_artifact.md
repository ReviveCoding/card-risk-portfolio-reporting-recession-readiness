# Card Risk Portfolio Dashboard Artifact

This dashboard artifact supports credit-card risk reporting, portfolio monitoring, recession-readiness analysis, review-capacity decisioning, and data-validation communication.

## Dashboard Outputs

- Interactive HTML: `reports/dashboard/card_risk_portfolio_dashboard.html`
- Markdown summary: `reports/card_risk_dashboard_artifact.md`

## Executive KPI Summary

| Metric                   | Value         |
|:-------------------------|:--------------|
| PR-AUC                   | 0.332 → 0.896 |
| ROC-AUC                  | 0.692 → 0.982 |
| Top-10% Default Capture  | 0.214 → 0.967 |
| 10% Review F1            | 0.272         |
| 10% Review Precision     | 0.158         |
| Risk-Capture Recall      | 0.996         |
| Quarterly Avg PR-AUC     | 0.901         |
| Quarterly Avg ROC-AUC    | 0.948         |
| Quarterly Retrain Events | 2             |

## Views Included

1. Model ablation: baseline versus card-risk specialty method.
2. Review-capacity tradeoffs: precision, F1, and risk-capture recall where available.
3. Operational backtest: static versus quarterly versus drift-triggered retraining.
4. Validation and reporting artifact inventory.

## Claim Boundary

This is a synthetic/offline and public-data-aligned reporting artifact. It does not use proprietary bank data, real cardholder data, proprietary bureau microdata, JPMC internal systems, or deployed banking decisioning.

## Resume-Safe Wording

Compared static, quarterly, and drift-triggered retraining in an 18-month train / 6-month holdout backtest, selecting quarterly retraining with avg PR-AUC 0.901 and avg ROC-AUC 0.948, and packaged dashboard-ready artifacts for portfolio trends, recession scenarios, and review-capacity tradeoffs.
