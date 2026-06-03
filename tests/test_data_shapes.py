from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def test_synthetic_account_month_shape():
    accounts = pd.read_csv(ROOT / 'data/synthetic/accounts.csv')
    snap = pd.read_csv(ROOT / 'data/synthetic/monthly_card_snapshot.csv')
    assert len(accounts) > 0
    assert len(snap) >= len(accounts)
    assert {'account_id','month','delinquency_bucket','chargeoff_flag','default_next_3m'}.issubset(snap.columns)

def test_public_sample_files_exist_and_have_required_columns():
    fred_dq = pd.read_csv(ROOT / 'data/public_raw/sample_fred_delinquency.csv')
    fred_co = pd.read_csv(ROOT / 'data/public_raw/sample_fred_chargeoff.csv')
    philly = pd.read_csv(ROOT / 'data/public_raw/sample_phillyfed_credit_card.csv')
    assert {'quarter','delinquency_rate_pct'}.issubset(fred_dq.columns)
    assert {'quarter','chargeoff_rate_pct'}.issubset(fred_co.columns)
    assert {'quarter','avg_utilization_rate','payment_rate'}.issubset(philly.columns)
