# Scenario Sensitivity and Assumption Robustness Report

This report evaluates whether recession-readiness outputs behave consistently over a grid of macro, utilization, payment, and bureau-stress assumptions. It is a robustness check for scenario design, not a regulatory stress test.

## Monotonicity checks

| dimension                        | monotonic_loss_pass   |   points_checked |
|:---------------------------------|:----------------------|-----------------:|
| unemployment_shock_pp            | True                  |                4 |
| utilization_multiplier           | True                  |                3 |
| bureau_stress_multiplier         | True                  |                3 |
| payment_ratio_multiplier_inverse | True                  |                3 |

## Highest expected-loss scenarios

|   unemployment_shock_pp |   utilization_multiplier |   payment_ratio_multiplier |   bureau_stress_multiplier |   avg_predicted_severe_dq_rate |   expected_loss_proxy | tail_watch_flag   |
|------------------------:|-------------------------:|---------------------------:|---------------------------:|-------------------------------:|----------------------:|:------------------|
|                     3.5 |                     1.18 |                        0.8 |                        1.4 |                         0.1426 |           4.45813e+06 | True              |
|                     3.5 |                     1.18 |                        0.8 |                        1.2 |                         0.1401 |           4.34008e+06 | True              |
|                     3.5 |                     1.18 |                        0.9 |                        1.4 |                         0.139  |           4.30736e+06 | True              |
|                     3.5 |                     1.18 |                        0.8 |                        1   |                         0.1376 |           4.22202e+06 | True              |
|                     3.5 |                     1.18 |                        0.9 |                        1.2 |                         0.1365 |           4.1893e+06  | True              |
|                     3.5 |                     1.08 |                        0.8 |                        1.4 |                         0.1364 |           4.15851e+06 | True              |
|                     3.5 |                     1.18 |                        1   |                        1.4 |                         0.1354 |           4.15658e+06 | True              |
|                     3.5 |                     1.18 |                        0.9 |                        1   |                         0.134  |           4.07125e+06 | True              |
|                     3.5 |                     1.08 |                        0.8 |                        1.2 |                         0.1339 |           4.04046e+06 | True              |
|                     3.5 |                     1.18 |                        1   |                        1.2 |                         0.1329 |           4.03852e+06 | True              |
|                     3.5 |                     1.08 |                        0.9 |                        1.4 |                         0.1328 |           4.00773e+06 | True              |
|                     3.5 |                     1.08 |                        0.8 |                        1   |                         0.1314 |           3.9224e+06  | True              |
