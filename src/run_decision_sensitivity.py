from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import ROOT, save_csv, load_yaml


def _eval_selection(df: pd.DataFrame, selected: pd.Series, label: str, capacity_rate: float) -> dict:
    y = df['default_next_3m'].astype(int)
    exposure = df['balance'].clip(lower=0)
    selected = selected.astype(bool)
    captured = int(y[selected].sum())
    total = max(int(y.sum()), 1)
    reviewed = max(int(selected.sum()), 1)
    precision = captured / reviewed
    recall = captured / total
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    exposure_recall = float((exposure[selected] * y[selected]).sum() / max((exposure * y).sum(), 1))
    return {
        'strategy': label,
        'capacity_rate': capacity_rate,
        'review_queue_size': int(selected.sum()),
        'review_rate': float(selected.mean()),
        'review_precision': float(precision),
        'risk_capture_recall': float(recall),
        'risk_review_f1': float(f1),
        'exposure_weighted_recall': exposure_recall,
        'false_safe_rate': float(y[~selected].sum() / total),
        'over_review_rate': float(((selected) & (y == 0)).sum() / reviewed),
        'expected_loss_proxy_capture': float((exposure[selected] * df.loc[selected, 'residual_corrected_prob']).sum()),
    }


def _latest_evaluable_month(df: pd.DataFrame) -> pd.DataFrame:
    # Use the latest month with enough forward outcome variation for meaningful queue validation.
    for m in sorted(df['month'].unique(), reverse=True):
        g = df[df['month'] == m].copy()
        if g['default_next_3m'].nunique() >= 2 and g['default_next_3m'].sum() > 0:
            return g
    return df[df['month'] == df['month'].max()].copy()


def run_decision_sensitivity() -> dict[str, pd.DataFrame]:
    cfg = load_yaml('config/model_config.yaml')['models']
    near_band = float(cfg.get('asymmetric_risk_boundary', {}).get('near_threshold_band', 0.05))
    weak_min = int(cfg.get('asymmetric_risk_boundary', {}).get('weak_signal_min_count', 2))
    df = pd.read_csv(ROOT / 'data/processed/scored_card_risk_mart.csv')
    current = _latest_evaluable_month(df)
    current = current.copy()
    weak_signal_count = (
        (current['utilization'] >= current['utilization'].quantile(.80)).astype(int)
        + (current['payment_to_balance_ratio'] <= current['payment_to_balance_ratio'].quantile(.20)).astype(int)
        + (current['bureau_stress_score'] >= current['bureau_stress_score'].quantile(.80)).astype(int)
        + (current['delinquency_bucket'].isin(['DQ30', 'DQ60', 'DQ90', 'CHARGEOFF'])).astype(int)
    )
    current['weak_signal_count'] = weak_signal_count

    capacities = [0.05, 0.10, 0.15, 0.20, 0.30]
    rows = []
    detail_rows = []
    for cap in capacities:
        k = max(1, int(len(current) * cap))
        base_thresh = current['base_prob'].nlargest(k).min()
        corr_thresh = current['residual_corrected_prob'].nlargest(k).min()
        base_sel = current['base_prob'] >= base_thresh
        corrected_sel = current['residual_corrected_prob'] >= corr_thresh
        near = current['base_prob'] >= max(0, base_thresh - near_band)
        inflated = base_sel | (near & (current['weak_signal_count'] >= weak_min))
        pool = current[inflated].copy()
        if len(pool) >= k:
            arbc_ids = set(pool.nlargest(k, 'residual_corrected_prob')['account_id'])
        else:
            arbc_ids = set(pool['account_id']) | set(current.nlargest(k-len(pool), 'residual_corrected_prob')['account_id'])
        arbc_sel = current['account_id'].isin(arbc_ids)
        # Stress-weighted review uses severe scenario sensitivity as a decision overlay, not a new PD model.
        stress_score = (
            current['residual_corrected_prob']
            + 0.05 * (current['utilization'] >= current['utilization'].quantile(.85)).astype(float)
            + 0.04 * (current['payment_to_balance_ratio'] <= current['payment_to_balance_ratio'].quantile(.15)).astype(float)
            + 0.03 * (current['bureau_stress_score'] >= current['bureau_stress_score'].quantile(.85)).astype(float)
        ).clip(0, 1)
        stress_thresh = stress_score.nlargest(k).min()
        stress_sel = stress_score >= stress_thresh
        rows += [
            _eval_selection(current, base_sel, 'baseline_pd_threshold', cap),
            _eval_selection(current, corrected_sel, 'residual_corrected_threshold', cap),
            _eval_selection(current, inflated, 'inflated_risk_boundary', cap),
            _eval_selection(current, arbc_sel, 'asymmetric_risk_boundary_correction', cap),
            _eval_selection(current, stress_sel, 'stress_weighted_review_queue', cap),
        ]
        detail_rows.append({'capacity_rate': cap, 'base_threshold': float(base_thresh), 'corrected_threshold': float(corr_thresh), 'stress_threshold': float(stress_thresh), 'inflated_pool_size': int(inflated.sum()), 'target_review_size': k})

    sensitivity = pd.DataFrame(rows)
    thresholds = pd.DataFrame(detail_rows)
    save_csv(sensitivity, 'outputs/review_capacity_sensitivity.csv')
    save_csv(thresholds, 'outputs/review_threshold_sensitivity.csv')

    best_by_cap = sensitivity.sort_values(['capacity_rate', 'risk_review_f1'], ascending=[True, False]).groupby('capacity_rate').head(1)
    report = '# Review Capacity Sensitivity Report\n\n'
    report += 'This report evaluates review-queue decisions across capacity rates, separating model ranking from operational review capacity. It helps defend why a single 10% threshold is not the only valid operating point.\n\n'
    report += '## Best strategy by capacity\n\n' + best_by_cap.round(4).to_markdown(index=False) + '\n\n'
    report += '## Full sensitivity table\n\n' + sensitivity.round(4).to_markdown(index=False)
    (ROOT / 'reports/review_capacity_sensitivity_report.md').write_text(report + '\n', encoding='utf-8')
    return {'sensitivity': sensitivity, 'thresholds': thresholds}


if __name__ == '__main__':
    for name, df in run_decision_sensitivity().items():
        print(name)
        print(df.head())
