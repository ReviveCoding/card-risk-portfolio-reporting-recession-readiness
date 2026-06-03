from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, average_precision_score

from .utils import ROOT, save_csv, ece_score, top_capture


def _band_util(x: pd.Series) -> pd.Series:
    return pd.cut(
        x.fillna(0),
        bins=[-0.001, 0.30, 0.60, 0.80, 1.00, np.inf],
        labels=['u00_30', 'u30_60', 'u60_80', 'u80_100', 'u100_plus'],
    ).astype(str)


def _band_payment(x: pd.Series) -> pd.Series:
    return pd.cut(
        x.fillna(0),
        bins=[-0.001, 0.03, 0.08, 0.15, 0.30, np.inf],
        labels=['p00_03', 'p03_08', 'p08_15', 'p15_30', 'p30_plus'],
    ).astype(str)


def _band_bureau(x: pd.Series) -> pd.Series:
    return pd.cut(
        x.fillna(0),
        bins=[-0.001, 0.20, 0.40, 0.60, 0.80, np.inf],
        labels=['b00_20', 'b20_40', 'b40_60', 'b60_80', 'b80_plus'],
    ).astype(str)


def _safe_pr_auc(y: pd.Series, p: pd.Series) -> float:
    try:
        return float(average_precision_score(y, p))
    except Exception:
        return np.nan


def _psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    expected = pd.to_numeric(expected, errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
    actual = pd.to_numeric(actual, errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
    if expected.empty or actual.empty:
        return np.nan
    qs = np.linspace(0, 1, bins + 1)
    edges = np.unique(np.quantile(expected, qs))
    if len(edges) < 3:
        lo = min(expected.min(), actual.min())
        hi = max(expected.max(), actual.max())
        if lo == hi:
            return 0.0
        edges = np.linspace(lo, hi, bins + 1)
    edges[0] = -np.inf
    edges[-1] = np.inf
    e_counts = pd.cut(expected, edges, include_lowest=True).value_counts(sort=False)
    a_counts = pd.cut(actual, edges, include_lowest=True).value_counts(sort=False)
    e_pct = (e_counts / max(e_counts.sum(), 1)).replace(0, 1e-6)
    a_pct = (a_counts / max(a_counts.sum(), 1)).replace(0, 1e-6)
    return float(((a_pct - e_pct) * np.log(a_pct / e_pct)).sum())


def _psi_status(psi_value: float) -> str:
    if pd.isna(psi_value):
        return 'MISSING'
    if psi_value < 0.10:
        return 'PASS'
    if psi_value < 0.25:
        return 'WATCH'
    return 'REVIEW'


def _write_report(name: str, text: str) -> None:
    path = ROOT / 'reports' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + '\n', encoding='utf-8')


def run_risk_driver_monitoring() -> dict[str, pd.DataFrame]:
    scored = pd.read_csv(ROOT / 'data/processed/scored_card_risk_mart.csv')
    cross = pd.read_csv(ROOT / 'data/synthetic/cross_lob_relationships.csv')
    scored = scored.merge(cross, on='account_id', how='left')
    scored['expected_loss_proxy'] = scored['balance'].clip(lower=0) * scored['residual_corrected_prob'].clip(0, 1) * 0.85
    scored['credit_health_shift'] = (scored['credit_health_timestep'] - scored['account_age_months']).fillna(0)
    scored['utilization_band'] = _band_util(scored['utilization'])
    scored['payment_band'] = _band_payment(scored['payment_to_balance_ratio'])
    scored['bureau_stress_band'] = _band_bureau(scored['bureau_stress_score'])
    scored['relationship_depth_band'] = scored['relationship_depth'].fillna(0).astype(int).clip(0, 3).astype(str)

    latest_month = scored['month'].max()
    latest = scored[scored['month'] == latest_month].copy()
    total_expected_loss = max(latest['expected_loss_proxy'].sum(), 1e-9)
    risk_rows = []
    for driver_col in [
        'fico_band', 'utilization_band', 'payment_band', 'bureau_stress_band',
        'relationship_depth_band', 'product_type', 'state'
    ]:
        g = latest.groupby(driver_col, dropna=False).agg(
            accounts=('account_id', 'nunique'),
            total_balance=('balance', 'sum'),
            avg_utilization=('utilization', 'mean'),
            avg_payment_to_balance=('payment_to_balance_ratio', 'mean'),
            avg_bureau_stress=('bureau_stress_score', 'mean'),
            avg_risk_score=('residual_corrected_prob', 'mean'),
            observed_default_rate=('default_next_3m', 'mean'),
            expected_loss_proxy=('expected_loss_proxy', 'sum'),
        ).reset_index().rename(columns={driver_col: 'driver_value'})
        g.insert(0, 'driver', driver_col)
        risk_rows.append(g)
    drivers = pd.concat(risk_rows, ignore_index=True)
    drivers['expected_loss_contribution_share'] = drivers['expected_loss_proxy'] / total_expected_loss
    drivers = drivers.sort_values('expected_loss_contribution_share', ascending=False)
    save_csv(drivers, 'outputs/risk_driver_decomposition.csv')

    top = drivers.head(12).copy()
    _write_report('risk_driver_decomposition_report.md', '# Risk Driver Decomposition Report\n\n' + top.round(4).to_markdown(index=False) + '\n\nThis report decomposes the latest reporting month by risk drivers used in card-risk monitoring: FICO band, utilization, payment behavior, bureau-tradeline-style stress, relationship depth, product, and state. Expected-loss contribution is proxy-based and uses synthetic account-level data only.')

    months = sorted(scored['month'].unique())
    baseline_months = months[:max(1, min(3, len(months)//3))]
    recent_months = months[-max(1, min(3, len(months)//3)):]
    baseline = scored[scored['month'].isin(baseline_months)]
    recent = scored[scored['month'].isin(recent_months)]
    drift_rows = []
    for col in ['utilization', 'payment_to_balance_ratio', 'bureau_stress_score', 'credit_health_shift', 'residual_corrected_prob', 'balance']:
        val = _psi(baseline[col], recent[col])
        drift_rows.append({
            'feature': col,
            'baseline_window': f'{baseline_months[0]} to {baseline_months[-1]}',
            'recent_window': f'{recent_months[0]} to {recent_months[-1]}',
            'psi': val,
            'status': _psi_status(val),
        })
    drift = pd.DataFrame(drift_rows)
    save_csv(drift, 'outputs/drift_monitoring_summary.csv')
    _write_report('monitoring_drift_report.md', '# Monitoring and Drift Report\n\n' + drift.round(4).to_markdown(index=False) + '\n\nPSI thresholds: PASS < 0.10, WATCH < 0.25, REVIEW >= 0.25. `credit_health_shift` is monitored instead of raw Credit Health Timestep because raw timestep naturally increases as a portfolio matures. The report is a monitoring-style artifact for local/public-synthetic demonstration, not a bank production monitoring system.')

    stability = scored.groupby(['month', 'fico_band']).agg(
        accounts=('account_id', 'nunique'),
        observed_default_rate=('default_next_3m', 'mean'),
        avg_score=('residual_corrected_prob', 'mean'),
        expected_loss_proxy=('expected_loss_proxy', 'sum'),
    ).reset_index()
    segment = stability.groupby('fico_band').agg(
        months_observed=('month', 'nunique'),
        min_default_rate=('observed_default_rate', 'min'),
        max_default_rate=('observed_default_rate', 'max'),
        avg_default_rate=('observed_default_rate', 'mean'),
        avg_score=('avg_score', 'mean'),
        total_expected_loss_proxy=('expected_loss_proxy', 'sum'),
    ).reset_index()
    segment['default_rate_range'] = segment['max_default_rate'] - segment['min_default_rate']
    segment['stability_status'] = np.where(segment['default_rate_range'] < 0.05, 'PASS', np.where(segment['default_rate_range'] < 0.12, 'WATCH', 'REVIEW'))
    save_csv(segment, 'outputs/segment_stability_report.csv')

    # Monthly out-of-time style backtesting on scored account-month rows with known target.
    back_rows = []
    for m, g in scored.groupby('month'):
        if g['default_next_3m'].nunique() < 2:
            continue
        prec, cap = top_capture(g['default_next_3m'], g['residual_corrected_prob'], 0.10)
        back_rows.append({
            'month': m,
            'accounts': len(g),
            'observed_default_rate': g['default_next_3m'].mean(),
            'avg_score': g['residual_corrected_prob'].mean(),
            'brier': brier_score_loss(g['default_next_3m'], g['residual_corrected_prob']),
            'ece': ece_score(g['default_next_3m'], g['residual_corrected_prob']),
            'pr_auc': _safe_pr_auc(g['default_next_3m'], g['residual_corrected_prob']),
            'precision_at_top10pct': prec,
            'default_capture_at_top10pct': cap,
        })
    backtest = pd.DataFrame(back_rows)
    save_csv(backtest, 'outputs/backtest_validation_summary.csv')
    if backtest.empty:
        back_md = 'No backtest rows with both positive and negative outcomes were available.'
    else:
        back_md = backtest.tail(8).round(4).to_markdown(index=False)
    _write_report('backtesting_validation_report.md', '# Backtesting Validation Report\n\n' + back_md + '\n\nBacktesting summarizes monthly scoring behavior using known synthetic forward outcomes. It emphasizes calibration and top-capacity capture rather than accuracy alone.')

    # Data dictionary for reporting and interview defense.
    dictionary = pd.DataFrame([
        {'field': 'DQ30+ rate', 'definition': 'Share of active account-months in DQ30, DQ60, or DQ90 buckets; charge-off proxy is reported separately.', 'source': 'monthly_card_snapshot / SQL reporting'},
        {'field': 'roll-rate', 'definition': 'Transition rate from a prior delinquency bucket to a next-month bucket.', 'source': 'monthly_card_snapshot SQL lag query'},
        {'field': 'charge-off proxy', 'definition': 'Synthetic proxy for accounts in severe delinquency or charge-off state; not real bank loss data.', 'source': 'synthetic portfolio'},
        {'field': 'bureau_stress_score', 'definition': 'Synthetic bureau-tradeline-style proxy derived from external utilization, inquiries, and external delinquency flag.', 'source': 'bureau_tradeline_proxy'},
        {'field': 'Credit Health Timestep', 'definition': 'Behavior-adjusted account maturity feature inspired by health-state alignment; replaces raw account age in specialty experiments.', 'source': 'CHT module'},
        {'field': 'risk_capture_recall', 'definition': 'Share of default_next_3m outcomes captured by a review queue.', 'source': 'risk-boundary routing'},
        {'field': 'over_review_rate', 'definition': 'Share of reviewed accounts that do not realize the synthetic severe-delinquency target.', 'source': 'risk-boundary routing'},
        {'field': 'PSI', 'definition': 'Population Stability Index comparing baseline and recent feature distributions.', 'source': 'monitoring layer'},
    ])
    save_csv(dictionary, 'outputs/reporting_data_dictionary.csv')
    _write_report('data_dictionary.md', '# Reporting Data Dictionary\n\n' + dictionary.to_markdown(index=False))

    _write_report('model_card.md', f'''
# Model Card and Use Boundary

## Intended use
Offline card-risk reporting and recession-readiness analytics demonstration for public/synthetic data.

## Not intended for
Production credit decisioning, adverse action, customer-level underwriting, bank regulatory submission, or use with real bureau/customer records.

## Data
Public aggregate benchmarks are used for plausibility only. Synthetic account-level records simulate portfolio reporting workflows.

## Models
Vanilla baselines include logistic regression, calibrated logistic regression, random forest, static roll-rate, and segment-conditioned roll-rate. Specialty layers include Credit Health Timestep, validation-shrunk residual correction, and asymmetric risk-boundary routing.

## Monitoring
Drift is monitored with PSI; score and segment stability are summarized in `monitoring_drift_report.md` and `backtesting_validation_report.md`.

## Latest data window
Latest reporting month in this run: {latest_month}.
''')

    _write_report('monitoring_plan.md', '''
# Monitoring Plan

## Cadence
Monthly portfolio refresh, quarterly public benchmark alignment, and ad hoc recession scenario refresh.

## Monitored controls
- Account-month uniqueness and reconciliation
- Bureau-proxy join completeness
- Macro month alignment
- DQ transition validity
- Feature drift PSI
- Score calibration and PR-AUC
- Top-capacity default capture
- Scenario monotonicity
- Public benchmark plausibility

## Trigger actions
- PASS: continue reporting and document results.
- WATCH: review feature drift or calibration change in the next cycle.
- REVIEW: document root cause, inspect segments, and hold executive interpretation until resolved.
- BLOCK: do not publish risk conclusions until critical validation failures are fixed.
''')

    return {
        'drivers': drivers,
        'drift': drift,
        'segment_stability': segment,
        'backtest': backtest,
    }


if __name__ == '__main__':
    for k, v in run_risk_driver_monitoring().items():
        print('\n', k)
        print(v.head())
