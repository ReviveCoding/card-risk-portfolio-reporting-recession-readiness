DROP TABLE IF EXISTS rpt_bureau_overlay_report;
CREATE TABLE rpt_bureau_overlay_report AS
SELECT
  CASE
    WHEN b.external_utilization < 0.3 THEN 'low_external_util'
    WHEN b.external_utilization < 0.7 THEN 'mid_external_util'
    WHEN b.external_utilization < 1.0 THEN 'high_external_util'
    ELSE 'external_overlimit_proxy'
  END AS external_utilization_band,
  CASE
    WHEN b.inquiries_6m <= 1 THEN '0-1_inquiries'
    WHEN b.inquiries_6m <= 3 THEN '2-3_inquiries'
    ELSE '4plus_inquiries'
  END AS inquiry_band,
  b.external_dq_flag,
  COUNT(*) AS account_months,
  ROUND(AVG(s.default_next_3m), 4) AS next_3m_severe_dq_rate,
  ROUND(AVG(s.utilization), 4) AS avg_internal_utilization,
  ROUND(AVG(b.bureau_stress_score), 4) AS avg_bureau_stress_score
FROM monthly_card_snapshot s
JOIN bureau_tradeline_proxy b ON s.account_id = b.account_id AND s.month = b.month
GROUP BY external_utilization_band, inquiry_band, b.external_dq_flag
ORDER BY next_3m_severe_dq_rate DESC, avg_bureau_stress_score DESC;
