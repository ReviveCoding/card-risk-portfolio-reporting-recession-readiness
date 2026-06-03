from __future__ import annotations

import itertools
import numpy as np
import pandas as pd

from .utils import ROOT, save_csv


def run_scenario_sensitivity() -> pd.DataFrame:
    df = pd.read_csv(ROOT / 'data/processed/scored_card_risk_mart.csv')
    current = df[df['month'] == df['month'].max()].copy()
    grid = []
    for unemployment_shock_pp, util_mult, pay_mult, bureau_mult in itertools.product(
        [0.0, 1.0, 2.5, 3.5], [1.00, 1.08, 1.18], [1.00, 0.90, 0.80], [1.00, 1.20, 1.40]
    ):
        util = np.clip(current['utilization'] * util_mult, 0, 2.0)
        pay = np.clip(current['payment_to_balance_ratio'] * pay_mult, 0, 1.0)
        bureau = np.clip(current['bureau_stress_score'] * bureau_mult, 0, 2.0)
        shock = (
            0.018 * unemployment_shock_pp
            + 0.11 * (util - current['utilization']).clip(lower=0)
            + 0.16 * (current['payment_to_balance_ratio'] - pay).clip(lower=0)
            + 0.035 * (bureau - current['bureau_stress_score']).clip(lower=0)
        )
        stressed_prob = np.clip(current['residual_corrected_prob'] + shock, 0, 1)
        grid.append({
            'unemployment_shock_pp': unemployment_shock_pp,
            'utilization_multiplier': util_mult,
            'payment_ratio_multiplier': pay_mult,
            'bureau_stress_multiplier': bureau_mult,
            'avg_predicted_severe_dq_rate': float(stressed_prob.mean()),
            'expected_loss_proxy': float((stressed_prob * current['balance'] * 0.55).sum()),
            'tail_watch_flag': bool((stressed_prob.quantile(.95) > 0.35) or ((stressed_prob * current['balance']).sum() > (current['residual_corrected_prob'] * current['balance']).sum() * 1.5)),
        })
    out = pd.DataFrame(grid)
    save_csv(out, 'outputs/scenario_sensitivity_grid.csv')

    # Lightweight monotonic checks by input dimension while holding others at baseline.
    checks = []
    for dim in ['unemployment_shock_pp', 'utilization_multiplier', 'bureau_stress_multiplier']:
        base_filter = (out['payment_ratio_multiplier'] == 1.0)
        if dim != 'utilization_multiplier':
            base_filter &= out['utilization_multiplier'].eq(1.0)
        if dim != 'bureau_stress_multiplier':
            base_filter &= out['bureau_stress_multiplier'].eq(1.0)
        if dim != 'unemployment_shock_pp':
            base_filter &= out['unemployment_shock_pp'].eq(0.0)
        s = out[base_filter].sort_values(dim)
        checks.append({'dimension': dim, 'monotonic_loss_pass': bool(np.all(np.diff(s['expected_loss_proxy']) >= -1e-8)), 'points_checked': len(s)})
    # Payment ratio multiplier is inverse: lower payment ratio should increase risk.
    s = out[(out['unemployment_shock_pp'] == 0.0) & (out['utilization_multiplier'] == 1.0) & (out['bureau_stress_multiplier'] == 1.0)].sort_values('payment_ratio_multiplier', ascending=False)
    checks.append({'dimension': 'payment_ratio_multiplier_inverse', 'monotonic_loss_pass': bool(np.all(np.diff(s['expected_loss_proxy']) >= -1e-8)), 'points_checked': len(s)})
    checks_df = pd.DataFrame(checks)
    save_csv(checks_df, 'outputs/scenario_sensitivity_checks.csv')

    report = '# Scenario Sensitivity and Assumption Robustness Report\n\n'
    report += 'This report evaluates whether recession-readiness outputs behave consistently over a grid of macro, utilization, payment, and bureau-stress assumptions. It is a robustness check for scenario design, not a regulatory stress test.\n\n'
    report += '## Monotonicity checks\n\n' + checks_df.to_markdown(index=False) + '\n\n'
    report += '## Highest expected-loss scenarios\n\n' + out.sort_values('expected_loss_proxy', ascending=False).head(12).round(4).to_markdown(index=False)
    (ROOT / 'reports/scenario_sensitivity_report.md').write_text(report + '\n', encoding='utf-8')
    return out


if __name__ == '__main__':
    print(run_scenario_sensitivity().head())
