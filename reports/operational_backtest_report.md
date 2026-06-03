# Operational Backtest Report

Backtest design: train window = 18 months, test window = 6 months. The experiment compares static, quarterly retraining, and drift-triggered retraining policies under time-ordered operational validation.

## Retraining Policy Summary

| policy            |   months_tested |   avg_event_rate |   avg_roc_auc |   avg_pr_auc |   avg_brier |   retrain_events |   max_feature_psi |
|:------------------|----------------:|-----------------:|--------------:|-------------:|------------:|-----------------:|------------------:|
| drift_triggered   |               6 |           0.0905 |        0.9484 |       0.9007 |      0.0331 |                6 |           13.7449 |
| quarterly_retrain |               6 |           0.0905 |        0.9482 |       0.9006 |      0.0338 |                2 |           13.664  |
| static_model      |               6 |           0.0905 |        0.9485 |       0.9007 |      0.0352 |                1 |           13.664  |


## Review Capacity Policy Summary

| policy            | score_policy   |   capacity_rate |   review_queue_size |   review_precision |   risk_capture_recall |   risk_review_f1 |   false_safe_rate |   over_review_rate |
|:------------------|:---------------|----------------:|--------------------:|-------------------:|----------------------:|-----------------:|------------------:|-------------------:|
| static_model      | score          |            0.05 |                3000 |             1      |                0.5525 |           0.7117 |            0.4475 |             0      |
| static_model      | score          |            0.1  |                6000 |             0.8078 |                0.8926 |           0.8481 |            0.1074 |             0.1922 |
| static_model      | score          |            0.15 |                9000 |             0.5432 |                0.9004 |           0.6776 |            0.0996 |             0.4568 |
| static_model      | score          |            0.2  |               12000 |             0.4108 |                0.9077 |           0.5656 |            0.0923 |             0.5893 |
| quarterly_retrain | score          |            0.05 |                3000 |             1      |                0.5525 |           0.7117 |            0.4475 |             0      |
| quarterly_retrain | score          |            0.1  |                6000 |             0.8085 |                0.8934 |           0.8488 |            0.1066 |             0.1915 |
| quarterly_retrain | score          |            0.15 |                9000 |             0.5432 |                0.9004 |           0.6776 |            0.0996 |             0.4568 |
| quarterly_retrain | score          |            0.2  |               12000 |             0.4102 |                0.9064 |           0.5648 |            0.0936 |             0.5898 |
| drift_triggered   | score          |            0.05 |                3000 |             1      |                0.5525 |           0.7117 |            0.4475 |             0      |
| drift_triggered   | score          |            0.1  |                6000 |             0.8082 |                0.893  |           0.8485 |            0.107  |             0.1918 |
| drift_triggered   | score          |            0.15 |                9000 |             0.543  |                0.9    |           0.6773 |            0.1    |             0.457  |
| drift_triggered   | score          |            0.2  |               12000 |             0.4107 |                0.9076 |           0.5655 |            0.0924 |             0.5893 |


## Claim Boundary
This is an offline operational simulation using synthetic account-level data and public benchmark-aligned reporting artifacts. It is not a production bank deployment, not real bureau microdata, and not proprietary cardholder data.
