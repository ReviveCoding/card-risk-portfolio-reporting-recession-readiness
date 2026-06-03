from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, mean_absolute_error
from .utils import ROOT, save_csv, ece_score, top_capture, load_yaml


def _metrics(name, y_true, y_prob):
    precision, capture = top_capture(y_true, y_prob, 0.10)
    return {
        'model': name,
        'roc_auc': roc_auc_score(y_true, y_prob),
        'pr_auc': average_precision_score(y_true, y_prob),
        'brier': brier_score_loss(y_true, y_prob),
        'ece': ece_score(y_true, y_prob),
        'precision_at_top10pct': precision,
        'default_capture_at_top10pct': capture,
        'mae': mean_absolute_error(y_true, y_prob),
    }


def _platt_calibrate(train_prob, y_cal, test_prob):
    eps = 1e-6
    train_logit = np.log(np.clip(train_prob, eps, 1-eps) / np.clip(1-train_prob, eps, 1-eps)).reshape(-1, 1)
    test_logit = np.log(np.clip(test_prob, eps, 1-eps) / np.clip(1-test_prob, eps, 1-eps)).reshape(-1, 1)
    cal = LogisticRegression(max_iter=200, solver='liblinear')
    cal.fit(train_logit, y_cal)
    return cal.predict_proba(test_logit)[:, 1]


def train_default_baselines() -> pd.DataFrame:
    cfg = load_yaml('config/model_config.yaml')['models']
    df = pd.read_csv(ROOT / 'data/public_raw/sample_uci_default.csv')
    feature_cols = [c for c in df.columns if c not in ['ID','default_next_month']]
    X = df[feature_cols]
    y = df['default_next_month']
    X_train_full, X_test, y_train_full, y_test = train_test_split(X, y, test_size=cfg['test_size'], random_state=cfg['random_seed'], stratify=y)
    X_train, X_cal, y_train, y_cal = train_test_split(X_train_full, y_train_full, test_size=0.25, random_state=cfg['random_seed'], stratify=y_train_full)
    rows = []
    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=200, solver='liblinear', class_weight='balanced'))
    lr.fit(X_train, y_train)
    lr_prob_test = lr.predict_proba(X_test)[:,1]
    rows.append(_metrics('M0 Logistic Regression', y_test, lr_prob_test))
    lr_prob_cal = lr.predict_proba(X_cal)[:,1]
    cal_prob = _platt_calibrate(lr_prob_cal, y_cal, lr_prob_test)
    rows.append(_metrics('M1 Calibrated Logistic Regression', y_test, cal_prob))
    rf = RandomForestClassifier(n_estimators=60, min_samples_leaf=25, max_depth=8, n_jobs=-1, random_state=cfg['random_seed'])
    rf.fit(X_train_full, y_train_full)
    rows.append(_metrics('M2 RandomForest', y_test, rf.predict_proba(X_test)[:,1]))
    metrics_df = pd.DataFrame(rows)
    save_csv(metrics_df, 'outputs/baseline_model_metrics.csv')
    best_row = metrics_df.sort_values('brier').iloc[0]['model']
    best_prob = {'M0 Logistic Regression': lr_prob_test, 'M1 Calibrated Logistic Regression': cal_prob, 'M2 RandomForest': rf.predict_proba(X_test)[:,1]}[best_row]
    dec = pd.DataFrame({'y': y_test.to_numpy(), 'prob': best_prob})
    dec['risk_decile'] = pd.qcut(dec['prob'].rank(method='first'), 10, labels=False) + 1
    decile = dec.groupby('risk_decile').agg(accounts=('y','size'), observed_default_rate=('y','mean'), avg_predicted_pd=('prob','mean')).reset_index()
    save_csv(decile, 'outputs/risk_decile_calibration.csv')
    return metrics_df


def train_rollrate_baselines() -> pd.DataFrame:
    snap = pd.read_csv(ROOT / 'data/synthetic/monthly_card_snapshot.csv').sort_values(['account_id','month'])
    acct = pd.read_csv(ROOT / 'data/synthetic/accounts.csv')
    data = snap.merge(acct[['account_id','fico_band']], on='account_id', how='left')
    static = data.groupby('delinquency_bucket')['default_next_3m'].mean().to_dict()
    data['static_rollrate_prob'] = data['delinquency_bucket'].map(static).fillna(data['default_next_3m'].mean())
    seg = data.groupby(['fico_band','delinquency_bucket'])['default_next_3m'].mean().reset_index().rename(columns={'default_next_3m':'segment_rollrate_prob'})
    data = data.merge(seg, on=['fico_band','delinquency_bucket'], how='left')
    data['segment_rollrate_prob'] = data['segment_rollrate_prob'].fillna(data['static_rollrate_prob'])
    rows = []
    for name, col in [('M3 Static Roll-Rate Markov Baseline','static_rollrate_prob'), ('M4 Segment-Conditioned Roll-Rate Baseline','segment_rollrate_prob')]:
        rows.append(_metrics(name, data['default_next_3m'], data[col]))
    rr = pd.DataFrame(rows)
    prev = pd.read_csv(ROOT / 'outputs/baseline_model_metrics.csv')
    save_csv(pd.concat([prev, rr], ignore_index=True), 'outputs/baseline_model_metrics.csv')
    data.to_csv(ROOT / 'data/processed/card_risk_analytics_mart.csv', index=False)
    return rr


if __name__ == '__main__':
    print(train_default_baselines())
    print(train_rollrate_baselines())
