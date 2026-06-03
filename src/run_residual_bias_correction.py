from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, brier_score_loss, roc_auc_score, average_precision_score
from .utils import ROOT, save_csv, ece_score, top_capture


def _safe_auc(metric_fn, y, p):
    try:
        return metric_fn(y, p)
    except Exception:
        return np.nan


def _choose_shrinkage(valid: pd.DataFrame) -> float:
    """Choose a conservative residual shrinkage weight on validation months.

    Including 0.0 in the grid ensures that the probability correction does not
    have to be used when it fails to improve validation calibration/error.
    """
    alphas = np.linspace(0.0, 0.8, 9)
    best_alpha, best_score = 0.0, float('inf')
    y = valid['default_next_3m']
    for a in alphas:
        prob = np.clip(valid['base_prob'] + a * valid['pred_residual_raw'], 0, 1)
        # Brier + MAE is a conservative probability-quality objective.
        score = brier_score_loss(y, prob) + mean_absolute_error(y, prob)
        if score < best_score:
            best_score, best_alpha = score, float(a)
    return best_alpha


def run_residual_bias_correction() -> pd.DataFrame:
    mart = pd.read_csv(ROOT / 'data/processed/card_risk_analytics_mart.csv')
    bureau = pd.read_csv(ROOT / 'data/synthetic/bureau_tradeline_proxy.csv')
    acct = pd.read_csv(ROOT / 'data/synthetic/accounts.csv')
    macro = pd.read_csv(ROOT / 'data/synthetic/macro_scenario_panel.csv')
    df = (
        mart.merge(bureau, on=['account_id', 'month'], how='left')
        .merge(acct[['account_id', 'income_band', 'product_type', 'state']], on='account_id', how='left')
        .merge(macro[['month', 'unemployment_rate', 'revolving_credit_growth']], on='month', how='left')
    )
    df['base_prob'] = df['segment_rollrate_prob'].fillna(df['static_rollrate_prob']).clip(0, 1)
    df['residual'] = df['default_next_3m'] - df['base_prob']

    # Time split: train / validation / out-of-time test.
    months = sorted(df['month'].unique())
    train_end = max(1, int(len(months) * 0.55))
    valid_end = max(train_end + 1, int(len(months) * 0.75))
    train_months = months[:train_end]
    valid_months = months[train_end:valid_end]
    test_months = months[valid_end:]
    if not test_months:
        test_months = months[-max(1, int(len(months) * 0.25)):]
        valid_months = months[max(1, len(months) - len(test_months) * 2):len(months) - len(test_months)]
        train_months = [m for m in months if m not in set(valid_months + test_months)]

    features = [
        'utilization', 'payment_to_balance_ratio', 'balance', 'account_age_months',
        'credit_health_timestep', 'bureau_stress_score', 'external_utilization',
        'inquiries_6m', 'external_dq_flag', 'unemployment_rate', 'revolving_credit_growth'
    ]
    for col in features:
        df[col] = df[col].fillna(df[col].median())

    train = df[df['month'].isin(train_months)].copy()
    valid = df[df['month'].isin(valid_months)].copy()
    test = df[df['month'].isin(test_months)].copy()

    model = RandomForestRegressor(
        n_estimators=120,
        min_samples_leaf=60,
        max_depth=6,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(train[features], train['residual'])
    valid['pred_residual_raw'] = model.predict(valid[features])
    test['pred_residual_raw'] = model.predict(test[features])
    alpha = _choose_shrinkage(valid)
    test['pred_residual'] = alpha * test['pred_residual_raw']
    test['residual_corrected_prob'] = np.clip(test['base_prob'] + test['pred_residual'], 0, 1)

    base_mae = mean_absolute_error(test['default_next_3m'], test['base_prob'])
    corrected_mae = mean_absolute_error(test['default_next_3m'], test['residual_corrected_prob'])
    base_brier = brier_score_loss(test['default_next_3m'], test['base_prob'])
    corrected_brier = brier_score_loss(test['default_next_3m'], test['residual_corrected_prob'])
    base_pr = _safe_auc(average_precision_score, test['default_next_3m'], test['base_prob'])
    corrected_pr = _safe_auc(average_precision_score, test['default_next_3m'], test['residual_corrected_prob'])
    base_precision, base_capture = top_capture(test['default_next_3m'], test['base_prob'], 0.10)
    corr_precision, corr_capture = top_capture(test['default_next_3m'], test['residual_corrected_prob'], 0.10)

    rows = [{
        'metric': 'out_of_time_residual_correction',
        'selected_residual_shrinkage_alpha': alpha,
        'base_mae': base_mae,
        'corrected_mae': corrected_mae,
        'mae_reduction_pct': 100 * (base_mae - corrected_mae) / base_mae if base_mae else 0,
        'base_brier': base_brier,
        'corrected_brier': corrected_brier,
        'brier_reduction_pct': 100 * (base_brier - corrected_brier) / base_brier if base_brier else 0,
        'base_ece': ece_score(test['default_next_3m'], test['base_prob']),
        'corrected_ece': ece_score(test['default_next_3m'], test['residual_corrected_prob']),
        'base_pr_auc': base_pr,
        'corrected_pr_auc': corrected_pr,
        'pr_auc_delta': corrected_pr - base_pr,
        'base_precision_at_top10pct': base_precision,
        'corrected_precision_at_top10pct': corr_precision,
        'precision_at_top10pct_delta': corr_precision - base_precision,
        'base_default_capture_at_top10pct': base_capture,
        'corrected_default_capture_at_top10pct': corr_capture,
        'default_capture_at_top10pct_delta': corr_capture - base_capture,
    }]
    save_csv(pd.DataFrame(rows), 'outputs/residual_correction_diagnostics.csv')

    ablation_row = pd.DataFrame([{
        'version': 'V5 Residual Bias Correction',
        'roc_auc': _safe_auc(roc_auc_score, test['default_next_3m'], test['residual_corrected_prob']),
        'pr_auc': corrected_pr,
        'brier': corrected_brier,
        'ece': ece_score(test['default_next_3m'], test['residual_corrected_prob']),
        'precision_at_top10pct': corr_precision,
        'default_capture_at_top10pct': corr_capture,
        'mae': corrected_mae,
    }])

    scored = df.merge(
        test[['account_id', 'month', 'pred_residual', 'residual_corrected_prob']],
        on=['account_id', 'month'], how='left'
    )
    scored['pred_residual'] = scored['pred_residual'].fillna(0)
    scored['residual_corrected_prob'] = scored['residual_corrected_prob'].fillna(scored['base_prob']).clip(0, 1)
    scored.to_csv(ROOT / 'data/processed/scored_card_risk_mart.csv', index=False)

    baseline = pd.read_csv(ROOT / 'outputs/baseline_model_metrics.csv')
    baseline_ab = baseline.rename(columns={'model': 'version'})
    save_csv(pd.concat([baseline_ab, ablation_row], ignore_index=True), 'outputs/model_ablation_summary.csv')
    return pd.DataFrame(rows)


if __name__ == '__main__':
    print(run_residual_bias_correction())
