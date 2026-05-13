# gbsync

Sync metrics and fact tables to GrowthBook using a version-controlled YAML configuration. gbsync manages your experiment infrastructure as code, enabling reproducible deployments and safe collaboration.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Infrastructure as Code**: Define metrics and fact tables in YAML
- **Dry-Run Planning**: See what will change before applying
- **Safe Syncing**: Automatic conflict detection and validation
- **API-Managed Resources**: Mark resources to prevent manual UI edits
- **Reusable Filters**: Define WHERE clause conditions once, use many times
- **Multiple Metric Types**: Support for ratio, proportion, mean, quantile, and more
- **External File Includes**: Organize SQL in separate files
- **Template Support**: Preserve GrowthBook template variables
- **Comprehensive Validation**: Catch configuration errors early
- **Detailed Error Messages**: Clear guidance on what went wrong

## Installation

### From PyPI

```bash
pip install gbsync
```

### From Source

```bash
git clone https://github.com/growthbook/gbsync.git
cd gbsync
pip install -e .
```

### Requirements

- Python 3.12 or higher
- GrowthBook account with API access

## Quick Start

### 1. Get Your API Credentials

1. Log into GrowthBook
2. Go to **Settings → API Keys**
3. Create a new API key (or copy existing)
4. Note the API URL (e.g., `https://api.growthbook.io`)

### 2. Set Environment Variables

```bash
export GB_API_KEY="your_api_key"
export GB_API_URL="https://api.growthbook.io"
```

### 3. Create Configuration

Copy the example configuration:

```bash
cp examples/gbsync.yaml gbsync.yaml
```

Edit `gbsync.yaml` with your datasource ID, SQL, and metrics:

```yaml
factTables:
  - id: fact_events
    data:
      name: Events
      datasource: ds_YOUR_DATASOURCE_ID
      userIdTypes: [user_id]
      sql: !include fact_tables/events.sql

factMetrics:
  - id: metric_conversion_rate
    data:
      name: Conversion Rate
      metricType: ratio
      numerator:
        factTableId: fact_events
        column: conversions
      denominator:
        factTableId: fact_events
        column: total_events
```

### 4. Plan Changes

See what will be created/updated/deleted:

```bash
gbsync plan
```

Output:
```
GrowthBook: Planning changes...

Tables:
  ✓ Create: Events

Metrics:
  ✓ Create: Conversion Rate

Ready to apply 2 changes
```

### 5. Apply Changes

```bash
gbsync apply
```

Output:
```
GrowthBook: Planning changes...

Tables:
  ✓ Create: Events

Metrics:
  ✓ Create: Conversion Rate

Ready to apply 2 changes
Proceed with apply? [y/N]: y

✓ Applied successfully
```

## Commands

### plan

Preview changes without applying them.

```bash
gbsync plan [OPTIONS]
```

**Options:**
- `--config, -c`: Path to configuration file (default: `gbsync.yaml`)
- `--api-key`: GrowthBook API key (or `GB_API_KEY` env var)
- `--api-url`: GrowthBook API URL (or `GB_API_URL` env var)

**Example:**
```bash
gbsync plan --config ./metrics/prod.yaml
gbsync plan --api-key "sdk-abc123..."
```

### apply

Apply changes to GrowthBook.

```bash
gbsync apply [OPTIONS]
```

**Options:**
- `--config, -c`: Path to configuration file (default: `gbsync.yaml`)
- `--api-key`: GrowthBook API key (or `GB_API_KEY` env var)
- `--api-url`: GrowthBook API URL (or `GB_API_URL` env var)
- `--auto-approve`: Skip confirmation prompt (use with caution)

**Example:**
```bash
gbsync apply
gbsync apply --auto-approve  # Dangerous: skips confirmation
```

## Configuration

### Basic Structure

```yaml
projects:
  - id: proj_analytics
    data:
      name: Analytics
      description: Analytics project

factTables:
  - id: fact_table_id
    data:
      name: Table Name
      datasource: ds_123
      userIdTypes: [user_id]
      sql: SELECT ... FROM ...

factTableFilters:
  - id: filter_id
    factTableId: fact_table_id
    data:
      name: Filter Name
      value: "WHERE clause"

factMetrics:
  - id: metric_id
    data:
      name: Metric Name
      metricType: ratio
      numerator:
        factTableId: fact_table_id
        column: column_name
```

### Key Concepts

**Fact Tables**: SQL queries that define event data

```yaml
factTables:
  - id: fact_events
    data:
      name: Events
      datasource: ds_abc123
      userIdTypes: [user_id, anonymous_id]
      sql: |
        SELECT
          user_id,
          anonymous_id,
          event_date,
          event_type
        FROM events
        WHERE event_date >= '{{ startDate }}'
          AND event_date < '{{ endDate }}'
```

**Filters**: Reusable WHERE clause conditions

```yaml
factTableFilters:
  - id: filter_production
    factTableId: fact_events
    data:
      name: Production Only
      value: "environment = 'production'"
```

**Metrics**: Aggregations computed from fact tables

```yaml
factMetrics:
  - id: metric_conversion_rate
    data:
      name: Conversion Rate
      metricType: ratio
      numerator:
        factTableId: fact_conversions
        column: conversions
        filters: [filter_production]
      denominator:
        factTableId: fact_events
        column: null
        filters: [filter_production]
```

**Metric Types:**
- `proportion`: Numerator / total events
- `ratio`: Numerator / denominator
- `mean`: Average of column values
- `quantile`: Percentile value
- `dailyParticipation`: Daily participation rate

See [docs/CONFIG.md](docs/CONFIG.md) for complete schema reference.

## How It Works

### Sync Process

1. **Read Config**: Parse YAML configuration file
2. **Fetch State**: Get current resources from GrowthBook API
3. **Compare**: Detect differences (creates, updates, deletes)
4. **Display Plan**: Show user what will change
5. **Confirm**: Ask for approval (unless --auto-approve)
6. **Apply**: Create/update/delete resources via API
7. **Verify**: Confirm changes were applied

### Change Detection

gbsync detects:
- **Creates**: Resources in config but not in GrowthBook
- **Updates**: Resources with changed properties
- **Deletes**: Resources in GrowthBook but not in config (only if `managedBy: "api"`)

**API-Managed Resources:**

Mark resources with `managedBy: api` to allow deletion:

```yaml
factTables:
  - id: fact_events
    data:
      managedBy: api
      # ... other fields
```

Resources created by the API get `managedBy: "api"`. Manual resources (created in UI) are never deleted, only updated if config changes.

### Template Variables

Preserve GrowthBook template variables in SQL:

```yaml
sql: |
  SELECT *
  FROM events
  WHERE date >= '{{ startDate }}'
    AND date < '{{ endDate }}'
    AND experiment_id = '{{ experimentId }}'
```

These variables are preserved during config rendering and evaluated at runtime by GrowthBook.

## Example Workflow

### Step 1: Create Configuration

`gbsync.yaml`:
```yaml
factTables:
  - id: fact_page_views
    data:
      name: Page Views
      datasource: ds_19g624mf5exof1
      userIdTypes: [user_id]
      sql: !include fact_tables/page_views.sql

factTableFilters:
  - id: filter_paid
    factTableId: fact_page_views
    data:
      name: Paid Traffic
      value: "traffic_source = 'paid'"

factMetrics:
  - id: metric_paid_conversion_rate
    data:
      name: Paid Conversion Rate
      metricType: ratio
      numerator:
        factTableId: fact_page_views
        column: converted
        filters: [filter_paid]
      denominator:
        factTableId: fact_page_views
        column: null
        filters: [filter_paid]
```

`fact_tables/page_views.sql`:
```sql
SELECT
  user_id,
  converted,
  traffic_source
FROM events
WHERE event_date >= '{{ startDate }}'
  AND event_date < '{{ endDate }}'
```

### Step 2: Preview Changes

```bash
$ gbsync plan

GrowthBook: Planning changes...

Fact Tables:
  ✓ Create: Page Views

Fact Filters:
  ✓ Create: Paid Traffic

Fact Metrics:
  ✓ Create: Paid Conversion Rate

Ready to apply 3 changes
```

### Step 3: Apply Changes

```bash
$ gbsync apply

GrowthBook: Planning changes...

Fact Tables:
  ✓ Create: Page Views

Fact Filters:
  ✓ Create: Paid Traffic

Fact Metrics:
  ✓ Create: Paid Conversion Rate

Ready to apply 3 changes
Proceed with apply? [y/N]: y

✓ Applied successfully
```

### Step 4: Verify in GrowthBook

1. Log into GrowthBook
2. Check Metrics section
3. Verify "Paid Conversion Rate" metric exists
4. Use in experiments

## Advanced Usage

### Multiple Environments

Use separate configs for different environments:

```bash
gbsync plan --config gbsync.prod.yaml
gbsync apply --config gbsync.dev.yaml
```

Each config file can reference different datasources and environments.

### Including External Files

Organize SQL in separate files:

```yaml
factTables:
  - id: fact_events
    data:
      name: Events
      sql: !include fact_tables/events.sql
      
  - id: fact_conversions
    data:
      name: Conversions
      sql: !include fact_tables/conversions.sql
```

### Complex Metrics

Support for advanced metric features:

```yaml
factMetrics:
  - id: metric_capped_revenue
    data:
      name: Capped Revenue
      metricType: mean
      numerator:
        factTableId: fact_transactions
        column: revenue
      cappingSettings:
        type: percentile
        value: 0.99
      regressionAdjustmentSettings:
        enabled: true  # CUPED
      windowSettings:
        type: trailing
        value: 7
```

### Dry-Run for CI/CD

Use in continuous integration to validate configs:

```bash
#!/bin/bash
set -e

export GB_API_KEY="${GROWTHBOOK_API_KEY}"
export GB_API_URL="${GROWTHBOOK_API_URL}"

# Validate config
gbsync plan

# Only apply if not a pull request
if [ "${CI_COMMIT_BRANCH}" = "main" ]; then
  gbsync apply --auto-approve
fi
```

## Documentation

- **[CONFIG.md](docs/CONFIG.md)** - Complete configuration schema reference
- **[API.md](docs/API.md)** - GrowthBook API details
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Development setup and guidelines
- **[examples/](examples/)** - Reference configurations

## Requirements

- Python 3.12+
- GrowthBook account with API access
- Supported data warehouses:
  - Snowflake
  - BigQuery
  - PostgreSQL
  - MySQL
  - Redshift
  - Athena
  - ClickHouse
  - MongoDB

## Limitations

- API rate limits: 60 requests/min, 10,000 requests/hour
- SQL queries validated at GrowthBook (not locally)
- Some features may require GrowthBook Pro/Enterprise
- Manual edits in GrowthBook UI can cause conflicts

## Getting Help

- **Documentation**: See [docs/](docs/) directory
- **Examples**: See [examples/](examples/) for reference configs
- **Issues**: https://github.com/growthbook/gbsync/issues
- **GrowthBook Docs**: https://docs.growthbook.io/
- **GrowthBook Community**: https://join.slack.com/t/growthbook-community/

## Common Tasks

### Adding a New Metric

1. Create fact table (if needed):
```yaml
factTables:
  - id: fact_my_table
    data:
      name: My Table
      datasource: ds_123
      userIdTypes: [user_id]
      sql: SELECT ...
```

2. Add metric:
```yaml
factMetrics:
  - id: metric_my_metric
    data:
      name: My Metric
      metricType: ratio
      numerator:
        factTableId: fact_my_table
        column: col_name
      denominator:
        factTableId: fact_my_table
        column: null
```

3. Plan and apply:
```bash
gbsync plan
gbsync apply
```

### Updating an Existing Metric

1. Modify config:
```yaml
factMetrics:
  - id: metric_my_metric
    data:
      name: My Metric (Updated)
      description: New description
```

2. Plan and apply:
```bash
gbsync plan
gbsync apply
```

### Deleting a Metric

Remove from config and apply:
```bash
# Remove metric entry from gbsync.yaml
gbsync plan
gbsync apply
```

Note: Only deletes resources marked `managedBy: api`.

## Troubleshooting

**Q: I see hundreds of changes on first run**

A: This is normal for existing workspaces. Review carefully before applying.

**Q: My API key isn't working**

A: Verify key format (starts with `sdk-`) and check permissions in GrowthBook Settings.

**Q: SQL validation failed**

A: Test your SQL directly in your data warehouse first, then add to config.

**Q: Too many API requests**

A: Use fewer resources per config, batch changes together.

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Support

For questions or issues:
1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review [examples/](examples/)
3. Search [GitHub Issues](https://github.com/growthbook/gbsync/issues)
4. Create a new issue with details

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Next Steps

- Copy [examples/gbsync.yaml](examples/gbsync.yaml) to get started
- Read [docs/CONFIG.md](docs/CONFIG.md) for configuration reference
- Check [examples/](examples/) for reference configurations
- Run `gbsync plan` to preview changes
- Run `gbsync apply` to deploy metrics
