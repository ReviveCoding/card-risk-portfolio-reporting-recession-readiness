from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd

from .utils import ROOT, save_csv


def _file_meta(path: Path) -> dict:
    if not path.exists():
        return {'path': str(path.relative_to(ROOT)), 'exists': False, 'size_bytes': 0, 'modified_utc': None}
    return {
        'path': str(path.relative_to(ROOT)),
        'exists': True,
        'size_bytes': path.stat().st_size,
        'modified_utc': datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def run_reconciliation_governance() -> dict[str, pd.DataFrame]:
    snap = pd.read_csv(ROOT / 'data/synthetic/monthly_card_snapshot.csv')
    kpi = pd.read_csv(ROOT / 'outputs/portfolio_kpi_monthly.csv')
    latest_month = snap['month'].max()
    latest_snap = snap[snap['month'] == latest_month]
    latest_kpi = kpi[kpi['month'] == latest_month].iloc[0]
    recon_rows = []
    raw_active = latest_snap['account_id'].nunique()
    raw_balance = latest_snap['balance'].sum()
    raw_dq30 = latest_snap['delinquency_bucket'].isin(['DQ30', 'DQ60', 'DQ90']).mean()
    raw_dq90 = latest_snap['delinquency_bucket'].isin(['DQ90']).mean()
    raw_co = latest_snap['chargeoff_flag'].mean()
    checks = [
        ('active_accounts', raw_active, latest_kpi['active_accounts'], 0),
        ('total_balance', raw_balance, latest_kpi['total_balance'], max(raw_balance * 1e-9, 1e-6)),
        ('dq30_plus_rate', raw_dq30, latest_kpi['dq30_plus_rate'], 1e-12),
        ('dq90_plus_rate', raw_dq90, latest_kpi['dq90_plus_rate'], 1e-12),
        ('chargeoff_proxy_rate', raw_co, latest_kpi['chargeoff_proxy_rate'], 1e-12),
    ]
    for metric, raw_value, sql_value, tolerance in checks:
        delta = float(abs(float(raw_value) - float(sql_value)))
        recon_rows.append({'metric': metric, 'python_recomputed_value': raw_value, 'sql_output_value': sql_value, 'absolute_delta': delta, 'tolerance': tolerance, 'status': 'PASS' if delta <= tolerance else 'FAIL'})
    recon = pd.DataFrame(recon_rows)
    save_csv(recon, 'outputs/sql_python_reconciliation.csv')

    sources = pd.DataFrame([
        {'source_name': 'FRED DRCCLACBS', 'source_type': 'public aggregate sample/fallback', 'project_use': 'credit-card delinquency benchmark alignment', 'not_used_for': 'account-level label or bank portfolio microdata'},
        {'source_name': 'FRED CORCCACBS', 'source_type': 'public aggregate sample/fallback', 'project_use': 'credit-card charge-off benchmark alignment', 'not_used_for': 'account-level charge-off record'},
        {'source_name': 'Philadelphia Fed Large Bank Credit Card aggregate sample', 'source_type': 'public aggregate sample/fallback', 'project_use': 'large-bank card utilization/payment/performance context', 'not_used_for': 'FR Y-14M microdata'},
        {'source_name': 'UCI Default of Credit Card Clients sample', 'source_type': 'public account-level benchmark sample/fallback', 'project_use': 'default-risk modeling benchmark', 'not_used_for': 'U.S. consumer-bank production portfolio'},
        {'source_name': 'Synthetic account-level card mart', 'source_type': 'synthetic simulation', 'project_use': 'internal-style SQL reporting, bureau-proxy, cross-LOB, review-routing workflow', 'not_used_for': 'real customer/bureau/bank decisioning'},
    ])
    save_csv(sources, 'outputs/source_inventory.csv')

    tracked_patterns = ['outputs/*.csv', 'reports/*.md', 'figures/*.png', 'sql/*.sql', 'src/*.py', 'tests/*.py']
    rows = []
    for pattern in tracked_patterns:
        for p in sorted(ROOT.glob(pattern)):
            rows.append(_file_meta(p))
    manifest = pd.DataFrame(rows)
    save_csv(manifest, 'outputs/artifact_manifest.csv')
    (ROOT / 'outputs/artifact_manifest.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')

    report = '# SQL/Python Reconciliation and Source Governance Report\n\n'
    report += '## Latest-month SQL/Python reconciliation\n\n' + recon.round(8).to_markdown(index=False) + '\n\n'
    report += '## Source inventory and claim boundaries\n\n' + sources.to_markdown(index=False) + '\n\n'
    report += f'## Artifact manifest\n\nGenerated `{len(manifest)}` tracked artifacts across outputs, reports, figures, SQL, source, and tests. See `outputs/artifact_manifest.csv` and `.json`.'
    (ROOT / 'reports/reconciliation_governance_report.md').write_text(report + '\n', encoding='utf-8')

    responsible = '''# Responsible Use and Fair-Lending Boundary Note

This project is an offline reporting and analytics demonstration. It does not make customer-level credit decisions, does not generate adverse action notices, and does not use real customer or bureau microdata.

## Feature-use boundary

The primary monitoring and routing features are payment behavior, utilization, delinquency history, synthetic bureau-tradeline-style stress, vintage, product, and macro/scenario variables. Demographic or protected-class inference is not used for optimization. Public benchmark datasets are used only for aggregate plausibility and modeling demonstration.

## Appropriate use

The framework is appropriate for demonstrating SQL reporting, data controls, calibration diagnostics, review-capacity tradeoffs, scenario analysis, and executive/regulator-style documentation under public/synthetic data boundaries.

## Inappropriate use

Do not use this project for underwriting, credit-line assignment, customer treatment, adverse action, regulatory submission, or production bank monitoring.
'''
    (ROOT / 'reports/responsible_use_and_fair_lending_boundary.md').write_text(responsible, encoding='utf-8')
    return {'reconciliation': recon, 'source_inventory': sources, 'artifact_manifest': manifest}


if __name__ == '__main__':
    for name, df in run_reconciliation_governance().items():
        print(name)
        print(df.head())
