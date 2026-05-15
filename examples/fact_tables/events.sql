-- Generic event tracking fact table
-- Customize user_id, event_type, and source table for your data

SELECT
  user_id,
  event_timestamp,
  event_type,
  1 AS total_events,
  CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END AS conversions,
  properties
FROM raw_events
WHERE event_date >= DATE('{{ startDate }}')
  AND event_date <= DATE('{{ endDate }}')
  AND event_type IN ('pageview', 'click', 'purchase')
