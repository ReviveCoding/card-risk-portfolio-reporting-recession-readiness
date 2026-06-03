DROP TABLE IF EXISTS rpt_tableau_dashboard_extract;
CREATE TABLE rpt_tableau_dashboard_extract AS
SELECT
  s.month,
  a.state,
  a.fico_band,
  a.product_type,
  a.income_band,
  c.relationship_depth,
  CASE
    WHEN s.utilization < 0.3 THEN 'low_util'
    WHEN s.utilization < 0.7 THEN 'mid_util'
    WHEN s.utilization < 1.0 THEN 'high_util'
    ELSE 'overlimit_proxy'
  END AS utilization_band,
  COUNT(*) AS account_months,
  ROUND(SUM(s.balance), 2) AS total_balance,
  ROUND(AVG(s.utilization), 4) AS avg_utilization,
  ROUND(AVG(s.payment_to_balance_ratio), 4) AS avg_payment_to_balance_ratio,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ30','DQ60','DQ90','CHARGEOFF') THEN 1.0 ELSE 0.0 END), 4) AS dq30_plus_rate,
  ROUND(AVG(s.chargeoff_flag), 4) AS chargeoff_proxy_rate,
  ROUND(AVG(s.default_next_3m), 4) AS next_3m_severe_dq_rate
FROM monthly_card_snapshot s
JOIN accounts a ON s.account_id = a.account_id
JOIN cross_lob_relationships c ON s.account_id = c.account_id
GROUP BY s.month, a.state, a.fico_band, a.product_type, a.income_band, c.relationship_depth, utilization_band
ORDER BY s.month, a.state, a.fico_band;
