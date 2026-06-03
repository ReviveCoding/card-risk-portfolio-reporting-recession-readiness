from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
from .utils import ROOT


def generate_figures() -> None:
    kpi = pd.read_csv(ROOT / 'outputs/portfolio_kpi_monthly.csv')
    plt.figure(figsize=(8,5))
    plt.plot(kpi['month'], kpi['dq30_plus_rate'], marker='o', label='DQ30+')
    plt.plot(kpi['month'], kpi['dq90_plus_rate'], marker='o', label='DQ90+')
    plt.xticks(rotation=30, ha='right')
    plt.ylabel('Rate')
    plt.title('Monthly Delinquency Trend')
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/dq_trend.png', dpi=160)
    plt.close()

    roll = pd.read_csv(ROOT / 'outputs/roll_rate_matrix.csv')
    pivot = roll.pivot(index='current_bucket', columns='next_bucket', values='transition_rate').fillna(0)
    plt.figure(figsize=(7,5))
    plt.imshow(pivot.values, aspect='auto')
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha='right')
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.colorbar(label='Transition rate')
    plt.title('Roll-Rate Matrix')
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/roll_rate_heatmap.png', dpi=160)
    plt.close()

    vintage = pd.read_csv(ROOT / 'outputs/vintage_cohort_report.csv')
    v = vintage.groupby('account_age_band')['dq30_plus_rate'].mean().reset_index()
    plt.figure(figsize=(7,5))
    plt.plot(v['account_age_band'], v['dq30_plus_rate'], marker='o')
    plt.ylabel('DQ30+ rate')
    plt.title('Vintage/Cohort Delinquency Curve')
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/vintage_curve.png', dpi=160)
    plt.close()

    dec = pd.read_csv(ROOT / 'outputs/risk_decile_calibration.csv')
    plt.figure(figsize=(7,5))
    plt.plot(dec['risk_decile'], dec['observed_default_rate'], marker='o', label='Observed')
    plt.plot(dec['risk_decile'], dec['avg_predicted_pd'], marker='o', label='Predicted')
    plt.xlabel('Risk decile')
    plt.ylabel('Default rate / PD')
    plt.title('Risk Decile Calibration')
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/risk_decile_default_rate.png', dpi=160)
    plt.savefig(ROOT / 'figures/calibration_curve.png', dpi=160)
    plt.close()

    res = pd.read_csv(ROOT / 'outputs/residual_correction_diagnostics.csv')
    plt.figure(figsize=(6,4))
    plt.bar(['Base MAE','Corrected MAE'], [res.loc[0,'base_mae'], res.loc[0,'corrected_mae']])
    plt.title('Residual Bias Correction Error')
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/residual_correction_error.png', dpi=160)
    plt.close()

    rq = pd.read_csv(ROOT / 'outputs/review_queue_comparison.csv')
    plt.figure(figsize=(8,5))
    plt.plot(rq['strategy'], rq['risk_capture_recall'], marker='o', label='Risk capture')
    plt.plot(rq['strategy'], rq['review_precision'], marker='o', label='Review precision')
    plt.xticks(rotation=25, ha='right')
    plt.ylabel('Rate')
    plt.title('Risk Boundary Routing Tradeoff')
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/risk_boundary_tradeoff.png', dpi=160)
    plt.close()


    # Dashboard-style portfolio overview figure for Tableau / BI discussion.
    latest = kpi.iloc[-1]
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    ax.axis('off')
    lines = [
        'Portfolio Overview Dashboard Mock',
        f"Latest month: {latest['month']}",
        f"Active accounts: {int(latest['active_accounts']):,}",
        f"Total balance: ${latest['total_balance']:,.0f}",
        f"Average utilization: {latest['avg_utilization']:.2%}",
        f"DQ30+ rate: {latest['dq30_plus_rate']:.2%}",
        f"DQ90+ rate: {latest['dq90_plus_rate']:.2%}",
        f"Monthly charge-off proxy: {latest['chargeoff_proxy_rate']:.2%}",
    ]
    ax.text(0.03, 0.95, '\n'.join(lines), va='top', ha='left', fontsize=13)
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/dashboard_portfolio_overview.png', dpi=160)
    plt.close()

    # Roll-rate dashboard mock figure.
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    im = ax.imshow(pivot.values, aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(im, ax=ax, label='Transition rate')
    ax.set_title('Dashboard Mock: Delinquency Roll-Rate Monitor')
    plt.tight_layout()
    plt.savefig(ROOT / 'figures/dashboard_roll_rate.png', dpi=160)
    plt.close()

    # Scenario dashboard mock figure.
    try:
        scen = pd.read_csv(ROOT / 'outputs/recession_scenario_summary.csv')
        plt.figure(figsize=(9, 5))
        plt.plot(scen['scenario'], scen['avg_predicted_severe_dq_rate'], marker='o', label='Predicted severe DQ')
        plt.plot(scen['scenario'], scen['expected_loss_proxy'] / max(scen['expected_loss_proxy'].max(), 1), marker='o', label='Normalized expected loss')
        plt.xticks(rotation=30, ha='right')
        plt.ylabel('Rate / normalized loss')
        plt.title('Dashboard Mock: Recession Scenario Monitor')
        plt.legend()
        plt.tight_layout()
        plt.savefig(ROOT / 'figures/dashboard_recession_scenario.png', dpi=160)
        plt.close()
    except Exception:
        pass


    # Risk driver decomposition and drift monitoring figures.
    try:
        drivers = pd.read_csv(ROOT / 'outputs/risk_driver_decomposition.csv').head(10)
        plt.figure(figsize=(10, 5))
        labels = drivers['driver'] + ':' + drivers['driver_value'].astype(str)
        plt.bar(labels, drivers['expected_loss_contribution_share'])
        plt.xticks(rotation=35, ha='right')
        plt.ylabel('Expected-loss contribution share')
        plt.title('Top Risk Driver Contributions')
        plt.tight_layout()
        plt.savefig(ROOT / 'figures/risk_driver_contribution.png', dpi=160)
        plt.close()
    except Exception:
        pass

    try:
        drift = pd.read_csv(ROOT / 'outputs/drift_monitoring_summary.csv')
        plt.figure(figsize=(9, 5))
        plt.bar(drift['feature'], drift['psi'])
        plt.axhline(0.10, linestyle='--', linewidth=1)
        plt.axhline(0.25, linestyle='--', linewidth=1)
        plt.xticks(rotation=30, ha='right')
        plt.ylabel('PSI')
        plt.title('Feature Drift Monitoring')
        plt.tight_layout()
        plt.savefig(ROOT / 'figures/drift_monitoring_psi.png', dpi=160)
        plt.close()
    except Exception:
        pass


    # Review capacity sensitivity figure.
    try:
        sens = pd.read_csv(ROOT / 'outputs/review_capacity_sensitivity.csv')
        pivot_sens = sens.pivot_table(index='capacity_rate', columns='strategy', values='risk_review_f1', aggfunc='mean')
        plt.figure(figsize=(9, 5))
        for col in pivot_sens.columns:
            plt.plot(pivot_sens.index, pivot_sens[col], marker='o', label=col)
        plt.xlabel('Review capacity rate')
        plt.ylabel('Risk-review F1')
        plt.title('Review Capacity Sensitivity')
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(ROOT / 'figures/review_capacity_sensitivity.png', dpi=160)
        plt.close()
    except Exception:
        pass

    # Scenario sensitivity grid figure.
    try:
        sg = pd.read_csv(ROOT / 'outputs/scenario_sensitivity_grid.csv')
        severe = sg[(sg['utilization_multiplier'] == sg['utilization_multiplier'].max()) & (sg['bureau_stress_multiplier'] == sg['bureau_stress_multiplier'].max())]
        severe = severe.groupby(['unemployment_shock_pp', 'payment_ratio_multiplier'])['expected_loss_proxy'].mean().reset_index()
        plt.figure(figsize=(8, 5))
        for pay_mult, g in severe.groupby('payment_ratio_multiplier'):
            plt.plot(g['unemployment_shock_pp'], g['expected_loss_proxy'], marker='o', label=f'payment x{pay_mult}')
        plt.xlabel('Unemployment shock, pp')
        plt.ylabel('Expected loss proxy')
        plt.title('Scenario Sensitivity Grid')
        plt.legend()
        plt.tight_layout()
        plt.savefig(ROOT / 'figures/scenario_sensitivity_grid.png', dpi=160)
        plt.close()
    except Exception:
        pass


if __name__ == '__main__':
    generate_figures()
