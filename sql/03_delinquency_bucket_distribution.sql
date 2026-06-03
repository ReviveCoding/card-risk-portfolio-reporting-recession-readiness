DROP TABLE IF EXISTS rpt_delinquency_bucket_distribution;
CREATE TABLE rpt_delinquency_bucket_distribution AS
SELECT
  month,
  delinquency_bucket,
  COUNT(*) AS account_months,
  ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY month), 4) AS bucket_share,
  ROUND(SUM(balance), 2) AS balance_exposure
FROM monthly_card_snapshot
GROUP BY month, delinquency_bucket
ORDER BY month, delinquency_bucket;
