# Configuration Reference

This document describes the gbsync configuration schema for managing GrowthBook resources.

## Configuration File Format

gbsync uses YAML for configuration. The default file is `gbsync.yaml`.

```bash
gbsync plan --config ./my-config.yaml
```

## Schema Overview

```yaml
projects:
  - id: unique_project_id
    data:
      name: Project Name
      description: Optional description
      settings: Optional settings

environments:
  - id: unique_env_id
    data:
      description: Environment description
      defaultState: true
      toggleOnList: true

factTables:
  - id: unique_table_id
    data:
      name: table_name
      datasource: ds_XXXXXXX
      userIdTypes: [user_id]
      sql: SELECT ... FROM ...
      description: Optional description
      owner: optional_owner_email
      projects: [project_id]
      tags: [tag1, tag2]
      eventName: optional_event_name
      managedBy: api

factTableFilters:
  - id: unique_filter_id
    factTableId: unique_table_id
    data:
      name: filter_name
      value: "WHERE clause condition"
      description: Optional description
      managedBy: api

factMetrics:
  - id: unique_metric_id
    data:
      name: metric_name
      metricType: ratio
      numerator:
        factTableId: unique_table_id
        column: column_name
        filters: [filter_name1, filter_name2]
      denominator:
        factTableId: unique_table_id
        column: column_name
        filters: [filter_name]
      description: Optional description
      owner: optional_owner_email
      projects: [project_id]
      tags: [tag1]
      inverse: false
      displayAsPercentage: false
      cappingSettings: {}
      windowSettings: {}
      priorSettings: {}
      regressionAdjustmentSettings: {}
      managedBy: api
```

## Resource Types

### Projects

Projects organize GrowthBook resources.

```yaml
projects:
  - id: proj_analytics
    data:
      name: Analytics
      description: Analytics metrics and dimensions
      settings: null
```

**Fields:**
- `id`: Unique identifier (required)
- `name`: Display name (required)
- `description`: Optional project description
- `settings`: Optional project-level settings

### Environments

Environments represent deployment stages.

```yaml
environments:
  - id: env_prod
    data:
      description: Production environment
      defaultState: true
      toggleOnList: true
```

**Fields:**
- `id`: Unique identifier (required)
- `description`: Environment description
- `defaultState`: Default toggle state (default: true)
- `toggleOnList`: Show in toggle list (default: true)

### Fact Tables

Fact tables define SQL queries that compute your metric dimensions.

```yaml
factTables:
  - id: fact_events
    data:
      name: Events
      datasource: ds_19g624mf5exof1
      userIdTypes: [user_id, anonymous_id]
      sql: |
        SELECT
          event_id,
          user_id,
          anonymous_id,
          event_date,
          event_type,
          revenue
        FROM events
        WHERE event_date >= '{{ startDate }}'
          AND event_date < '{{ endDate }}'
      description: Raw events table
      owner: data-team@company.com
      projects: [proj_analytics]
      tags: [core, events]
      eventName: page_view
      managedBy: api
```

**Fields:**
- `id`: Unique configuration identifier (required)
- `name`: Display name in GrowthBook (required)
- `datasource`: GrowthBook datasource ID (required)
- `userIdTypes`: List of user identifier columns (required)
- `sql`: SQL query (required). Use `!include fact_tables/events.sql` to include external files
- `description`: Optional documentation
- `owner`: Optional owner email
- `projects`: Optional list of project IDs
- `tags`: Optional list of tags
- `eventName`: Optional event name for identification
- `managedBy`: Set to `api` for API-managed resources (do not edit in UI)

**Template Variables:**
Your SQL can include GrowthBook template variables:
- `{{ startDate }}`: Start date (ISO format)
- `{{ endDate }}`: End date (ISO format)
- `{{ experimentId }}`: Current experiment ID

**Example with template variables:**
```sql
SELECT user_id, COUNT(*) as events
FROM analytics
WHERE event_date >= '{{ startDate }}'
  AND event_date < '{{ endDate }}'
GROUP BY user_id
```

### Fact Table Filters

Filters define reusable WHERE clause conditions for fact tables.

```yaml
factTableFilters:
  - id: filter_prod
    factTableId: fact_events
    data:
      name: Production Events
      value: "environment = 'production'"
      description: Filter to production events only
      managedBy: api
```

**Fields:**
- `id`: Unique configuration identifier (required)
- `factTableId`: Parent fact table ID (required)
- `name`: Display name (required)
- `value`: WHERE clause condition (required, without WHERE keyword)
- `description`: Optional documentation
- `managedBy`: Set to `api` for API-managed resources

**Rules:**
- Filter names must be unique across all tables
- `factTableId` must reference an existing fact table
- Value should be a valid SQL WHERE clause condition (without WHERE keyword)

### Fact Metrics

Metrics aggregate fact table data into experiment metrics.

```yaml
factMetrics:
  - id: metric_conversion_rate
    data:
      name: Conversion Rate
      metricType: ratio
      numerator:
        factTableId: fact_conversions
        column: conversions
        filters: [filter_prod]
      denominator:
        factTableId: fact_events
        column: null
        filters: [filter_prod]
      description: Conversion rate in production
      owner: data-team@company.com
      projects: [proj_analytics]
      tags: [critical]
      inverse: false
      displayAsPercentage: true
      managedBy: api
```

**Fields:**
- `id`: Unique configuration identifier (required)
- `name`: Display name (required)
- `metricType`: One of:
  - `proportion`: Numerator / total events
  - `ratio`: Numerator / denominator
  - `mean`: Average value
  - `quantile`: Percentile (requires quantileSettings)
  - `dailyParticipation`: Participation rate (daily)
- `numerator`: Metric operand (required)
  - `factTableId`: Fact table ID (required)
  - `column`: Column name for aggregation (required for ratio, mean, quantile)
  - `filters`: Optional list of filter names
- `denominator`: Metric operand (required for ratio, optional for others)
  - Same structure as numerator
- `description`: Optional documentation
- `owner`: Optional owner email
- `projects`: Optional list of project IDs
- `tags`: Optional list of tags
- `inverse`: Optional boolean (default: null) - invert metric direction
- `displayAsPercentage`: Optional boolean (default: null) - display as percentage
- `cappingSettings`: Optional capping configuration
- `windowSettings`: Optional windowing configuration
- `priorSettings`: Optional prior settings for Bayesian analysis
- `regressionAdjustmentSettings`: Optional CUPED settings
- `managedBy`: Set to `api` for API-managed resources

**Metric Type Rules:**

*Proportion:*
- Numerator required with column
- Denominator optional (uses all events if omitted)
- Example: conversion rate = conversions / all events

*Ratio:*
- Numerator and denominator both required
- Both must have columns
- Example: CTR = clicks / impressions

*Mean:*
- Numerator required with column
- Denominator optional
- Computes average of column values

*Quantile:*
- Numerator required with column
- Requires quantile settings specifying percentile

*Daily Participation:*
- Tracks whether user participated on given day
- Special aggregation type for participation metrics

**Advanced Settings:**

Capping Settings - Truncate extreme values:
```yaml
cappingSettings:
  type: percentile
  value: 0.99
```

Window Settings - Define event lookback:
```yaml
windowSettings:
  type: trailing
  value: 7
```

Prior Settings - Bayesian prior:
```yaml
priorSettings:
  type: normal
  mean: 0
  stdDev: 1
```

Regression Adjustment (CUPED):
```yaml
regressionAdjustmentSettings:
  enabled: true
```

## Including External Files

Use YAML's `!include` directive to reference external files:

```yaml
factTables:
  - id: fact_events
    data:
      name: Events
      datasource: ds_XXXXXXX
      userIdTypes: [user_id]
      sql: !include fact_tables/events.sql
```

## Validation Rules

### IDs
- Must be globally unique across all resources
- No duplicates allowed
- Each resource must have an id

### Names
- Must be unique within their resource type
- User-friendly display names
- No duplicate metric names, table names, filter names, etc.

### References
- Filters must reference existing fact tables via `factTableId`
- Metrics must reference existing fact tables in operands
- Metric filters must exist and belong to the same table as the operand
- Project references must match existing project IDs

### Fact Table Columns
- Column names must exist in the SQL result
- For ratio/mean metrics, column must be specified
- For proportion without denominator, column optional

## Common Patterns

### Conversion Funnel

```yaml
factTables:
  - id: fact_pageviews
    data:
      name: Page Views
      datasource: ds_XXXXXXX
      userIdTypes: [user_id]
      sql: !include fact_tables/pageviews.sql

  - id: fact_conversions
    data:
      name: Conversions
      datasource: ds_XXXXXXX
      userIdTypes: [user_id]
      sql: !include fact_tables/conversions.sql

factMetrics:
  - id: metric_conversion_rate
    data:
      name: Conversion Rate
      metricType: ratio
      numerator:
        factTableId: fact_conversions
        column: completed
      denominator:
        factTableId: fact_pageviews
        column: null
```

### Filtered Metrics

```yaml
factTableFilters:
  - id: filter_mobile
    factTableId: fact_events
    data:
      name: Mobile Only
      value: "device_type = 'mobile'"

factMetrics:
  - id: metric_mobile_conversion
    data:
      name: Mobile Conversion Rate
      metricType: ratio
      numerator:
        factTableId: fact_conversions
        column: completed
        filters: [filter_mobile]
      denominator:
        factTableId: fact_events
        column: null
        filters: [filter_mobile]
```

### Multi-Dimensional Metrics

```yaml
factMetrics:
  - id: metric_revenue_per_user
    data:
      name: Revenue per User
      metricType: mean
      numerator:
        factTableId: fact_transactions
        column: revenue
        filters: []
      description: Average revenue per user
```

## Common Mistakes

### Duplicate IDs
```yaml
# WRONG: ID used twice
factTables:
  - id: fact_events
    data: ...
  - id: fact_events  # ERROR: Duplicate ID
    data: ...
```

### Referencing Non-existent Tables
```yaml
# WRONG: Filter references non-existent table
factTableFilters:
  - id: filter_1
    factTableId: fact_missing  # ERROR: Table not defined
    data:
      name: Filter
      value: "x = 1"
```

### Ratio Without Denominator
```yaml
# WRONG: Ratio metric needs denominator
factMetrics:
  - id: metric_bad
    data:
      name: Bad Metric
      metricType: ratio
      numerator:
        factTableId: fact_conversions
        column: conversions
      # ERROR: denominator required for ratio
```

### Filter from Wrong Table
```yaml
# WRONG: Using filter from different table
factMetrics:
  - id: metric_bad
    data:
      name: Bad Metric
      metricType: ratio
      numerator:
        factTableId: fact_events
        column: events
        filters: [filter_conversions]  # ERROR: Filter belongs to fact_conversions
```

### Missing Required Fields
```yaml
# WRONG: Missing required fields
factTables:
  - id: fact_events
    data:
      name: Events
      # ERROR: Missing datasource, userIdTypes, sql
```

## Best Practices

1. **Organize by concern**: Group related tables, filters, and metrics
2. **Use descriptive IDs**: `metric_conversion_rate` vs `m1`
3. **Document complex queries**: Add `description` fields
4. **Set owners**: Use `owner` field for accountability
5. **Use tags**: Organize metrics by `tags` (critical, experimental, deprecated)
6. **Version control**: Store `gbsync.yaml` and SQL files in git
7. **Test queries**: Validate SQL in your data warehouse before adding
8. **Use filters for reuse**: Define common conditions as filters
9. **Set managedBy**: Use `managedBy: api` to prevent manual edits
10. **Limit SQL scope**: Use date filters to limit data scans

## Environment-Specific Configs

Create separate configs for different environments:

```bash
gbsync plan --config gbsync.prod.yaml
gbsync plan --config gbsync.dev.yaml
```

Each file can have different datasource IDs, metrics, and settings.

## Next Steps

- See [API.md](./API.md) for REST API details
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guide
- See [examples/](../examples/) for reference configurations
