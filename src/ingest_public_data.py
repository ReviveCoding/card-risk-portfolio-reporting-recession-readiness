from __future__ import annotations
import numpy as np
import pandas as pd
from .utils import ensure_dirs, save_csv


def create_sample_public_data(seed: int = 42) -> None:
    ensure_dirs()
    rng = np.random.default_rng(seed)
    quarters = pd.period_range('2023Q1', '2026Q1', freq='Q')
    qstr = [str(q) for q in quarters]
    delinquency = np.array([2.55,2.62,2.70,2.78,2.88,2.98,3.08,3.12,3.06,3.04,2.98,2.94,2.92])
    chargeoff = np.array([3.10,3.25,3.50,3.82,4.05,4.35,4.55,4.62,4.46,4.21,4.15,4.07,3.84])
    philly = pd.DataFrame({
        'quarter': qstr,
        'active_accounts_millions': 500 + np.linspace(0, 24, len(qstr)) + rng.normal(0, 1.5, len(qstr)),
        'avg_cycle_end_balance': 1730 + np.linspace(0, 145, len(qstr)) + rng.normal(0, 20, len(qstr)),
        'avg_utilization_rate': 0.225 + np.linspace(0, 0.025, len(qstr)) + rng.normal(0, 0.004, len(qstr)),
        'payment_rate': 0.285 - np.linspace(0, 0.020, len(qstr)) + rng.normal(0, 0.004, len(qstr)),
        'dq30_plus_rate': delinquency / 100 + rng.normal(0, 0.001, len(qstr)),
    })
    save_csv(pd.DataFrame({'quarter': qstr, 'delinquency_rate_pct': delinquency}), 'data/public_raw/sample_fred_delinquency.csv')
    save_csv(pd.DataFrame({'quarter': qstr, 'chargeoff_rate_pct': chargeoff}), 'data/public_raw/sample_fred_chargeoff.csv')
    save_csv(philly, 'data/public_raw/sample_phillyfed_credit_card.csv')
    create_sample_uci_default(seed=seed)


def create_sample_uci_default(seed: int = 42, n: int = 8000) -> None:
    rng = np.random.default_rng(seed)
    limit_bal = rng.choice([20000, 50000, 80000, 120000, 200000, 300000, 500000], size=n, p=[.16,.20,.18,.16,.14,.10,.06])
    age = rng.integers(21, 72, size=n)
    education = rng.choice([1,2,3,4], size=n, p=[.28,.47,.22,.03])
    marriage = rng.choice([1,2,3], size=n, p=[.43,.53,.04])
    sex = rng.choice([1,2], size=n, p=[.42,.58])
    pay_status, bill_amts, pay_amts = {}, {}, {}
    latent = rng.normal(0, 1, n) - (limit_bal / 500000) * 0.8 + (age < 25) * .15 + (education == 3) * .12
    for k in range(6):
        st = np.clip(np.round(latent + rng.normal(0, 1.1, n) - 0.1*k), -2, 8).astype(int)
        pay_status[f'PAY_{k}'] = st
        util = np.clip(0.25 + 0.11*st + rng.normal(0, .18, n), 0.02, 1.45)
        bill = np.maximum(0, (limit_bal * util + rng.normal(0, 3000, n)).astype(int))
        bill_amts[f'BILL_AMT{k+1}'] = bill
        pay = np.maximum(0, (bill * np.clip(.28 - .035*st + rng.normal(0,.08,n), 0.0, .75)).astype(int))
        pay_amts[f'PAY_AMT{k+1}'] = pay
    recent_pay = np.vstack([pay_status['PAY_0'], pay_status['PAY_1'], pay_status['PAY_2']]).mean(axis=0)
    avg_util = np.mean([bill_amts[f'BILL_AMT{k+1}']/limit_bal for k in range(6)], axis=0)
    score = -2.0 + 0.55*recent_pay + 1.65*avg_util + rng.normal(0, .45, n)
    prob = 1/(1+np.exp(-score))
    default = (rng.random(n) < prob).astype(int)
    df = pd.DataFrame({'ID': np.arange(1, n+1), 'LIMIT_BAL': limit_bal, 'SEX': sex, 'EDUCATION': education, 'MARRIAGE': marriage, 'AGE': age})
    for d in [pay_status, bill_amts, pay_amts]:
        for k, v in d.items():
            df[k] = v
    df['default_next_month'] = default
    save_csv(df, 'data/public_raw/sample_uci_default.csv')


if __name__ == '__main__':
    create_sample_public_data()
