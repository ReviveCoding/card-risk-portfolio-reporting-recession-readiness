# Reporting Control Matrix

| control_id   | control                         | risk_addressed                                              | evidence                                                | severity   |
|:-------------|:--------------------------------|:------------------------------------------------------------|:--------------------------------------------------------|:-----------|
| C01          | Account-month uniqueness        | Duplicate reporting rows                                    | validation_exception_log.csv                            | CRITICAL   |
| C02          | Balance/payment non-negativity  | Invalid financial fields                                    | validation_exception_log.csv                            | CRITICAL   |
| C03          | Delinquency transition validity | Impossible or excessive bucket migration                    | validation_exception_log.csv; roll_rate_matrix.csv      | CRITICAL   |
| C04          | Bureau-proxy join completeness  | Third-party/proxy data coverage gaps                        | validation_exception_log.csv; bureau_overlay_report.csv | WARNING    |
| C05          | Macro month alignment           | Scenario and reporting period mismatch                      | validation_exception_log.csv                            | CRITICAL   |
| C06          | Public benchmark plausibility   | Synthetic portfolio not aligned to aggregate market context | public_benchmark_alignment_summary.csv                  | WARNING    |
| C07          | Scenario monotonicity           | Stress scenario inconsistencies                             | recession_scenario_summary.csv                          | CRITICAL   |
| C08          | Release gate decision           | Uncontrolled report publication                             | release_decision.md                                     | CRITICAL   |
