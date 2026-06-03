from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_dashboard_spec_and_mock_figures_exist():
    assert (ROOT / 'reports/tableau_dashboard_spec.md').exists()
    for path in [
        'figures/dashboard_portfolio_overview.png',
        'figures/dashboard_roll_rate.png',
        'figures/dashboard_recession_scenario.png',
    ]:
        p = ROOT / path
        assert p.exists() and p.stat().st_size > 0

def test_control_matrix_exists():
    p = ROOT / 'reports/control_matrix.md'
    assert p.exists()
    txt = p.read_text(encoding='utf-8')
    assert 'Account-month uniqueness' in txt
    assert 'Release gate decision' in txt
