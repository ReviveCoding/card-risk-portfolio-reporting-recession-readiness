from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd
from .utils import ROOT, load_yaml, save_csv

SQL_OUTPUTS = {
    '02_monthly_portfolio_summary.sql': ('rpt_portfolio_kpi_monthly', 'outputs/portfolio_kpi_monthly.csv'),
    '03_delinquency_bucket_distribution.sql': ('rpt_delinquency_bucket_distribution', 'outputs/delinquency_bucket_distribution.csv'),
    '04_roll_rate_matrix.sql': ('rpt_roll_rate_matrix', 'outputs/roll_rate_matrix.csv'),
    '05_vintage_cohort_analysis.sql': ('rpt_vintage_cohort_report', 'outputs/vintage_cohort_report.csv'),
    '06_segment_risk_analysis.sql': ('rpt_segment_risk_report', 'outputs/segment_risk_report.csv'),
    '07_bureau_tradeline_overlay.sql': ('rpt_bureau_overlay_report', 'outputs/bureau_overlay_report.csv'),
    '08_cross_lob_relationship_analysis.sql': ('rpt_cross_lob_segment_report', 'outputs/cross_lob_segment_report.csv'),
    '09_public_benchmark_alignment.sql': ('rpt_public_benchmark_alignment', 'outputs/public_benchmark_alignment.csv'),
    '10_tableau_dashboard_extract.sql': ('rpt_tableau_dashboard_extract', 'outputs/tableau_dashboard_extract.csv'),
}


def run_sql_reporting_pack(db_path: str | None = None) -> None:
    cfg = load_yaml('config/project_config.yaml')['project']
    path = ROOT / (db_path or cfg['database_path'])
    conn = sqlite3.connect(path)
    try:
        for sql_file, (table, out_path) in SQL_OUTPUTS.items():
            sql = (ROOT / 'sql' / sql_file).read_text(encoding='utf-8')
            conn.executescript(sql)
            conn.commit()
            df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
            save_csv(df, out_path)
    finally:
        conn.close()


if __name__ == '__main__':
    run_sql_reporting_pack()
