from __future__ import annotations
import numpy as np
import pandas as pd
from .utils import load_yaml, month_range, month_to_quarter, save_csv, ensure_dirs
from .ingest_public_data import create_sample_public_data

FICO_BANDS = ['subprime','near_prime','prime','super_prime']
DQ_ORDER = ['CURRENT','DQ30','DQ60','DQ90','CHARGEOFF']
STATES = ['NJ','NY','PA','CT','DE','CA','TX','FL','IL','OH']
PRODUCTS = ['cash_back','travel','student','secured','premium']
INCOME = ['low','moderate','middle','upper']


def _risk_scale(fico_band: str) -> float:
    return {'subprime': 1.55, 'near_prime': 1.15, 'prime': 0.72, 'super_prime': 0.42}[fico_band]


def _transition(prev_bucket: str, risk: float, cure_signal: float, rng: np.random.Generator) -> str:
    """Monthly delinquency migration model.

    The parameters intentionally keep the *baseline* synthetic portfolio close to
    public aggregate card-risk benchmarks, while still producing enough stressed
    accounts for roll-rate, review-queue, and recession-readiness analyses.
    """
    if prev_bucket == 'CHARGEOFF':
        return 'CHARGEOFF'

    # Baseline deterioration is calibrated to keep DQ30+ in a plausible
    # single-digit range; stressed scenarios are handled downstream.
    p_worse = np.clip(0.0025 + 0.024 * risk, 0.0015, 0.060)
    p_cure = np.clip(0.48 * cure_signal + 0.10, 0.06, 0.70)
    u = rng.random()

    if prev_bucket == 'CURRENT':
        return 'DQ30' if u < p_worse else 'CURRENT'
    if prev_bucket == 'DQ30':
        if u < p_cure:
            return 'CURRENT'
        return 'DQ60' if u < p_cure + p_worse * 1.10 else 'DQ30'
    if prev_bucket == 'DQ60':
        if u < p_cure * 0.60:
            return 'DQ30'
        return 'DQ90' if u < p_cure * 0.60 + p_worse * 1.20 else 'DQ60'
    if prev_bucket == 'DQ90':
        if u < p_cure * 0.30:
            return 'DQ60'
        p_charge = np.clip(0.14 + 0.24 * risk, 0.08, 0.42)
        return 'CHARGEOFF' if u < p_cure * 0.30 + p_charge else 'DQ90'
    return prev_bucket


def generate_synthetic_card_portfolio(accounts: int | None = None, months: int | None = None, seed: int | None = None) -> None:
    cfg = load_yaml('config/project_config.yaml')['project']
    ensure_dirs()
    seed = cfg['random_seed'] if seed is None else seed
    n = int(cfg['default_accounts'] if accounts is None else accounts)
    m = int(cfg['default_months'] if months is None else months)
    rng = np.random.default_rng(seed)
    months_idx = month_range(cfg['start_month'], m)
    create_sample_public_data(seed)

    account_ids = np.arange(1, n+1)
    fico = rng.choice(FICO_BANDS, size=n, p=[.18,.27,.37,.18])
    product = rng.choice(PRODUCTS, size=n, p=[.36,.23,.12,.14,.15])
    income = rng.choice(INCOME, size=n, p=[.22,.32,.31,.15])
    state = rng.choice(STATES, size=n, p=[.18,.18,.11,.06,.04,.13,.12,.09,.05,.04])
    open_offset = rng.integers(-48, 1, size=n)
    open_month = (months_idx[0] + open_offset).astype(str)
    base_limit = {'subprime':3500,'near_prime':7000,'prime':13500,'super_prime':24500}
    income_mult = {'low':0.72,'moderate':1.0,'middle':1.35,'upper':1.85}
    limit = np.array([base_limit[f]*income_mult[i] for f,i in zip(fico,income)]) * rng.lognormal(0, .28, n)
    limit = np.round(np.clip(limit, 500, 60000), -2).astype(int)
    accounts_df = pd.DataFrame({
        'account_id': account_ids, 'open_month': open_month, 'product_type': product,
        'credit_limit': limit, 'fico_band': fico, 'income_band': income, 'state': state,
        'origination_vintage': [month_to_quarter(x) for x in open_month],
    })
    save_csv(accounts_df, 'data/synthetic/accounts.csv')

    rel_depth = rng.choice([0,1,2,3], size=n, p=[.30,.35,.23,.12])
    cross = pd.DataFrame({
        'account_id': account_ids,
        'has_deposit': (rel_depth >= 1).astype(int),
        'has_auto': ((rel_depth >= 2) & (rng.random(n) < .55)).astype(int),
        'has_mortgage': ((rel_depth >= 2) & (rng.random(n) < .35)).astype(int),
        'relationship_tenure_months': np.maximum(0, rng.normal(34 + 18*rel_depth, 15, n)).astype(int),
        'relationship_depth': rel_depth,
    })
    save_csv(cross, 'data/synthetic/cross_lob_relationships.csv')

    macro_rows = []
    for t, mon in enumerate(months_idx):
        unemployment = 3.8 + 0.02*t + 0.35*np.sin(t/5)
        fed_rate = 4.8 - 0.02*t + 0.2*np.cos(t/6)
        rev_growth = 0.028 + 0.012*np.sin(t/4)
        stress = 'normal'
        if unemployment > 4.2: stress = 'watch'
        if unemployment > 4.6: stress = 'stress'
        macro_rows.append({'month': str(mon), 'quarter': month_to_quarter(str(mon)), 'unemployment_rate': round(float(unemployment),3), 'fed_funds_proxy': round(float(fed_rate),3), 'revolving_credit_growth': round(float(rev_growth),4), 'macro_stress_state': stress})
    macro_df = pd.DataFrame(macro_rows)
    save_csv(macro_df, 'data/synthetic/macro_scenario_panel.csv')

    snapshot_rows, bureau_rows = [], []
    prev_bucket = rng.choice(['CURRENT','DQ30','DQ60','DQ90'], size=n, p=[0.965, 0.010, 0.005, 0.020]).astype(object)
    prev_util = np.clip(rng.beta(2, 5, n), .02, .95)
    for t, mon in enumerate(months_idx):
        macro = macro_df.iloc[t]
        macro_stress = max(0, (macro['unemployment_rate'] - 3.8)/2.5)
        drift = rng.normal(0, .04, n) + macro_stress*.025
        util = np.clip(prev_util + drift + np.array([_risk_scale(f) for f in fico])*.01, 0.01, 1.45)
        payment_ratio = np.clip(.34 - .13*util - .025*macro_stress - np.array([_risk_scale(f) for f in fico])*.025 + rng.normal(0,.045,n), 0.0, .60)
        purchase = np.maximum(0, limit * np.clip(.04 + .14*util + rng.normal(0,.04,n), 0, .45))
        balance = np.maximum(0, limit * util + rng.normal(0, 250, n))
        payment = np.minimum(balance, balance*payment_ratio)
        ext_util = np.clip(util + rng.normal(.04, .16, n) + np.array([_risk_scale(f) for f in fico])*.03, 0, 1.7)
        inquiries = rng.poisson(np.clip(.25 + 1.2*ext_util + macro_stress*.5, .1, 5), n)
        ext_dq_prob = np.clip(.01 + .12*ext_util + .02*np.array([_risk_scale(f) for f in fico]) + .02*macro_stress, 0, .7)
        ext_dq = (rng.random(n) < ext_dq_prob).astype(int)
        total_tradelines = np.maximum(1, rng.poisson(5 + 3*(fico != 'subprime') + 2*(income == 'upper'), n))
        bureau_stress = np.clip(.45*ext_util + .25*(inquiries/6) + .30*ext_dq, 0, 1.8)
        risk = np.clip(.22*np.array([_risk_scale(f) for f in fico]) + .32*util + .22*(1-payment_ratio) + .18*bureau_stress + .10*macro_stress, 0, 1.8) / 1.8
        cure_signal = np.clip(.6*payment_ratio + .3*(1-util) + .1*(rel_depth/3), 0, 1)
        new_bucket = np.array([_transition(prev_bucket[i], risk[i], cure_signal[i], rng) for i in range(n)], dtype=object)
        # Add a small ongoing charge-off conversion channel for already delinquent accounts
        # so the synthetic loss proxy remains comparable to public annualized charge-off benchmarks.
        delinquent_now = np.isin(prev_bucket, ['DQ30', 'DQ60', 'DQ90']) | np.isin(new_bucket, ['DQ30', 'DQ60', 'DQ90'])
        late_stage = np.isin(prev_bucket, ['DQ60', 'DQ90']) | np.isin(new_bucket, ['DQ60', 'DQ90'])
        override_prob = np.where(late_stage, np.clip(0.12 + 0.18 * risk, 0.06, 0.35), np.clip(0.010 + 0.045 * risk, 0.004, 0.08))
        override_chargeoff = delinquent_now & (rng.random(n) < override_prob)
        new_bucket = np.where(override_chargeoff, 'CHARGEOFF', new_bucket).astype(object)
        chargeoff = ((prev_bucket != 'CHARGEOFF') & (new_bucket == 'CHARGEOFF')).astype(int)
        is_charged_off = (new_bucket == 'CHARGEOFF').astype(int)
        balance = np.where(is_charged_off == 1, np.maximum(0, balance * .25), balance)
        purchase = np.where(is_charged_off == 1, 0, purchase)
        payment = np.where(is_charged_off == 1, 0, payment)
        ages = [(mon - pd.Period(open_month[i], freq='M')).n for i in range(n)]
        snap = pd.DataFrame({
            'account_id': account_ids, 'month': str(mon), 'account_age_months': ages,
            'balance': np.round(balance, 2), 'purchase_amount': np.round(purchase, 2), 'payment_amount': np.round(payment, 2),
            'credit_limit': limit, 'utilization': np.round(util, 4), 'payment_to_balance_ratio': np.round(payment_ratio, 4),
            'delinquency_bucket': new_bucket, 'chargeoff_flag': chargeoff, 'risk_mechanism_score': np.round(risk, 4)
        })
        bur = pd.DataFrame({
            'account_id': account_ids, 'month': str(mon), 'external_utilization': np.round(ext_util, 4),
            'total_tradelines': total_tradelines, 'inquiries_6m': inquiries, 'external_dq_flag': ext_dq,
            'bureau_stress_score': np.round(bureau_stress, 4)
        })
        snapshot_rows.append(snap); bureau_rows.append(bur)
        prev_bucket = new_bucket; prev_util = util
    snap = pd.concat(snapshot_rows, ignore_index=True)
    bureau = pd.concat(bureau_rows, ignore_index=True)
    snap['dq_severe_flag'] = snap['delinquency_bucket'].isin(['DQ60','DQ90','CHARGEOFF']).astype(int)
    snap['default_next_3m'] = 0
    for _, g in snap.groupby('account_id', sort=False):
        vals = g['dq_severe_flag'].to_numpy()
        future = np.zeros(len(vals), dtype=int)
        for i in range(len(vals)):
            future[i] = int(vals[i+1:min(i+4, len(vals))].max() if i+1 < len(vals) else 0)
        snap.loc[g.index, 'default_next_3m'] = future
    save_csv(snap.drop(columns=['dq_severe_flag']), 'data/synthetic/monthly_card_snapshot.csv')
    save_csv(bureau, 'data/synthetic/bureau_tradeline_proxy.csv')


if __name__ == '__main__':
    generate_synthetic_card_portfolio()
