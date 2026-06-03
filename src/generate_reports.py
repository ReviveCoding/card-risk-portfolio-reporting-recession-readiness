from __future__ import annotations
import pandas as pd
from .utils import ROOT


def _fmt_pct(x):
    try:
        return f"{float(x)*100:.2f}%"
    except Exception:
        return str(x)


def _write(name: str, text: str) -> None:
    p = ROOT / 'reports' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + "\n", encoding='utf-8')


def generate_reports() -> None:
    kpi = pd.read_csv(ROOT / 'outputs/portfolio_kpi_monthly.csv')
    latest = kpi.iloc[-1]
    models = pd.read_csv(ROOT / 'outputs/model_ablation_summary.csv')
    residual = pd.read_csv(ROOT / 'outputs/residual_correction_diagnostics.csv')
    queue = pd.read_csv(ROOT / 'outputs/review_queue_comparison.csv')
    scenarios = pd.read_csv(ROOT / 'outputs/recession_scenario_summary.csv')
    validation = pd.read_csv(ROOT / 'outputs/validation_exception_log.csv')
    align = pd.read_csv(ROOT / 'outputs/public_benchmark_alignment_summary.csv')
    critical_fails = validation[(validation['severity']=='CRITICAL') & (validation['status']=='FAIL')]
    scenario_pass = bool(scenarios['core_scenario_monotonicity_pass'].iloc[0])
    min_ece = models['ece'].dropna().min() if 'ece' in models else 0
    align_mae = align['mean_abs_error'].max()
    align_review = bool((align.get('status', pd.Series(['PASS'])) == 'REVIEW').any())
    release = 'PASS'
    reasons = []
    if len(critical_fails) > 0:
        release = 'BLOCK'; reasons.append('critical data validation failure')
    if not scenario_pass:
        release = 'BLOCK'; reasons.append('scenario monotonicity failure')
    if align_review and release != 'BLOCK':
        release = 'REVIEW'; reasons.append('public benchmark alignment warning')
    if min_ece > 0.15 and release != 'BLOCK':
        release = 'REVIEW'; reasons.append('model calibration warning')
    if not reasons:
        reasons.append('all critical checks passed')
    reason_text = ', '.join(reasons)

    _write('executive_risk_summary.md', f'''
# Executive Risk Summary

## Release decision

**{release}**: {reason_text}.

## Latest reporting month

- Month: {latest['month']}
- Active accounts: {int(latest['active_accounts']):,}
- Total balance: ${latest['total_balance']:,.0f}
- Average utilization: {_fmt_pct(latest['avg_utilization'])}
- DQ30+ rate: {_fmt_pct(latest['dq30_plus_rate'])}
- DQ90+ rate: {_fmt_pct(latest['dq90_plus_rate'])}
- Charge-off proxy rate: {_fmt_pct(latest['chargeoff_proxy_rate'])}

## Management readout

The framework identifies risk pressure from utilization growth, deteriorating payment-to-balance behavior, bureau-tradeline-style stress proxies, and delinquency migration. It produces SQL-first portfolio reporting, validation exceptions, vanilla baseline metrics, specialty-enhanced risk scoring, recession scenario outputs, and review-queue tradeoff diagnostics.

## Decision recommendation

Use the SQL reporting pack for recurring portfolio monitoring, use the residual-corrected score for out-of-time severe-delinquency risk ranking, and use the asymmetric risk-boundary routing layer when review capacity must balance risk capture against review burden.
''')

    _write('sql_reporting_pack.md', '''
# SQL Reporting Pack

Generated SQL outputs:

- `portfolio_kpi_monthly.csv`
- `delinquency_bucket_distribution.csv`
- `roll_rate_matrix.csv`
- `vintage_cohort_report.csv`
- `segment_risk_report.csv`
- `bureau_overlay_report.csv`
- `cross_lob_segment_report.csv`
- `public_benchmark_alignment.csv`
- `tableau_dashboard_extract.csv`

The SQL layer covers monthly portfolio KPIs, DQ bucket distribution, roll-rate migration, vintage/cohort views, FICO/utilization/payment segments, bureau-tradeline-style overlays, cross-LOB relationship views, public benchmark alignment, and a Tableau-ready extract.
''')

    _write('data_validation_report.md', '# Data Validation Report\n\n' + validation.to_markdown(index=False))

    controls = pd.DataFrame([
        {'control_id':'C01','control':'Account-month uniqueness','risk_addressed':'Duplicate reporting rows','evidence':'validation_exception_log.csv','severity':'CRITICAL'},
        {'control_id':'C02','control':'Balance/payment non-negativity','risk_addressed':'Invalid financial fields','evidence':'validation_exception_log.csv','severity':'CRITICAL'},
        {'control_id':'C03','control':'Delinquency transition validity','risk_addressed':'Impossible or excessive bucket migration','evidence':'validation_exception_log.csv; roll_rate_matrix.csv','severity':'CRITICAL'},
        {'control_id':'C04','control':'Bureau-proxy join completeness','risk_addressed':'Third-party/proxy data coverage gaps','evidence':'validation_exception_log.csv; bureau_overlay_report.csv','severity':'WARNING'},
        {'control_id':'C05','control':'Macro month alignment','risk_addressed':'Scenario and reporting period mismatch','evidence':'validation_exception_log.csv','severity':'CRITICAL'},
        {'control_id':'C06','control':'Public benchmark plausibility','risk_addressed':'Synthetic portfolio not aligned to aggregate market context','evidence':'public_benchmark_alignment_summary.csv','severity':'WARNING'},
        {'control_id':'C07','control':'Scenario monotonicity','risk_addressed':'Stress scenario inconsistencies','evidence':'recession_scenario_summary.csv','severity':'CRITICAL'},
        {'control_id':'C08','control':'Release gate decision','risk_addressed':'Uncontrolled report publication','evidence':'release_decision.md','severity':'CRITICAL'},
    ])
    _write('control_matrix.md', '# Reporting Control Matrix\n\n' + controls.to_markdown(index=False))

    tableau_spec = """
# Tableau Dashboard Specification

## Purpose

Provide a Tableau-ready dashboard design for recurring card-risk portfolio monitoring, recession-readiness review, and executive readout.

## Data source

`outputs/tableau_dashboard_extract.csv`

## Recommended dashboard tabs

1. **Portfolio Overview**: active accounts, total balance, average utilization, DQ30+, DQ90+, monthly charge-off proxy, next-3M severe-DQ proxy.
2. **Delinquency Roll-Rate Monitor**: current bucket to next bucket transition matrix, deterioration and cure trends.
3. **Vintage / Cohort View**: DQ30+ and DQ90+ by account-age band and origination vintage.
4. **Segment Risk View**: FICO band, utilization band, payment-to-balance band, state, and product cuts.
5. **Bureau Proxy Overlay**: external utilization, inquiries, external DQ flag, and bureau-stress score by segment.
6. **Recession Scenario Monitor**: baseline, mild, severe, payment-deterioration, high-utilization, and combined-tail stress outcomes.
7. **Review Queue Monitor**: baseline threshold, inflated queue, and asymmetric risk-boundary corrected queue tradeoffs.
8. **Data Quality & Release Gate**: validation exceptions, public benchmark alignment, scenario monotonicity, and PASS/REVIEW/BLOCK decision.

## Included dashboard mock figures

- `figures/dashboard_portfolio_overview.png`
- `figures/dashboard_roll_rate.png`
- `figures/dashboard_recession_scenario.png`
"""
    _write('tableau_dashboard_spec.md', tableau_spec)
    _write('model_validation_report.md', '# Model Validation Report\n\n' + models.round(4).to_markdown(index=False) + '\n\nMetrics emphasize calibration, PR-AUC, Precision@Top10%, default capture, and MAE rather than ROC-AUC alone.')
    _write('residual_bias_correction_report.md', '# Residual Bias Correction Report\n\n' + residual.round(4).to_markdown(index=False) + '\n\nThe residual layer learns errors from a structured segment-conditioned roll-rate path and applies a validation-selected shrinkage weight before adding the correction to the expected risk path. Probability quality is evaluated with MAE/Brier/ECE, while risk-ranking utility is evaluated with PR-AUC, Precision@Top10%, and default capture. The report intentionally documents tradeoffs instead of assuming every metric must improve.')
    _write('risk_boundary_review_routing_report.md', '# Risk Boundary Review Routing Report\n\n' + queue.round(4).to_markdown(index=False) + '\n\nThe asymmetric routing layer first inflates the candidate review set using weak but informative risk signals, then deflates/re-ranks the queue using residual-corrected risk scores.')
    _write('recession_readiness_report.md', '# Recession Readiness Report\n\n' + scenarios.round(4).to_markdown(index=False) + '\n\nScenario outputs compare baseline, mild, severe, high-utilization, payment deterioration, and combined tail stress conditions.')
    _write('public_benchmark_alignment_report.md', '# Public Benchmark Alignment Report\n\n' + align.round(4).to_markdown(index=False) + '\n\nPublic aggregate benchmarks are used for plausibility and market-context checks only, not as account-level labels.')
    _write('methodology_note.md', '''
# Methodology Note

## Intended use

Offline portfolio analytics demonstration for card-risk reporting, recession-readiness analysis, and model-validation style documentation.

## Data boundary

Public aggregate datasets are used for market context and benchmark alignment. Synthetic account-level data simulate internal-style card reporting, bureau-tradeline-style proxy integration, cross-LOB segmentation, and recession scenario analysis. No proprietary bank, real customer, or real bureau microdata are used.

## Modeling boundary

Vanilla baselines include logistic regression, calibrated logistic regression, HistGradientBoosting, static roll-rate, and segment-conditioned roll-rate. Specialty enhancements include Credit Health Timestep, residual bias correction, and asymmetric risk-boundary review routing.

## Limitations

The synthetic portfolio does not represent an actual bank portfolio. Public aggregate data cannot validate account-level behavior. The UCI benchmark is a public Taiwan default dataset and should not be interpreted as a U.S. consumer-bank production portfolio.
''')
    _write('mock_regulator_response.md', f'''
# Mock Regulator-Style Response

## Request

Explain the data sources, risk metrics, model methodology, validation controls, and recession-readiness assumptions used in the card-risk reporting framework.

## Response summary

The framework uses public aggregate credit-card benchmarks and synthetic account-level account-month data. It produces SQL reporting for delinquency migration, roll rates, vintage/cohort behavior, segment risk, and charge-off proxies. It includes validation checks for account-month uniqueness, bureau-proxy join completeness, macro month alignment, range checks, delinquency transition validity, and release-gate decisions.

## Release decision

**{release}**: {reason_text}.

## Known limitations

This is an offline public/synthetic analytics project. It does not use proprietary bank data, real bureau microdata, real cardholder records, or production bank infrastructure.
''')
    _write('release_decision.md', f'# Release Decision\n\n**{release}**\n\nReasons: {reason_text}.\n')


if __name__ == '__main__':
    generate_reports()
