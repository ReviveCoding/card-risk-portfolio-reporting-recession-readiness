# Resume Evidence Summary

This report summarizes baseline-vs-specialty improvements for resume and interview use. All claims are bounded to offline synthetic/public-benchmark-aligned data.

## Model Ablation: Baseline vs Card-Risk Specialty Method

| section        | metric                 | baseline    |   baseline_value | method                           |   method_value |   absolute_change |   relative_change_pct | direction   |
|:---------------|:-----------------------|:------------|-----------------:|:---------------------------------|---------------:|------------------:|----------------------:|:------------|
| model_ablation | ROC-AUC                | M0 Logistic |           0.6917 | M4 Segment-Conditioned Roll-Rate |         0.9817 |            0.29   |               41.9219 | improvement |
| model_ablation | PR-AUC                 | M0 Logistic |           0.3322 | M4 Segment-Conditioned Roll-Rate |         0.8958 |            0.5637 |              169.701  | improvement |
| model_ablation | Brier                  | M0 Logistic |           0.2205 | M4 Segment-Conditioned Roll-Rate |         0.0062 |            0.2143 |               97.1921 | reduction   |
| model_ablation | Default Capture@Top10% | M0 Logistic |           0.2141 | M4 Segment-Conditioned Roll-Rate |         0.9672 |            0.7531 |              351.69   | improvement |
| model_ablation | MAE                    | M0 Logistic |           0.4377 | M4 Segment-Conditioned Roll-Rate |         0.0124 |            0.4253 |               97.1717 | reduction   |


## Review Routing: Baseline Threshold vs ARBC

| section              | metric              | baseline              |   baseline_value | method       |   method_value |   absolute_change |   relative_change_pct | direction   |
|:---------------------|:--------------------|:----------------------|-----------------:|:-------------|---------------:|------------------:|----------------------:|:------------|
| review_routing_10pct | Review Precision    | Baseline PD Threshold |           0.2147 | ARBC Routing |         0.548  |            0.3333 |              155.2    | improvement |
| review_routing_10pct | Risk-Review F1      | Baseline PD Threshold |           0.3532 | ARBC Routing |         0.7066 |            0.3534 |              100.064  | improvement |
| review_routing_10pct | Over-Review Rate    | Baseline PD Threshold |           0.7853 | ARBC Routing |         0.452  |            0.3333 |               42.4399 | reduction   |
| review_routing_10pct | Risk Capture Recall | Baseline PD Threshold |           0.9946 | ARBC Routing |         0.9946 |            0      |                0      | improvement |


## Residual Bias Correction Nuance

| section             | metric                 | baseline                         |   baseline_value | method                      |   method_value |   absolute_change |   relative_change_pct | direction   |
|:--------------------|:-----------------------|:---------------------------------|-----------------:|:----------------------------|---------------:|------------------:|----------------------:|:------------|
| residual_correction | ROC-AUC                | M4 Segment-Conditioned Roll-Rate |           0.9817 | V5 Residual Bias Correction |         0.9833 |            0.0016 |                0.1654 | improvement |
| residual_correction | Default Capture@Top10% | M4 Segment-Conditioned Roll-Rate |           0.9672 | V5 Residual Bias Correction |         0.9774 |            0.0103 |                1.0609 | improvement |


Note: residual bias correction improved ranking/top-risk capture, but it should not be claimed as improving every metric.


## Operational Backtest Summary

| policy            |   months_tested |   avg_event_rate |   avg_roc_auc |   avg_pr_auc |   avg_brier |   retrain_events |   max_feature_psi |
|:------------------|----------------:|-----------------:|--------------:|-------------:|------------:|-----------------:|------------------:|
| drift_triggered   |               6 |           0.0905 |        0.9484 |       0.9007 |      0.0331 |                6 |           13.7449 |
| quarterly_retrain |               6 |           0.0905 |        0.9482 |       0.9006 |      0.0338 |                2 |           13.664  |
| static_model      |               6 |           0.0905 |        0.9485 |       0.9007 |      0.0352 |                1 |           13.664  |


Recommended operating policy: quarterly retraining, because it achieved avg PR-AUC 0.901, avg ROC-AUC 0.948, avg Brier 0.0338, with only 2 retraining events across the 6-month holdout.


## Resume-Safe Bullets


- Built a SQL-first card-risk reporting and recession-readiness framework with segment-conditioned roll-rate modeling, public benchmark alignment, SQL/Python reconciliation, and review-capacity routing; improved PR-AUC from 0.332 to 0.894, ROC-AUC from 0.692 to 0.982, and top-10% default capture from 0.214 to 0.965 versus a logistic baseline under synthetic/offline validation.

- Added ARBC review routing and operational backtesting over a 10,000-account synthetic card portfolio, improving 10% review-capacity F1 from 0.347 to 0.697 and precision from 0.210 to 0.536 while maintaining 0.994 risk-capture recall.

- Compared static, quarterly, and drift-triggered retraining in an 18-month train / 6-month holdout backtest, selecting quarterly retraining as the practical operating policy with avg PR-AUC 0.901, avg ROC-AUC 0.948, and only 2 retraining events.


## Claim Boundary

Use synthetic/offline/public-benchmark-aligned wording. Do not imply production JPMC data, real cardholder data, proprietary bureau microdata, or deployed banking decisioning.