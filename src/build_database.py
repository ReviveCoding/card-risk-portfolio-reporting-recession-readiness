from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd
from .utils import ROOT, load_yaml

TABLE_FILES = {
    'accounts': 'data/synthetic/accounts.csv',
    'monthly_card_snapshot': 'data/synthetic/monthly_card_snapshot.csv',
    'bureau_tradeline_proxy': 'data/synthetic/bureau_tradeline_proxy.csv',
    'cross_lob_relationships': 'data/synthetic/cross_lob_relationships.csv',
    'macro_scenario_panel': 'data/synthetic/macro_scenario_panel.csv',
    'public_fred_delinquency': 'data/public_raw/sample_fred_delinquency.csv',
    'public_fred_chargeoff': 'data/public_raw/sample_fred_chargeoff.csv',
    'public_phillyfed_credit_card': 'data/public_raw/sample_phillyfed_credit_card.csv',
}


def build_database(db_path: str | None = None) -> Path:
    cfg = load_yaml('config/project_config.yaml')['project']
    path = ROOT / (db_path or cfg['database_path'])
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    try:
        for table, rel in TABLE_FILES.items():
            df = pd.read_csv(ROOT / rel)
            df.to_sql(table, conn, if_exists='replace', index=False)
        sql = (ROOT / 'sql/01_create_tables.sql').read_text(encoding='utf-8')
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
    return path


if __name__ == '__main__':
    print(build_database())
