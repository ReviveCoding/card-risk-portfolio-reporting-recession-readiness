DROP TABLE IF EXISTS rpt_roll_rate_matrix;
CREATE TABLE rpt_roll_rate_matrix AS
WITH lagged AS (
  SELECT
    account_id,
    month,
    delinquency_bucket AS current_bucket,
    LEAD(delinquency_bucket) OVER (PARTITION BY account_id ORDER BY month) AS next_bucket
  FROM monthly_card_snapshot
)
SELECT
  current_bucket,
  COALESCE(next_bucket, 'END_OF_WINDOW') AS next_bucket,
  COUNT(*) AS transitions,
  ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY current_bucket), 4) AS transition_rate
FROM lagged
WHERE next_bucket IS NOT NULL
GROUP BY current_bucket, next_bucket
ORDER BY current_bucket, next_bucket;
