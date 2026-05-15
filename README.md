# gbsync

Sync artifacts to GrowthBook using a version-controlled YAML configuration. gbsync manages your experiment infrastructure as code, enabling reproducible deployments and safe collaboration.

Currently supports:
* Fact Tables
* Fact Table Filters
* Fact Metrics
* Environments

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Infrastructure as Code**: Define growthbook artifacts in YAML so that it can be version controlled
- **Dry-Run Planning**: See what will change before applying
- **Safe Syncing**: Automatic conflict detection and validation
- **API-Managed Resources**: Mark resources to prevent manual UI edits
- **External File Includes**: Organize SQL in separate files

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

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Next Steps

- Copy [examples/gbsync.yaml](examples/gbsync.yaml) to get started
- Read [docs/CONFIG.md](docs/CONFIG.md) for configuration reference
- Check [examples/](examples/) for reference configurations
- Run `gbsync plan` to preview changes
- Run `gbsync apply` to deploy metrics
