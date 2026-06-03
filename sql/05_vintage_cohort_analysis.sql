DROP TABLE IF EXISTS rpt_vintage_cohort_report;
CREATE TABLE rpt_vintage_cohort_report AS
SELECT
  a.origination_vintage,
  CASE
    WHEN s.account_age_months < 6 THEN '00-05m'
    WHEN s.account_age_months < 12 THEN '06-11m'
    WHEN s.account_age_months < 24 THEN '12-23m'
    WHEN s.account_age_months < 36 THEN '24-35m'
    ELSE '36m+'
  END AS account_age_band,
  COUNT(*) AS account_months,
  ROUND(AVG(s.utilization), 4) AS avg_utilization,
  ROUND(AVG(s.payment_to_balance_ratio), 4) AS avg_payment_to_balance_ratio,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ30','DQ60','DQ90','CHARGEOFF') THEN 1.0 ELSE 0.0 END), 4) AS dq30_plus_rate,
  ROUND(AVG(s.chargeoff_flag), 4) AS chargeoff_proxy_rate
FROM monthly_card_snapshot s
JOIN accounts a ON s.account_id = a.account_id
GROUP BY a.origination_vintage, account_age_band
ORDER BY a.origination_vintage, account_age_band;
