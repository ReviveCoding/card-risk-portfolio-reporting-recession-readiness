DROP TABLE IF EXISTS rpt_segment_risk_report;
CREATE TABLE rpt_segment_risk_report AS
SELECT
  a.fico_band,
  CASE
    WHEN s.utilization < 0.3 THEN 'low_util'
    WHEN s.utilization < 0.7 THEN 'mid_util'
    WHEN s.utilization < 1.0 THEN 'high_util'
    ELSE 'overlimit_proxy'
  END AS utilization_band,
  CASE
    WHEN s.payment_to_balance_ratio < 0.08 THEN 'low_payment'
    WHEN s.payment_to_balance_ratio < 0.22 THEN 'moderate_payment'
    ELSE 'strong_payment'
  END AS payment_band,
  COUNT(*) AS account_months,
  ROUND(AVG(s.default_next_3m), 4) AS next_3m_severe_dq_rate,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ30','DQ60','DQ90','CHARGEOFF') THEN 1.0 ELSE 0.0 END), 4) AS dq30_plus_rate,
  ROUND(AVG(s.chargeoff_flag), 4) AS chargeoff_proxy_rate,
  ROUND(AVG(s.balance), 2) AS avg_balance
FROM monthly_card_snapshot s
JOIN accounts a ON s.account_id = a.account_id
GROUP BY a.fico_band, utilization_band, payment_band
ORDER BY next_3m_severe_dq_rate DESC, account_months DESC;
