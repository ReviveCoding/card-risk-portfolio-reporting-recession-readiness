from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def test_sql_reporting_outputs_have_rows():
    for path in [
        'outputs/portfolio_kpi_monthly.csv',
        'outputs/roll_rate_matrix.csv',
        'outputs/vintage_cohort_report.csv',
        'outputs/segment_risk_report.csv',
        'outputs/bureau_overlay_report.csv',
        'outputs/cross_lob_segment_report.csv',
        'outputs/tableau_dashboard_extract.csv',
    ]:
        df = pd.read_csv(ROOT / path)
        assert len(df) > 0, path

def test_roll_rate_matrix_is_valid_probability_table():
    df = pd.read_csv(ROOT / 'outputs/roll_rate_matrix.csv')
    assert ((df['transition_rate'] >= 0) & (df['transition_rate'] <= 1)).all()
    row_sums = df.groupby('current_bucket')['transition_rate'].sum()
    assert ((row_sums > 0.98) & (row_sums < 1.02)).all()

def test_tableau_extract_contains_dashboard_fields():
    df = pd.read_csv(ROOT / 'outputs/tableau_dashboard_extract.csv')
    expected = {'month','fico_band','utilization_band','account_months','total_balance','dq30_plus_rate','next_3m_severe_dq_rate'}
    assert expected.issubset(df.columns)
