DROP TABLE IF EXISTS rpt_portfolio_kpi_monthly;
CREATE TABLE rpt_portfolio_kpi_monthly AS
SELECT
  s.month,
  COUNT(*) AS account_months,
  COUNT(DISTINCT s.account_id) AS active_accounts,
  ROUND(SUM(s.balance), 2) AS total_balance,
  ROUND(AVG(s.balance), 2) AS avg_balance,
  ROUND(AVG(s.utilization), 4) AS avg_utilization,
  ROUND(AVG(s.payment_to_balance_ratio), 4) AS avg_payment_to_balance_ratio,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ30','DQ60','DQ90') THEN 1.0 ELSE 0.0 END), 4) AS dq30_plus_rate,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ60','DQ90') THEN 1.0 ELSE 0.0 END), 4) AS dq60_plus_rate,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ90') THEN 1.0 ELSE 0.0 END), 4) AS dq90_plus_rate,
  ROUND(AVG(s.chargeoff_flag), 4) AS chargeoff_proxy_rate,
  ROUND(AVG(s.default_next_3m), 4) AS next_3m_severe_dq_rate
FROM monthly_card_snapshot s
GROUP BY s.month
ORDER BY s.month;
