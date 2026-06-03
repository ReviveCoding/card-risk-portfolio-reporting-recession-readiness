from __future__ import annotations
import pandas as pd
import numpy as np
from .utils import ROOT, save_csv, load_yaml


def _result(rule, severity, failed_rows, description):
    return {
        'rule_name': rule,
        'severity': severity,
        'failed_rows': int(failed_rows),
        'status': 'PASS' if int(failed_rows) == 0 else 'FAIL',
        'description': description,
    }


def validate_data_quality() -> pd.DataFrame:
    snap = pd.read_csv(ROOT / 'data/synthetic/monthly_card_snapshot.csv')
    acct = pd.read_csv(ROOT / 'data/synthetic/accounts.csv')
    bureau = pd.read_csv(ROOT / 'data/synthetic/bureau_tradeline_proxy.csv')
    macro = pd.read_csv(ROOT / 'data/synthetic/macro_scenario_panel.csv')
    results = []
    results.append(_result('account_month_uniqueness', 'CRITICAL', snap.duplicated(['account_id','month']).sum(), 'One row per account-month in monthly card snapshot.'))
    results.append(_result('bureau_account_month_uniqueness', 'CRITICAL', bureau.duplicated(['account_id','month']).sum(), 'One bureau proxy row per account-month.'))
    results.append(_result('negative_balance', 'CRITICAL', (snap['balance'] < 0).sum(), 'Balances must be nonnegative.'))
    results.append(_result('negative_payment', 'CRITICAL', (snap['payment_amount'] < 0).sum(), 'Payments must be nonnegative.'))
    results.append(_result('utilization_range', 'WARNING', ((snap['utilization'] < 0) | (snap['utilization'] > 2.0)).sum(), 'Utilization should be in a plausible range.'))
    results.append(_result('payment_ratio_range', 'WARNING', ((snap['payment_to_balance_ratio'] < 0) | (snap['payment_to_balance_ratio'] > 1.0)).sum(), 'Payment-to-balance ratio should be within 0 to 1.'))
    allowed = {'CURRENT','DQ30','DQ60','DQ90','CHARGEOFF'}
    results.append(_result('valid_delinquency_bucket', 'CRITICAL', (~snap['delinquency_bucket'].isin(allowed)).sum(), 'Delinquency bucket must be in approved set.'))
    merged_b = snap[['account_id','month']].merge(bureau[['account_id','month']], on=['account_id','month'], how='left', indicator=True)
    results.append(_result('bureau_join_completeness', 'CRITICAL', (merged_b['_merge'] != 'both').sum(), 'All account-month records should join to bureau proxy features.'))
    merged_m = snap[['month']].drop_duplicates().merge(macro[['month']], on='month', how='left', indicator=True)
    results.append(_result('macro_month_alignment', 'CRITICAL', (merged_m['_merge'] != 'both').sum(), 'All portfolio months should have macro scenario rows.'))
    results.append(_result('account_master_join', 'CRITICAL', (~snap['account_id'].isin(acct['account_id'])).sum(), 'All snapshot records should join to account master.'))
    # invalid jump: CURRENT directly to CHARGEOFF on next month
    sorted_snap = snap.sort_values(['account_id','month'])
    next_bucket = sorted_snap.groupby('account_id')['delinquency_bucket'].shift(-1)
    invalid_jump = ((sorted_snap['delinquency_bucket'] == 'CURRENT') & (next_bucket == 'CHARGEOFF')).sum()
    results.append(_result('delinquency_transition_validity', 'WARNING', invalid_jump, 'CURRENT should not jump directly to CHARGEOFF in one month.'))
    latest = snap['month'].max()
    latest_rows = snap[snap['month'] == latest]
    results.append(_result('active_latest_month_population', 'CRITICAL', 0 if len(latest_rows) > 0 else 1, 'Latest month should contain active reporting population.'))
    df = pd.DataFrame(results)
    save_csv(df, 'outputs/validation_exception_log.csv')
    return df


if __name__ == '__main__':
    print(validate_data_quality())
