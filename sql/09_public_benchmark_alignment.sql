DROP TABLE IF EXISTS rpt_public_benchmark_alignment;
CREATE TABLE rpt_public_benchmark_alignment AS
WITH synthetic_q AS (
  SELECT
    m.quarter,
    ROUND(AVG(CASE WHEN s.delinquency_bucket IN ('DQ30','DQ60','DQ90') THEN 1.0 ELSE 0.0 END) * 100, 4) AS synthetic_dq30_plus_pct,
    ROUND(AVG(0.0032 + 0.0015 * s.risk_mechanism_score + CASE WHEN s.delinquency_bucket = 'DQ90' THEN 0.030 WHEN s.delinquency_bucket = 'DQ60' THEN 0.012 ELSE 0 END) * 1200, 4) AS synthetic_chargeoff_proxy_pct,
    ROUND(AVG(s.utilization), 4) AS synthetic_avg_utilization,
    ROUND(AVG(s.payment_to_balance_ratio), 4) AS synthetic_payment_rate
  FROM monthly_card_snapshot s
  JOIN macro_scenario_panel m ON s.month = m.month
  GROUP BY m.quarter
)
SELECT
  q.quarter,
  q.synthetic_dq30_plus_pct,
  fd.delinquency_rate_pct AS fred_delinquency_rate_pct,
  ROUND(ABS(q.synthetic_dq30_plus_pct - fd.delinquency_rate_pct), 4) AS delinquency_alignment_abs_error,
  q.synthetic_chargeoff_proxy_pct,
  fc.chargeoff_rate_pct AS fred_chargeoff_rate_pct,
  ROUND(ABS(q.synthetic_chargeoff_proxy_pct - fc.chargeoff_rate_pct), 4) AS chargeoff_alignment_abs_error,
  q.synthetic_avg_utilization,
  p.avg_utilization_rate AS phillyfed_avg_utilization_rate,
  q.synthetic_payment_rate,
  p.payment_rate AS phillyfed_payment_rate
FROM synthetic_q q
LEFT JOIN public_fred_delinquency fd ON q.quarter = fd.quarter
LEFT JOIN public_fred_chargeoff fc ON q.quarter = fc.quarter
LEFT JOIN public_phillyfed_credit_card p ON q.quarter = p.quarter
ORDER BY q.quarter;
