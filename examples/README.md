# gbsync Examples

This directory contains generic reference configurations to help you get started with gbsync.

## Using These Examples

1. Copy `gbsync.yaml` to your project root
2. Copy `fact_tables/` directory to your project
3. Update:
   - Datasource ID (find in GrowthBook UI → Data Sources)
   - SQL queries to match your data warehouse schema
   - User ID types matching your user identifier columns
4. Run `gbsync plan` to preview changes
5. Run `gbsync apply` to sync to GrowthBook

## Key Concepts

- **Fact Tables**: SQL queries that define your event data
- **Filters**: Reusable WHERE clause conditions
- **Metrics**: Aggregations computed from fact tables (ratio, proportion, mean, quantile)
- **Projects**: Organizational groupings in GrowthBook

## Finding Your Datasource ID

1. Open GrowthBook console
2. Go to Data Sources → Your Datasource
3. Copy the ID from the URL (e.g., `ds_19g624mf5exof1`)

## Customizing SQL

These examples use Snowflake syntax. Adapt to your warehouse:
- **BigQuery**: Use `DATE_ADD()`, `DATE_TRUNC()`, `CURRENT_TIMESTAMP()`
- **Postgres**: Use `CURRENT_DATE`, `DATE_TRUNC()`, window functions
- **Redshift**: Similar to Postgres

Ensure date filters limit lookback window for performance (e.g., last 90 days).
