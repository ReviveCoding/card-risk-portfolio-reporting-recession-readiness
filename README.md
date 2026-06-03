# Card Risk Portfolio Reporting & Recession Readiness Analytics Framework

A SQL-first, public-data-augmented, offline card-risk analytics framework for delinquency migration, roll-rate reporting, data validation, calibrated risk scoring, residual bias correction, recession scenario analysis, and executive/regulator-style reporting.

## What this project demonstrates

This project simulates the end-to-end workflow of a card-risk reporting and recession-readiness analytics team:

1. Build a synthetic account-level card portfolio mart with realistic risk mechanisms.
2. Use public aggregate credit-card benchmarks for market context and plausibility checks.
3. Run SQL-first card-risk reporting for monthly KPIs, delinquency buckets, roll rates, vintage/cohort, segment risk, bureau-style overlays, and Tableau-ready extracts.
4. Validate reporting data quality with exception logs, control checks, and a PASS/REVIEW/BLOCK release gate.
5. Compare vanilla risk baselines against specialty-enhanced modules:
   - Credit Health Timestep, inspired by health-state alignment.
   - Structured risk path plus residual bias correction.
   - Asymmetric risk-boundary review routing.
6. Produce executive, methodology, validation, public benchmark, recession-readiness, monitoring, model-card, and mock regulator-response reports.
7. Decompose risk drivers, monitor drift with PSI, summarize monthly backtesting behavior, reconcile SQL outputs against Python recomputation, and evaluate review-capacity/scenario-sensitivity robustness.

## Claim boundaries

This project uses public aggregate credit-card risk benchmarks and synthetic account-level card portfolio data. Public aggregate datasets are used for market context and benchmark-alignment analysis. Synthetic account-level data are used only to simulate internal-style reporting, bureau-tradeline-style proxy integration, cross-LOB segmentation, and recession-readiness workflow. No proprietary bank data, real customer-level cardholder data, real bureau microdata, or production bank deployment is used or claimed.

## Data sources used as public references

The repository includes sample/fallback public-reference files so it runs offline. Optional ingestion scripts can be extended to replace these files with current public downloads.

| Source | Role in this project | Boundary |
|---|---|---|
| FRED DRCCLACBS | Credit-card delinquency aggregate benchmark | Aggregate market context only |
| FRED CORCCACBS | Credit-card charge-off aggregate benchmark | Aggregate market context only |
| Philadelphia Fed Large Bank Credit Card and Mortgage Data | Large-bank aggregate card benchmark | Aggregate FR Y-14M-derived public data, not microdata |
| UCI Default of Credit Card Clients | Public default-risk modeling benchmark | Taiwan public dataset, not a U.S. bank portfolio |
| Synthetic card mart | Account-level reporting simulation | Not real bank or bureau data |

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
make run
make test
```

The pipeline does not require internet access. It generates sample public-reference files, synthetic account-level card data, SQL outputs, model metrics, figures, and Markdown reports.

## Main commands

```bash
make run      # run the full pipeline with default sample size
make run-small # run a smaller validation sample, 500 accounts x 12 months
make test     # run pytest
make audit    # verify required artifacts and repository hygiene
make clean    # remove generated outputs, figures, reports, processed data, and database
```

## Output highlights

- `outputs/portfolio_kpi_monthly.csv`
- `outputs/roll_rate_matrix.csv`
- `outputs/model_ablation_summary.csv`
- `outputs/review_queue_comparison.csv`
- `outputs/recession_scenario_summary.csv`
- `outputs/risk_driver_decomposition.csv`
- `outputs/drift_monitoring_summary.csv`
- `outputs/backtest_validation_summary.csv`
- `outputs/tableau_dashboard_extract.csv`
- `outputs/review_capacity_sensitivity.csv`
- `outputs/scenario_sensitivity_grid.csv`
- `outputs/sql_python_reconciliation.csv`
- `outputs/source_inventory.csv`
- `outputs/artifact_manifest.csv`
- `reports/executive_risk_summary.md`
- `reports/mock_regulator_response.md`
- `reports/release_decision.md`
- `reports/control_matrix.md`
- `reports/risk_driver_decomposition_report.md`
- `reports/monitoring_drift_report.md`
- `reports/backtesting_validation_report.md`
- `reports/model_card.md`
- `reports/monitoring_plan.md`
- `reports/data_dictionary.md`
- `reports/tableau_dashboard_spec.md`
- `reports/small_data_validation_report.md`
- `reports/review_capacity_sensitivity_report.md`
- `reports/scenario_sensitivity_report.md`
- `reports/reconciliation_governance_report.md`
- `reports/responsible_use_and_fair_lending_boundary.md`
- `figures/dashboard_portfolio_overview.png`
- `figures/dashboard_roll_rate.png`
- `figures/dashboard_recession_scenario.png`
- `figures/risk_driver_contribution.png`
- `figures/drift_monitoring_psi.png`
- `figures/review_capacity_sensitivity.png`
- `figures/scenario_sensitivity_grid.png`

## Suggested resume bullets

- Built a SQL-first, public-data-augmented card-risk portfolio reporting and recession-readiness framework combining Federal Reserve/FRED credit-card delinquency and charge-off benchmarks, Philadelphia Fed large-bank aggregate card indicators, UCI public default-risk modeling data, and synthetic account-level card marts for delinquency migration, roll-rate, charge-off proxy, vintage/cohort, bureau-proxy, and high-risk segment analysis.
- Enhanced vanilla risk baselines with calibrated default modeling, segment-conditioned roll-rate diagnostics, validation-shrunk residual bias correction, credit-health timestep features inspired by health-state alignment research, and asymmetric risk-boundary review routing, improving review-queue precision/F1 while documenting calibration, benchmark-alignment, and release-gate controls.

## Latest verified run

- Full pipeline: `make run` completed successfully.
- Tests: `30 passed` in the latest reinforced release; the second reinforcement adds SQL/Python reconciliation, source-inventory, review-capacity sensitivity, scenario-sensitivity, responsible-use, and artifact-manifest tests.
- Release gate: `PASS` in the generated sample/fallback run.
- Public benchmark alignment: delinquency and charge-off proxy checks both passed the configured plausibility threshold.



## Local and GitHub runnable checks

- `scripts/run_quickstart.sh` runs the full pipeline and test suite.
- `.github/workflows/ci.yml` provides a GitHub Actions workflow using Python 3.11.
- `docs/LOCAL_RUNBOOK.md` documents local execution and expected outputs.
- `reports/small_data_validation_report.md` records a separate 500-account x 12-month smoke validation.
- `.gitignore` excludes Python cache files and local database artifacts.


## Second reinforcement loop additions

The latest reinforcement adds:

- SQL/Python reconciliation of latest-month KPI outputs.
- Source inventory and explicit public/synthetic claim-boundary artifact.
- Review-capacity sensitivity across 5%, 10%, 15%, 20%, and 30% operating points.
- Scenario-sensitivity grid and monotonicity checks for recession-readiness assumptions.
- Responsible-use and fair-lending boundary note.
- Artifact manifest in CSV/JSON form.
- Project audit command and GitHub CI audit step.

These additions strengthen the project for card-risk reporting roles by showing not only modeling and reporting outputs, but also reconciliation, operating-threshold analysis, scenario-assumption robustness, and repository-level reproducibility.
