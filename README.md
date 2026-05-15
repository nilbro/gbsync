# gbsync

Sync artifacts to GrowthBook using a version-controlled YAML configuration, enabling reproducible deployments and safe collaboration.

Currently supports:
* Fact Tables
* Fact Table Filters
* Fact Metrics
* Environments

> **Note:** gbsync talks directly to the GrowthBook API, so synced resources are flagged as **official** and cannot be edited from the console — change YAML and re-apply.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Infrastructure as Code**: Define growthbook artifacts in YAML so that it can be version controlled
- **Dry-Run Planning**: See what will change before applying
- **Safe Syncing**: Automatic conflict detection and validation
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
- Supported data warehouses: Snowflake, BigQuery, PostgreSQL, MySQL, Redshift, Athena, ClickHouse, MongoDB

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

See [examples/gbsync.yaml](examples/gbsync.yaml) for an annotated reference covering projects, environments, fact tables, filters, metrics, template variables.

