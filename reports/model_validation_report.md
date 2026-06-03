# Model Validation Report

| version                                   |   roc_auc |   pr_auc |   brier |    ece |   precision_at_top10pct |   default_capture_at_top10pct |    mae |
|:------------------------------------------|----------:|---------:|--------:|-------:|------------------------:|------------------------------:|-------:|
| M0 Logistic Regression                    |    0.6917 |   0.3322 |  0.2205 | 0.2757 |                  0.3917 |                        0.2141 | 0.4377 |
| M1 Calibrated Logistic Regression         |    0.6917 |   0.3322 |  0.1388 | 0.0215 |                  0.3917 |                        0.2141 | 0.2815 |
| M2 RandomForest                           |    0.6869 |   0.3323 |  0.139  | 0.023  |                  0.3917 |                        0.2141 | 0.2798 |
| M3 Static Roll-Rate Markov Baseline       |    0.9795 |   0.8823 |  0.0062 | 0      |                  0.3811 |                        0.9652 | 0.0124 |
| M4 Segment-Conditioned Roll-Rate Baseline |    0.9817 |   0.8958 |  0.0062 | 0      |                  0.3818 |                        0.9672 | 0.0124 |
| V5 Residual Bias Correction               |    0.9833 |   0.8126 |  0.011  | 0.0056 |                  0.4517 |                        0.9774 | 0.0185 |

Metrics emphasize calibration, PR-AUC, Precision@Top10%, default capture, and MAE rather than ROC-AUC alone.
