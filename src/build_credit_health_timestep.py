from __future__ import annotations
import numpy as np
import pandas as pd
from .utils import ROOT, save_csv, load_yaml

DQ_SCORE = {'CURRENT':0.0,'DQ30':0.35,'DQ60':0.65,'DQ90':0.9,'CHARGEOFF':1.0}


def build_credit_health_timestep() -> pd.DataFrame:
    cfg = load_yaml('config/model_config.yaml')['models']['credit_health_timestep']
    mart = pd.read_csv(ROOT / 'data/processed/card_risk_analytics_mart.csv')
    bureau = pd.read_csv(ROOT / 'data/synthetic/bureau_tradeline_proxy.csv')
    macro = pd.read_csv(ROOT / 'data/synthetic/macro_scenario_panel.csv')
    df = mart.merge(bureau, on=['account_id','month'], how='left').merge(macro[['month','unemployment_rate']], on='month', how='left')
    df = df.sort_values(['account_id','month'])
    df['utilization_trend_3m'] = df.groupby('account_id')['utilization'].diff(3).fillna(0)
    df['payment_trend_3m'] = df.groupby('account_id')['payment_to_balance_ratio'].diff(3).fillna(0)
    df['dq_score'] = df['delinquency_bucket'].map(DQ_SCORE).fillna(0)
    # Normalize key behavior signals.
    def norm(s):
        denom = s.std(ddof=0)
        return (s - s.mean()) / (denom if denom and denom > 0 else 1)
    risk_age_shift_raw = (
        cfg['utilization_weight'] * norm(df['utilization'] + df['utilization_trend_3m'].clip(lower=0))
        + cfg['payment_weight'] * norm((-df['payment_to_balance_ratio']) + (-df['payment_trend_3m']).clip(lower=0))
        + cfg['delinquency_weight'] * norm(df['dq_score'])
        + cfg['bureau_weight'] * norm(df['bureau_stress_score'])
        + cfg['macro_weight'] * norm(df['unemployment_rate'])
    )
    shift = np.clip(risk_age_shift_raw * 4.0, cfg['min_shift_months'], cfg['max_shift_months'])
    df['credit_health_timestep'] = np.maximum(0, df['account_age_months'] + shift).round(2)
    out = df[['account_id','month','account_age_months','credit_health_timestep','utilization','payment_to_balance_ratio','bureau_stress_score','dq_score','default_next_3m']]
    save_csv(out, 'outputs/credit_health_timestep_features.csv')
    # Update processed mart with CHT.
    base = pd.read_csv(ROOT / 'data/processed/card_risk_analytics_mart.csv')
    base = base.merge(out[['account_id','month','credit_health_timestep']], on=['account_id','month'], how='left')
    base.to_csv(ROOT / 'data/processed/card_risk_analytics_mart.csv', index=False)
    return out


if __name__ == '__main__':
    print(build_credit_health_timestep().head())
