from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_risk_driver_outputs_exist_and_are_nonempty():
    path = ROOT / 'outputs/risk_driver_decomposition.csv'
    assert path.exists()
    df = pd.read_csv(path)
    assert not df.empty
    assert {'driver', 'driver_value', 'expected_loss_contribution_share'}.issubset(df.columns)
    assert df['expected_loss_contribution_share'].max() > 0


def test_drift_monitoring_summary_has_valid_statuses():
    path = ROOT / 'outputs/drift_monitoring_summary.csv'
    assert path.exists()
    df = pd.read_csv(path)
    assert not df.empty
    assert set(df['status']).issubset({'PASS', 'WATCH', 'REVIEW', 'MISSING'})
    assert df['psi'].notna().any()


def test_backtesting_validation_summary_has_monthly_metrics():
    path = ROOT / 'outputs/backtest_validation_summary.csv'
    assert path.exists()
    df = pd.read_csv(path)
    assert not df.empty
    required = {'month', 'brier', 'ece', 'precision_at_top10pct', 'default_capture_at_top10pct'}
    assert required.issubset(df.columns)
    assert (df['brier'] >= 0).all()


def test_model_card_and_monitoring_plan_exist():
    for rel in ['reports/model_card.md', 'reports/monitoring_plan.md', 'reports/data_dictionary.md']:
        path = ROOT / rel
        assert path.exists()
        text = path.read_text(encoding='utf-8')
        assert 'proprietary bank' in text.lower() or 'monitor' in text.lower() or 'dictionary' in text.lower()


def test_github_ci_and_runbook_exist():
    assert (ROOT / '.github/workflows/ci.yml').exists()
    assert (ROOT / 'docs/LOCAL_RUNBOOK.md').exists()
    assert (ROOT / 'scripts/run_quickstart.sh').exists()
