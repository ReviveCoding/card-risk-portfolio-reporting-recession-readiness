from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
from .utils import ROOT, save_csv, load_yaml


def run_public_benchmark_alignment() -> pd.DataFrame:
    align = pd.read_csv(ROOT / 'outputs/public_benchmark_alignment.csv')
    thresholds = load_yaml('config/scenario_config.yaml').get('release_thresholds', {})
    max_mae = float(thresholds.get('max_public_benchmark_alignment_mae', 2.0))

    rows = []
    for metric, col in [
        ('delinquency_alignment_abs_error', 'delinquency_alignment_abs_error'),
        ('chargeoff_alignment_abs_error', 'chargeoff_alignment_abs_error'),
    ]:
        vals = align[col].dropna()
        mean_abs = float(vals.mean()) if len(vals) else float('nan')
        max_abs = float(vals.max()) if len(vals) else float('nan')
        rows.append({
            'metric': metric,
            'mean_abs_error': mean_abs,
            'max_abs_error': max_abs,
            'plausibility_threshold': max_mae,
            'status': 'PASS' if mean_abs <= max_mae else 'REVIEW',
        })
    summary = pd.DataFrame(rows)
    save_csv(summary, 'outputs/public_benchmark_alignment_summary.csv')

    plt.figure(figsize=(8, 5))
    plt.plot(align['quarter'], align['synthetic_dq30_plus_pct'], marker='o', label='Synthetic DQ30+ proxy')
    plt.plot(align['quarter'], align['fred_delinquency_rate_pct'], marker='o', label='FRED delinquency benchmark')
    plt.xticks(rotation=30, ha='right')
    plt.ylabel('Rate (%)')
    plt.title('Delinquency Benchmark Alignment')
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/fred_delinquency_vs_synthetic.png', dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(align['quarter'], align['synthetic_chargeoff_proxy_pct'], marker='o', label='Synthetic annualized charge-off proxy')
    plt.plot(align['quarter'], align['fred_chargeoff_rate_pct'], marker='o', label='FRED charge-off benchmark')
    plt.xticks(rotation=30, ha='right')
    plt.ylabel('Annualized rate (%)')
    plt.title('Charge-Off Benchmark Alignment')
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/fred_chargeoff_vs_synthetic.png', dpi=160)
    plt.close()
    return summary


if __name__ == '__main__':
    print(run_public_benchmark_alignment())
