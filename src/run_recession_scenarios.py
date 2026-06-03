from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .utils import ROOT, save_csv, load_yaml


def run_recession_scenarios() -> pd.DataFrame:
    cfg = load_yaml('config/scenario_config.yaml')['scenarios']
    df = pd.read_csv(ROOT / 'data/processed/scored_card_risk_mart.csv')
    latest = df['month'].max()
    current = df[df['month'] == latest].copy()
    if current['residual_corrected_prob'].isna().all():
        current['residual_corrected_prob'] = current['base_prob']
    rows = []
    for name, sc in cfg.items():
        util = np.clip(current['utilization'] * sc['utilization_multiplier'], 0, 2.0)
        pay = np.clip(current['payment_to_balance_ratio'] * sc['payment_ratio_multiplier'], 0, 1.0)
        bureau = np.clip(current['bureau_stress_score'] * sc['bureau_stress_multiplier'], 0, 2.0)
        shock = 0.018*sc['unemployment_shock_pp'] + 0.11*(util - current['utilization']).clip(lower=0) + 0.16*(current['payment_to_balance_ratio'] - pay).clip(lower=0) + 0.035*(bureau - current['bureau_stress_score']).clip(lower=0)
        stressed_prob = np.clip(current['residual_corrected_prob'] + shock, 0, 1)
        rows.append({
            'scenario': name,
            'avg_predicted_severe_dq_rate': float(stressed_prob.mean()),
            'expected_severe_dq_accounts': float(stressed_prob.sum()),
            'expected_loss_proxy': float((stressed_prob * current['balance'] * 0.55).sum()),
            'avg_utilization': float(util.mean()),
            'avg_payment_to_balance_ratio': float(pay.mean()),
            'avg_bureau_stress_score': float(bureau.mean()),
            'unemployment_shock_pp': sc['unemployment_shock_pp'],
        })
    out = pd.DataFrame(rows)
    severity_order = {'baseline':0,'mild_recession':1,'severe_recession':2,'combined_tail_stress':3}
    mono_subset = out[out['scenario'].isin(severity_order)].copy()
    mono_subset['order'] = mono_subset['scenario'].map(severity_order)
    mono_subset = mono_subset.sort_values('order')
    monotonic_pass = bool(np.all(np.diff(mono_subset['avg_predicted_severe_dq_rate']) >= -1e-8) and np.all(np.diff(mono_subset['expected_loss_proxy']) >= -1e-8))
    out['core_scenario_monotonicity_pass'] = monotonic_pass
    save_csv(out, 'outputs/recession_scenario_summary.csv')
    plt.figure(figsize=(9, 5))
    plt.bar(out['scenario'], out['expected_loss_proxy'])
    plt.xticks(rotation=30, ha='right')
    plt.ylabel('Expected loss proxy')
    plt.title('Recession Readiness Scenario Expected Loss Proxy')
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/recession_scenario_waterfall.png', dpi=160)
    plt.close()
    return out


if __name__ == '__main__':
    print(run_recession_scenarios())
