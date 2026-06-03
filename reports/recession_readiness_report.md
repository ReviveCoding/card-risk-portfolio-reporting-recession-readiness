# Recession Readiness Report

| scenario                     |   avg_predicted_severe_dq_rate |   expected_severe_dq_accounts |   expected_loss_proxy |   avg_utilization |   avg_payment_to_balance_ratio |   avg_bureau_stress_score |   unemployment_shock_pp | core_scenario_monotonicity_pass   |
|:-----------------------------|-------------------------------:|------------------------------:|----------------------:|------------------:|-------------------------------:|--------------------------:|------------------------:|:----------------------------------|
| baseline                     |                         0.0563 |                       563.244 |      788863           |            0.5978 |                         0.2378 |                    0.3798 |                     0   | True                              |
| mild_recession               |                         0.0808 |                       808.425 |           1.81851e+06 |            0.6277 |                         0.2259 |                    0.4178 |                     1   | True                              |
| severe_recession             |                         0.1163 |                      1162.68  |           3.308e+06   |            0.6695 |                         0.214  |                    0.4748 |                     2.5 | True                              |
| high_utilization_stress      |                         0.08   |                       800.105 |           1.82824e+06 |            0.7054 |                         0.2283 |                    0.4178 |                     0.5 | True                              |
| payment_deterioration_stress |                         0.0829 |                       828.531 |           1.89906e+06 |            0.6277 |                         0.195  |                    0.4368 |                     0.8 | True                              |
| combined_tail_stress         |                         0.14   |                      1399.86  |           4.35887e+06 |            0.7293 |                         0.1902 |                    0.5318 |                     3.2 | True                              |

Scenario outputs compare baseline, mild, severe, high-utilization, payment deterioration, and combined tail stress conditions.
