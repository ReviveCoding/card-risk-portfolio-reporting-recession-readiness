# Monitoring and Drift Report

| feature                  | baseline_window    | recent_window      |    psi | status   |
|:-------------------------|:-------------------|:-------------------|-------:|:---------|
| utilization              | 2024-01 to 2024-03 | 2025-11 to 2026-01 | 1.3553 | REVIEW   |
| payment_to_balance_ratio | 2024-01 to 2024-03 | 2025-11 to 2026-01 | 0.4211 | REVIEW   |
| bureau_stress_score      | 2024-01 to 2024-03 | 2025-11 to 2026-01 | 0.7299 | REVIEW   |
| credit_health_shift      | 2024-01 to 2024-03 | 2025-11 to 2026-01 | 1.5255 | REVIEW   |
| residual_corrected_prob  | 2024-01 to 2024-03 | 2025-11 to 2026-01 | 0.0369 | PASS     |
| balance                  | 2024-01 to 2024-03 | 2025-11 to 2026-01 | 0.4568 | REVIEW   |

PSI thresholds: PASS < 0.10, WATCH < 0.25, REVIEW >= 0.25. `credit_health_shift` is monitored instead of raw Credit Health Timestep because raw timestep naturally increases as a portfolio matures. The report is a monitoring-style artifact for local/public-synthetic demonstration, not a bank production monitoring system.
