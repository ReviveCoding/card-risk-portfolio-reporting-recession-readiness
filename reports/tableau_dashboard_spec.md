# Tableau Dashboard Specification

## Purpose

Provide a Tableau-ready dashboard design for recurring card-risk portfolio monitoring, recession-readiness review, and executive readout.

## Data source

`outputs/tableau_dashboard_extract.csv`

## Recommended dashboard tabs

1. **Portfolio Overview**: active accounts, total balance, average utilization, DQ30+, DQ90+, monthly charge-off proxy, next-3M severe-DQ proxy.
2. **Delinquency Roll-Rate Monitor**: current bucket to next bucket transition matrix, deterioration and cure trends.
3. **Vintage / Cohort View**: DQ30+ and DQ90+ by account-age band and origination vintage.
4. **Segment Risk View**: FICO band, utilization band, payment-to-balance band, state, and product cuts.
5. **Bureau Proxy Overlay**: external utilization, inquiries, external DQ flag, and bureau-stress score by segment.
6. **Recession Scenario Monitor**: baseline, mild, severe, payment-deterioration, high-utilization, and combined-tail stress outcomes.
7. **Review Queue Monitor**: baseline threshold, inflated queue, and asymmetric risk-boundary corrected queue tradeoffs.
8. **Data Quality & Release Gate**: validation exceptions, public benchmark alignment, scenario monotonicity, and PASS/REVIEW/BLOCK decision.

## Included dashboard mock figures

- `figures/dashboard_portfolio_overview.png`
- `figures/dashboard_roll_rate.png`
- `figures/dashboard_recession_scenario.png`
