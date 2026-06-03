from __future__ import annotations
import numpy as np
import pandas as pd
from .utils import ROOT, save_csv


def _eval_queue(name: str, df: pd.DataFrame, flag_col: str) -> dict:
    selected = df[flag_col].astype(bool)
    y = df['default_next_3m'].astype(int)
    exposure = df['balance'].clip(lower=0)
    captured_defaults = y[selected].sum()
    total_defaults = max(y.sum(), 1)
    review_precision = captured_defaults / max(selected.sum(), 1)
    risk_capture = captured_defaults / total_defaults
    exposure_capture = (exposure[selected] * y[selected]).sum() / max((exposure * y).sum(), 1)
    f1 = 2 * review_precision * risk_capture / max(review_precision + risk_capture, 1e-9)
    false_safe_rate = y[~selected].sum() / total_defaults
    over_review_rate = ((selected) & (y == 0)).sum() / max(selected.sum(), 1)
    return {
        'strategy': name,
        'review_queue_size': int(selected.sum()),
        'review_rate': float(selected.mean()),
        'review_precision': float(review_precision),
        'risk_capture_recall': float(risk_capture),
        'risk_review_f1': float(f1),
        'exposure_weighted_recall': float(exposure_capture),
        'false_safe_rate': float(false_safe_rate),
        'over_review_rate': float(over_review_rate),
    }


def run_risk_boundary_routing() -> pd.DataFrame:
    df = pd.read_csv(ROOT / 'data/processed/scored_card_risk_mart.csv')
    # Use latest fully scored month to emulate current reporting queue.
    latest = df['month'].max()
    current = df[df['month'] == latest].copy()
    if current['default_next_3m'].sum() == 0:
        # Use latest month with observed next-3m outcomes if final month has no forward outcome by construction.
        candidates = [m for m in sorted(df['month'].unique()) if df[df['month'] == m]['default_next_3m'].sum() > 0]
        if candidates:
            current = df[df['month'] == candidates[-1]].copy()
    k = max(1, int(len(current) * 0.10))
    base_thresh = current['base_prob'].nlargest(k).min()
    corr_thresh = current['residual_corrected_prob'].nlargest(k).min()
    current['baseline_pd_threshold'] = current['base_prob'] >= base_thresh
    weak_signal_count = (
        (current['utilization'] >= current['utilization'].quantile(.80)).astype(int)
        + (current['payment_to_balance_ratio'] <= current['payment_to_balance_ratio'].quantile(.20)).astype(int)
        + (current['bureau_stress_score'] >= current['bureau_stress_score'].quantile(.80)).astype(int)
        + (current['delinquency_bucket'].isin(['DQ30','DQ60','DQ90','CHARGEOFF'])).astype(int)
    )
    near_threshold = current['base_prob'] >= max(0, base_thresh - 0.05)
    inflated = current['baseline_pd_threshold'] | (near_threshold & (weak_signal_count >= 2))
    current['inflated_review_queue'] = inflated
    # Bias-corrected deflation: keep capacity by residual-corrected score after inflation.
    pool = current[inflated].copy()
    if len(pool) >= k:
        keep_ids = set(pool.nlargest(k, 'residual_corrected_prob')['account_id'])
    else:
        keep_ids = set(pool['account_id']) | set(current.nlargest(k-len(pool), 'residual_corrected_prob')['account_id'])
    current['arbc_review_queue'] = current['account_id'].isin(keep_ids)
    rows = [
        _eval_queue('baseline_pd_threshold', current, 'baseline_pd_threshold'),
        _eval_queue('inflated_risk_boundary', current, 'inflated_review_queue'),
        _eval_queue('asymmetric_risk_boundary_correction', current, 'arbc_review_queue'),
    ]
    out = pd.DataFrame(rows)
    save_csv(out, 'outputs/review_queue_comparison.csv')
    current[['account_id','month','base_prob','residual_corrected_prob','baseline_pd_threshold','inflated_review_queue','arbc_review_queue','default_next_3m','balance','utilization','payment_to_balance_ratio','bureau_stress_score']].to_csv(ROOT / 'outputs/current_review_queue_detail.csv', index=False)
    return out


if __name__ == '__main__':
    print(run_risk_boundary_routing())
