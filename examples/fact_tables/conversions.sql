-- Generic conversion/purchase fact table
-- Customize columns and filtering for your business logic

SELECT
  user_id,
  conversion_timestamp,
  CASE WHEN status = 'completed' THEN 1 ELSE 0 END AS converted,
  revenue,
  product_category
FROM purchases
WHERE conversion_date >= DATE('{{ startDate }}')
  AND conversion_date <= DATE('{{ endDate }}')
  AND status IN ('completed', 'pending', 'failed')
