from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def test_public_benchmark_alignment_passes_summary_thresholds():
    df = pd.read_csv(ROOT / 'outputs/public_benchmark_alignment_summary.csv')
    assert set(df['status']).issubset({'PASS','REVIEW'})
    assert (df['status'] == 'PASS').all()

def test_release_decision_is_pass_or_review_not_block():
    text = (ROOT / 'reports/release_decision.md').read_text(encoding='utf-8')
    assert '**BLOCK**' not in text
    assert ('**PASS**' in text) or ('**REVIEW**' in text)

def test_scenario_severe_exceeds_baseline():
    df = pd.read_csv(ROOT / 'outputs/recession_scenario_summary.csv')
    b = df[df['scenario'] == 'baseline'].iloc[0]
    s = df[df['scenario'] == 'severe_recession'].iloc[0]
    assert s['avg_predicted_severe_dq_rate'] >= b['avg_predicted_severe_dq_rate']
    assert s['expected_loss_proxy'] >= b['expected_loss_proxy']
