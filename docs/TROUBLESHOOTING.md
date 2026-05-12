# Troubleshooting Guide

Common issues and solutions when using gbsync.

## Setup Issues

### Error: API key required (set GB_API_KEY or use --api-key)

**Cause:** gbsync couldn't find your GrowthBook API key.

**Solution:**
```bash
# Option 1: Set environment variable
export GB_API_KEY="your_api_key_here"
gbsync plan

# Option 2: Pass as command argument
gbsync plan --api-key "your_api_key_here"

# Option 3: Create .env file (if using python-dotenv)
echo "GB_API_KEY=your_api_key_here" > .env
```

**Where to get your API key:**
1. Log in to GrowthBook
2. Go to Settings → API Keys
3. Create new key (or copy existing)
4. Store in `GB_API_KEY` environment variable

### Error: API URL required (set GB_API_URL or use --api-url)

**Cause:** gbsync couldn't find your GrowthBook API URL.

**Solution:**
```bash
# Option 1: Set environment variable
export GB_API_URL="https://api.growthbook.io"
gbsync plan

# Option 2: Pass as command argument
gbsync plan --api-url "https://api.growthbook.io"
```

**Common URLs:**
- Hosted: `https://api.growthbook.io`
- Self-hosted: `https://growthbook.example.com`

### Error: Configuration file not found

**Cause:** gbsync couldn't find the configuration file.

**Solution:**
```bash
# Option 1: Create default config
# (copy from examples/)
cp examples/gbsync.yaml gbsync.yaml

# Option 2: Specify config path
gbsync plan --config /path/to/config.yaml

# Option 3: Check current directory
pwd
ls -la | grep gbsync.yaml
```

## Authentication Issues

### Error: 401 Unauthorized

**Cause:** API key is invalid or expired.

**Solution:**
1. Verify API key format (should start with `sdk-`)
2. Log into GrowthBook and regenerate key
3. Test with curl:
   ```bash
   curl -H "Authorization: Bearer $GB_API_KEY" \
        https://api.growthbook.io/api/v1/fact-tables
   ```
4. Check key has correct permissions in GrowthBook Settings

### Error: 403 Forbidden

**Cause:** API key lacks required permissions.

**Solution:**
1. Log into GrowthBook
2. Go to Settings → API Keys → Your Key
3. Enable required permissions:
   - Read: Data Sources, Fact Tables, Metrics, Projects, Environments
   - Write: Fact Tables, Metrics
   - Delete: Fact Tables, Metrics
4. Save and test again

### Error: Invalid API key format

**Cause:** API key is malformed or corrupted.

**Solution:**
1. Delete old key in GrowthBook Settings → API Keys
2. Create new key
3. Copy entire key (including `sdk-` prefix)
4. Test immediately (don't modify)

## Configuration Issues

### Error: Datasource not found

**Cause:** Configuration references non-existent datasource.

**Example:**
```yaml
factTables:
  - id: fact_events
    data:
      datasource: ds_NONEXISTENT  # ERROR
```

**Solution:**
1. Log into GrowthBook
2. Go to Data Sources
3. Copy correct datasource ID
4. Update config:
   ```yaml
   datasource: ds_19g624mf5exof1
   ```
5. Run `gbsync plan` to verify

### Error: Unknown table ID in metric

**Cause:** Metric references non-existent fact table.

**Example:**
```yaml
factMetrics:
  - id: metric_conversion
    data:
      numerator:
        factTableId: fact_MISSING  # ERROR
```

**Solution:**
1. Check fact table IDs in config
2. Ensure all table IDs exist
3. Match ID exactly (case-sensitive)
4. Run `gbsync plan` to validate

### Error: Duplicate ID

**Cause:** Configuration has duplicate resource IDs.

**Example:**
```yaml
factTables:
  - id: fact_events
    data: ...
  - id: fact_events  # ERROR: Duplicate
    data: ...
```

**Solution:**
1. Find duplicate ID
2. Make each ID unique
3. Use descriptive IDs: `fact_events_prod`, `fact_events_staging`

### Error: Duplicate name

**Cause:** Two resources have same name.

**Example:**
```yaml
factTables:
  - id: table_1
    data:
      name: Events  # Same name
  - id: table_2
    data:
      name: Events  # ERROR: Duplicate name
```

**Solution:**
1. Give each resource unique name
2. Use qualifiers: `Events (Production)`, `Events (Staging)`

### Error: Filter references unknown table

**Cause:** Filter's `factTableId` is invalid.

**Example:**
```yaml
factTableFilters:
  - id: filter_prod
    factTableId: fact_NONEXISTENT  # ERROR
    data:
      name: Production
      value: "env = 'prod'"
```

**Solution:**
1. Check fact table IDs in config
2. Match `factTableId` to existing table ID
3. Ensure table is defined before filter

### Error: Ratio metric missing denominator

**Cause:** Ratio metric needs both numerator and denominator.

**Example:**
```yaml
factMetrics:
  - id: metric_conversion
    data:
      metricType: ratio
      numerator:
        factTableId: fact_conversions
        column: converted
      # ERROR: denominator required
```

**Solution:**
Add denominator:
```yaml
denominator:
  factTableId: fact_events
  column: null
```

### Error: Unknown filter in metric

**Cause:** Metric references non-existent filter.

**Example:**
```yaml
factMetrics:
  - id: metric_conversion
    data:
      numerator:
        filters: [filter_NONEXISTENT]  # ERROR
```

**Solution:**
1. Check filter names in config
2. Ensure filter is defined
3. Match name exactly (case-sensitive)

### Error: Filter from wrong table

**Cause:** Metric uses filter from different table.

**Example:**
```yaml
factTableFilters:
  - id: filter_prod
    factTableId: fact_conversions  # belongs to conversions table
    data:
      name: Production
      value: "env = 'prod'"

factMetrics:
  - id: metric_rate
    data:
      numerator:
        factTableId: fact_events  # ERROR: using conversion filter on events table
        filters: [filter_prod]
```

**Solution:**
Use only filters that belong to the same table:
```yaml
numerator:
  factTableId: fact_conversions
  filters: [filter_prod]  # OK: filter belongs to fact_conversions
```

### Error: Invalid SQL syntax

**Cause:** SQL query has syntax errors.

**Example:**
```yaml
sql: "SELECT * FORM events WHERE x = 1"  # TYPO: FORM not FROM
```

**Solution:**
1. Validate SQL in data warehouse query editor first
2. Common errors:
   - FORM instead of FROM
   - Missing commas in SELECT
   - Mismatched quotes
   - Invalid date functions
3. Check data warehouse SQL syntax (Snowflake, BigQuery, etc.)

### Error: Column not found

**Cause:** SQL result missing expected column.

**Example:**
```yaml
factTables:
  - id: fact_events
    data:
      sql: "SELECT user_id FROM events"

factMetrics:
  - id: metric_revenue
    data:
      numerator:
        factTableId: fact_events
        column: revenue  # ERROR: not in SELECT
```

**Solution:**
1. Test SQL query in data warehouse
2. Ensure column exists in result
3. Update SQL or metric column reference

## Sync Issues

### Error: Hundreds of changes detected

**Cause:** Large diff between config and GrowthBook state.

**Common causes:**
1. First run of existing workspace
2. Significant config restructuring
3. Comparing different environments
4. Schema changes in fact tables

**Solution:**
1. Review planned changes carefully
2. Use dry-run first: `gbsync plan > changes.txt`
3. If changes look correct: `gbsync apply`
4. If not ready: don't apply yet
5. Start fresh: Delete old resources manually in GrowthBook UI

**For existing workspaces:**
```bash
# Review what will happen
gbsync plan

# Proceed carefully
gbsync apply
```

### Error: 400 Bad Request

**Cause:** Invalid request data sent to API.

**Common causes:**
1. Invalid SQL syntax
2. Invalid column names
3. Missing required fields
4. Type mismatch in data

**Solution:**
1. Run `gbsync plan` to see detailed error
2. Check error message for specific issue
3. Validate SQL separately in data warehouse
4. Verify fact table columns exist
5. Check for special characters in names

**Detailed error:**
```bash
# See verbose error output
gbsync plan --debug
```

### Error: 409 Conflict

**Cause:** Resource already exists with same name.

**Solution:**
1. Check GrowthBook UI for existing resource
2. Either:
   - Delete existing resource and retry
   - Rename in config to avoid conflict
   - Use different ID with same name

### Error: 422 Unprocessable Entity

**Cause:** Request data fails validation.

**Common causes:**
1. Missing required field
2. Invalid data type
3. Invalid enum value
4. Constraint violation

**Solution:**
1. Check config against schema in CONFIG.md
2. Verify required fields:
   - Table: name, datasource, userIdTypes, sql
   - Filter: name, value, factTableId
   - Metric: name, metricType, numerator
3. Check field types match schema

### Error: 500 Server Error

**Cause:** Temporary GrowthBook API issue.

**Solution:**
1. Check GrowthBook status page
2. Wait a minute and retry
3. Use exponential backoff
4. Contact GrowthBook support if persistent

## Connection Issues

### Error: Connection refused

**Cause:** Cannot reach API URL.

**Solution:**
1. Check URL is correct
2. Test with curl:
   ```bash
   curl https://api.growthbook.io/api/v1/fact-tables
   ```
3. Check network connectivity
4. Try different URL (self-hosted vs hosted)
5. Check firewall/proxy settings

### Error: TLS certificate verification failed

**Cause:** SSL/TLS certificate issue.

**Solution:**
1. Check certificate is valid
2. For self-hosted: verify certificate setup
3. Check system time is accurate
4. Try with --insecure (dev only):
   ```bash
   # Not recommended for production
   ```

### Error: Timeout

**Cause:** Request took too long.

**Common causes:**
1. Large fact table causing slow query
2. Slow network connection
3. GrowthBook API overloaded

**Solution:**
1. Try again (might be transient)
2. Simplify SQL queries (add date filters)
3. Reduce batch size
4. Contact GrowthBook support if persistent

## Performance Issues

### Slow `gbsync plan`

**Cause:** Fetching large number of resources.

**Solution:**
1. Reduce number of resources in config
2. Split into multiple config files
3. Check network latency
4. Check GrowthBook API responsiveness

### High API usage

**Cause:** gbsync making too many requests.

**Typical usage:**
- 4 list calls (tables, filters, metrics, projects)
- N create/update/delete calls

**Solution:**
1. Batch changes together
2. Avoid frequent small updates
3. Monitor with `gbsync plan` before apply

## Rate Limiting

### Error: 429 Too Many Requests

**Cause:** Exceeded API rate limit.

**Limits:**
- 60 requests per minute
- 10,000 requests per hour

**Solution:**
1. Wait before retrying (gbsync does this automatically)
2. Batch operations
3. Reduce frequency of syncs
4. Request higher limits from GrowthBook

## Debug Mode

Enable verbose output for troubleshooting:

```bash
# See detailed logs
gbsync plan --debug

# Or set environment variable
export DEBUG=1
gbsync plan
```

Logs include:
- API requests/responses
- Configuration parsing
- Change detection logic
- Validation errors

## Getting Help

### Gather Information

Before reporting issues:

1. Run with debug output:
   ```bash
   gbsync plan --debug > debug.log 2>&1
   ```

2. Check GrowthBook server logs (if self-hosted)

3. Verify setup:
   ```bash
   echo "API Key: $GB_API_KEY"
   echo "API URL: $GB_API_URL"
   cat gbsync.yaml
   ```

4. Test API connection:
   ```bash
   curl -H "Authorization: Bearer $GB_API_KEY" \
        $GB_API_URL/api/v1/fact-tables
   ```

### Common Resolutions

| Issue | First Try | Then Try |
|-------|-----------|----------|
| Can't connect | Verify URL | Check firewall |
| 401/403 error | Verify API key | Regenerate key |
| 400 Bad Request | Validate config | Check SQL syntax |
| Duplicate name | Review config | Rename resource |
| Filter error | Check table ID | Verify filter exists |

### Contact Support

- GrowthBook Docs: https://docs.growthbook.io/
- GrowthBook API: https://docs.growthbook.io/api
- GitHub Issues: https://github.com/growthbook/growthbook/issues
- Community: https://join.slack.com/t/growthbook-community/

## Next Steps

- See [CONFIG.md](./CONFIG.md) for configuration reference
- See [API.md](./API.md) for API details
- See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup
