# Risk Boundary Review Routing Report

| strategy                            |   review_queue_size |   review_rate |   review_precision |   risk_capture_recall |   risk_review_f1 |   exposure_weighted_recall |   false_safe_rate |   over_review_rate |
|:------------------------------------|--------------------:|--------------:|-------------------:|----------------------:|-----------------:|---------------------------:|------------------:|-------------------:|
| baseline_pd_threshold               |                2552 |        0.2552 |             0.2147 |                0.9946 |           0.3532 |                     0.9716 |            0.0054 |             0.7853 |
| inflated_risk_boundary              |                3485 |        0.3485 |             0.1575 |                0.9964 |           0.2721 |                     0.9906 |            0.0036 |             0.8425 |
| asymmetric_risk_boundary_correction |                1000 |        0.1    |             0.548  |                0.9946 |           0.7066 |                     0.9716 |            0.0054 |             0.452  |

The asymmetric routing layer first inflates the candidate review set using weak but informative risk signals, then deflates/re-ranks the queue using residual-corrected risk scores.
