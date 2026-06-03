# Local Runbook

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Full run

```bash
make run
make test
make audit
```

Expected result:

```text
Pipeline complete. See outputs/, figures/, and reports/.
30 passed
Project audit PASS
```

## Small-data smoke run

```bash
make clean
make run-small
make test
```

The small-data run uses 500 accounts x 12 months and validates that the pipeline does not depend on the default synthetic sample size.

## Key artifacts to review

- `reports/executive_risk_summary.md`
- `reports/release_decision.md`
- `reports/sql_reporting_pack.md`
- `reports/data_validation_report.md`
- `reports/model_validation_report.md`
- `reports/review_capacity_sensitivity_report.md`
- `reports/scenario_sensitivity_report.md`
- `reports/reconciliation_governance_report.md`
- `reports/responsible_use_and_fair_lending_boundary.md`
- `outputs/tableau_dashboard_extract.csv`
- `outputs/artifact_manifest.csv`

## Claim boundary reminder

This is an offline public/synthetic analytics project. Do not describe it as a production bank system, real bureau integration, real customer-level cardholder analysis, or regulatory submission.
