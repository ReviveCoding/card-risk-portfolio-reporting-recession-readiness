from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def test_model_ablation_contains_expected_layers():
    df = pd.read_csv(ROOT / 'outputs/model_ablation_summary.csv')
    versions = set(df['version'])
    assert 'M1 Calibrated Logistic Regression' in versions
    assert 'M4 Segment-Conditioned Roll-Rate Baseline' in versions
    assert 'V5 Residual Bias Correction' in versions

def test_residual_diagnostics_have_probability_and_ranking_metrics():
    df = pd.read_csv(ROOT / 'outputs/residual_correction_diagnostics.csv')
    cols = {'base_mae','corrected_mae','base_pr_auc','corrected_pr_auc','selected_residual_shrinkage_alpha'}
    assert cols.issubset(df.columns)
    assert ((df['selected_residual_shrinkage_alpha'] >= 0) & (df['selected_residual_shrinkage_alpha'] <= 1)).all()

def test_credit_health_timestep_feature_is_generated():
    df = pd.read_csv(ROOT / 'outputs/credit_health_timestep_features.csv')
    assert 'credit_health_timestep' in df.columns
    assert df['credit_health_timestep'].notna().all()
