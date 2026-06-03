from __future__ import annotations
import argparse
from .utils import ensure_dirs
from .generate_synthetic_card_portfolio import generate_synthetic_card_portfolio
from .build_database import build_database
from .run_sql_reporting_pack import run_sql_reporting_pack
from .validate_data_quality import validate_data_quality
from .train_baseline_models import train_default_baselines, train_rollrate_baselines
from .build_credit_health_timestep import build_credit_health_timestep
from .run_residual_bias_correction import run_residual_bias_correction
from .run_risk_boundary_routing import run_risk_boundary_routing
from .run_recession_scenarios import run_recession_scenarios
from .run_public_benchmark_alignment import run_public_benchmark_alignment
from .run_risk_driver_monitoring import run_risk_driver_monitoring
from .run_decision_sensitivity import run_decision_sensitivity
from .run_scenario_sensitivity import run_scenario_sensitivity
from .run_reconciliation_governance import run_reconciliation_governance
from .generate_figures import generate_figures
from .generate_reports import generate_reports


def main(accounts: int | None = None, months: int | None = None) -> None:
    ensure_dirs()
    print('[1/14] Generating sample public data and synthetic card portfolio...')
    generate_synthetic_card_portfolio(accounts=accounts, months=months)
    print('[2/14] Building local SQL database...')
    build_database()
    print('[3/14] Running SQL reporting pack...')
    run_sql_reporting_pack()
    print('[4/14] Validating data quality...')
    validate_data_quality()
    print('[5/14] Training vanilla default models...')
    train_default_baselines()
    print('[6/14] Training roll-rate baselines and building analytics mart...')
    train_rollrate_baselines()
    print('[7/14] Building Credit Health Timestep features...')
    build_credit_health_timestep()
    print('[8/14] Running residual bias correction...')
    run_residual_bias_correction()
    print('[9/14] Running asymmetric risk-boundary routing...')
    run_risk_boundary_routing()
    print('[10/14] Running recession scenarios and public benchmark alignment...')
    run_recession_scenarios()
    run_public_benchmark_alignment()
    print('[11/14] Running risk-driver decomposition, drift monitoring, and backtesting...')
    run_risk_driver_monitoring()
    print('[12/14] Running review-capacity and scenario-sensitivity diagnostics...')
    run_decision_sensitivity()
    run_scenario_sensitivity()
    print('[13/14] Running reconciliation, source inventory, and governance checks...')
    run_reconciliation_governance()
    print('[14/14] Generating figures and reports...')
    generate_figures()
    generate_reports()
    print('Pipeline complete. See outputs/, figures/, and reports/.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the local card-risk reporting pipeline.')
    parser.add_argument('--accounts', type=int, default=None, help='Override number of synthetic accounts.')
    parser.add_argument('--months', type=int, default=None, help='Override number of synthetic months.')
    args = parser.parse_args()
    main(accounts=args.accounts, months=args.months)
