from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_sql_python_reconciliation_passes():
    path = ROOT / 'outputs/sql_python_reconciliation.csv'
    assert path.exists(), 'SQL/Python reconciliation output is missing'
    df = pd.read_csv(path)
    assert not df.empty
    assert set(df['status']) == {'PASS'}
    assert df['absolute_delta'].max() <= df['tolerance'].max() + 1e-9


def test_source_inventory_boundaries_are_documented():
    path = ROOT / 'outputs/source_inventory.csv'
    assert path.exists(), 'source inventory is missing'
    df = pd.read_csv(path)
    assert len(df) >= 5
    assert df['not_used_for'].str.contains('microdata|real|production|label', case=False, regex=True).any()


def test_review_capacity_sensitivity_has_multiple_capacities_and_strategies():
    path = ROOT / 'outputs/review_capacity_sensitivity.csv'
    assert path.exists(), 'review capacity sensitivity is missing'
    df = pd.read_csv(path)
    assert df['capacity_rate'].nunique() >= 5
    assert {'baseline_pd_threshold', 'asymmetric_risk_boundary_correction', 'stress_weighted_review_queue'}.issubset(set(df['strategy']))
    assert df['risk_review_f1'].between(0, 1).all()


def test_scenario_sensitivity_monotonicity_checks_pass():
    path = ROOT / 'outputs/scenario_sensitivity_checks.csv'
    assert path.exists(), 'scenario sensitivity checks are missing'
    df = pd.read_csv(path)
    assert not df.empty
    assert df['monotonic_loss_pass'].all()


def test_artifact_manifest_and_responsible_use_report_exist():
    manifest = ROOT / 'outputs/artifact_manifest.csv'
    resp = ROOT / 'reports/responsible_use_and_fair_lending_boundary.md'
    assert manifest.exists()
    assert resp.exists()
    md = resp.read_text(encoding='utf-8').lower()
    assert 'not use real customer' in md or 'does not use real customer' in md
    assert 'adverse action' in md


def test_new_sensitivity_figures_exist():
    expected = [
        ROOT / 'figures/review_capacity_sensitivity.png',
        ROOT / 'figures/scenario_sensitivity_grid.png',
    ]
    for path in expected:
        assert path.exists(), f'{path.name} missing'
        assert path.stat().st_size > 1000
