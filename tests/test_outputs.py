from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_required_output_files_exist():
    required = [
        'outputs/portfolio_kpi_monthly.csv',
        'outputs/roll_rate_matrix.csv',
        'outputs/model_ablation_summary.csv',
        'outputs/review_queue_comparison.csv',
        'outputs/recession_scenario_summary.csv',
        'outputs/tableau_dashboard_extract.csv',
        'reports/executive_risk_summary.md',
        'reports/mock_regulator_response.md',
        'reports/release_decision.md',
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    assert not missing, f'Missing generated files: {missing}'


def test_portfolio_kpi_rates_in_range():
    df = pd.read_csv(ROOT / 'outputs/portfolio_kpi_monthly.csv')
    for col in ['avg_utilization','dq30_plus_rate','dq90_plus_rate','chargeoff_proxy_rate']:
        assert ((df[col] >= 0) & (df[col] <= 2)).all()
    assert df['active_accounts'].min() > 0


def test_validation_no_critical_failures():
    df = pd.read_csv(ROOT / 'outputs/validation_exception_log.csv')
    critical = df[(df['severity'] == 'CRITICAL') & (df['status'] == 'FAIL')]
    assert len(critical) == 0


def test_scenario_monotonicity_passes():
    df = pd.read_csv(ROOT / 'outputs/recession_scenario_summary.csv')
    assert bool(df['core_scenario_monotonicity_pass'].iloc[0])


def test_model_metrics_are_valid():
    df = pd.read_csv(ROOT / 'outputs/model_ablation_summary.csv')
    for col in ['roc_auc','pr_auc','brier','ece']:
        assert col in df.columns
        assert df[col].notna().any()
    assert ((df['brier'].dropna() >= 0) & (df['brier'].dropna() <= 1)).all()


def test_review_queue_has_arbc_strategy():
    df = pd.read_csv(ROOT / 'outputs/review_queue_comparison.csv')
    assert 'asymmetric_risk_boundary_correction' in set(df['strategy'])
    assert ((df['risk_capture_recall'] >= 0) & (df['risk_capture_recall'] <= 1)).all()
