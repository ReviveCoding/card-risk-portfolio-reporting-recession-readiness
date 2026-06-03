DROP TABLE IF EXISTS rpt_cross_lob_segment_report;
CREATE TABLE rpt_cross_lob_segment_report AS
SELECT
  c.relationship_depth,
  c.has_deposit,
  c.has_auto,
  c.has_mortgage,
  COUNT(*) AS account_months,
  ROUND(AVG(s.utilization), 4) AS avg_utilization,
  ROUND(AVG(s.payment_to_balance_ratio), 4) AS avg_payment_to_balance_ratio,
  ROUND(AVG(s.default_next_3m), 4) AS next_3m_severe_dq_rate,
  ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ30','DQ60','DQ90','CHARGEOFF') THEN 1.0 ELSE 0.0 END), 4) AS dq30_plus_rate
FROM monthly_card_snapshot s
JOIN cross_lob_relationships c ON s.account_id = c.account_id
GROUP BY c.relationship_depth, c.has_deposit, c.has_auto, c.has_mortgage
ORDER BY c.relationship_depth, next_3m_severe_dq_rate DESC;
