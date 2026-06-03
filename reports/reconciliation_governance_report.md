# SQL/Python Reconciliation and Source Governance Report

## Latest-month SQL/Python reconciliation

| metric               |   python_recomputed_value |   sql_output_value |   absolute_delta |   tolerance | status   |
|:---------------------|--------------------------:|-------------------:|-----------------:|------------:|:---------|
| active_accounts      |           10000           |    10000           |                0 |   0         | PASS     |
| total_balance        |               7.48639e+07 |        7.48639e+07 |                0 |   0.0748639 | PASS     |
| dq30_plus_rate       |               0.041       |        0.041       |                0 |   0         | PASS     |
| dq90_plus_rate       |               0.0001      |        0.0001      |                0 |   0         | PASS     |
| chargeoff_proxy_rate |               0.0017      |        0.0017      |                0 |   0         | PASS     |

## Source inventory and claim boundaries

| source_name                                              | source_type                                    | project_use                                                                    | not_used_for                                    |
|:---------------------------------------------------------|:-----------------------------------------------|:-------------------------------------------------------------------------------|:------------------------------------------------|
| FRED DRCCLACBS                                           | public aggregate sample/fallback               | credit-card delinquency benchmark alignment                                    | account-level label or bank portfolio microdata |
| FRED CORCCACBS                                           | public aggregate sample/fallback               | credit-card charge-off benchmark alignment                                     | account-level charge-off record                 |
| Philadelphia Fed Large Bank Credit Card aggregate sample | public aggregate sample/fallback               | large-bank card utilization/payment/performance context                        | FR Y-14M microdata                              |
| UCI Default of Credit Card Clients sample                | public account-level benchmark sample/fallback | default-risk modeling benchmark                                                | U.S. consumer-bank production portfolio         |
| Synthetic account-level card mart                        | synthetic simulation                           | internal-style SQL reporting, bureau-proxy, cross-LOB, review-routing workflow | real customer/bureau/bank decisioning           |

## Artifact manifest

Generated `112` tracked artifacts across outputs, reports, figures, SQL, source, and tests. See `outputs/artifact_manifest.csv` and `.json`.
