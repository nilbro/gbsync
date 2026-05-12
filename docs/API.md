# GrowthBook API Reference

This document describes the GrowthBook REST API endpoints used by gbsync for managing metrics, fact tables, and related resources.

## Overview

The GrowthBook API is a REST API for programmatic access to your GrowthBook instance. gbsync uses the API to sync configuration from YAML files to your GrowthBook workspace.

**Base URL:**
```
https://api.growthbook.io/api/v1
```

Or your self-hosted instance:
```
https://growthbook.example.com/api/v1
```

**Authentication:**
All requests require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

## Getting Your API Key

1. Log in to GrowthBook
2. Navigate to Settings → API Keys
3. Create a new API key with appropriate permissions
4. Copy the key and store securely in `GB_API_KEY` environment variable

**Permissions Required:**
- Read access to: Data Sources, Fact Tables, Metrics, Projects, Environments
- Write access to: Fact Tables, Metrics, Projects, Environments
- Delete access to: Fact Tables, Metrics

**Creating a Limited Key:**
For safety, create keys with minimal required permissions:
- Read: All data sources (required to validate datasources)
- Write: Metrics and Fact Tables only
- Delete: Metrics and Fact Tables only

## Endpoints

### Fact Tables

#### List Fact Tables

Get all fact tables in the workspace.

```
GET /api/v1/fact-tables?limit=100&offset=0
```

**Parameters:**
- `limit`: Maximum results (default: 10, max: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "factTables": [
    {
      "id": "ft_123",
      "name": "Events",
      "description": "User events table",
      "datasource": "ds_456",
      "userIdTypes": ["user_id", "anonymous_id"],
      "sql": "SELECT * FROM events",
      "owner": "team@company.com",
      "tags": ["core"],
      "managedBy": "api",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Fact Table

Get a single fact table by ID.

```
GET /api/v1/fact-tables/{id}
```

**Response:**
```json
{
  "factTable": {
    "id": "ft_123",
    "name": "Events",
    ...
  }
}
```

#### Create Fact Table

Create a new fact table.

```
POST /api/v1/fact-tables
Content-Type: application/json

{
  "name": "Events",
  "description": "User events",
  "datasource": "ds_456",
  "userIdTypes": ["user_id"],
  "sql": "SELECT * FROM events WHERE date >= '2024-01-01'",
  "owner": "team@company.com",
  "tags": ["core"]
}
```

**Response:**
```json
{
  "factTable": {
    "id": "ft_new",
    "name": "Events",
    ...
  }
}
```

#### Update Fact Table

Update an existing fact table.

```
POST /api/v1/fact-tables/{id}
Content-Type: application/json

{
  "name": "Events (Updated)",
  "description": "Updated description",
  "sql": "SELECT * FROM events WHERE date >= '2024-01-01'"
}
```

**Note:** Only fields provided in the request body are updated.

#### Delete Fact Table

Delete a fact table.

```
DELETE /api/v1/fact-tables/{id}
```

**Response:**
```json
{
  "success": true
}
```

### Fact Metrics

#### List Fact Metrics

Get all fact metrics in the workspace.

```
GET /api/v1/fact-metrics?limit=100&offset=0
```

**Parameters:**
- `limit`: Maximum results (default: 10, max: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "factMetrics": [
    {
      "id": "fm_123",
      "name": "Conversion Rate",
      "description": "User conversion rate",
      "metricType": "ratio",
      "numerator": {
        "factTableId": "ft_conversions",
        "column": "conversions",
        "filters": []
      },
      "denominator": {
        "factTableId": "ft_events",
        "column": null,
        "filters": []
      },
      "owner": "team@company.com",
      "tags": ["critical"],
      "managedBy": "api",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Fact Metric

Get a single fact metric by ID.

```
GET /api/v1/fact-metrics/{id}
```

**Response:**
```json
{
  "factMetric": {
    "id": "fm_123",
    ...
  }
}
```

#### Create Fact Metric

Create a new fact metric.

```
POST /api/v1/fact-metrics
Content-Type: application/json

{
  "name": "Conversion Rate",
  "description": "User conversion rate",
  "metricType": "ratio",
  "numerator": {
    "factTableId": "ft_conversions",
    "column": "conversions",
    "filters": []
  },
  "denominator": {
    "factTableId": "ft_events",
    "column": null,
    "filters": []
  },
  "owner": "team@company.com",
  "tags": ["critical"]
}
```

**Response:**
```json
{
  "factMetric": {
    "id": "fm_new",
    ...
  }
}
```

#### Update Fact Metric

Update an existing fact metric.

```
POST /api/v1/fact-metrics/{id}
Content-Type: application/json

{
  "name": "Conversion Rate (Updated)",
  "description": "Updated description",
  "tags": ["critical", "important"]
}
```

#### Delete Fact Metric

Delete a fact metric.

```
DELETE /api/v1/fact-metrics/{id}
```

**Response:**
```json
{
  "success": true
}
```

### Projects

#### List Projects

Get all projects in the workspace.

```
GET /api/v1/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "Analytics",
      "description": "Analytics project",
      "settings": null,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Project

Create a new project.

```
POST /api/v1/projects
Content-Type: application/json

{
  "name": "Analytics",
  "description": "Analytics project",
  "settings": null
}
```

#### Update Project

Update a project.

```
POST /api/v1/projects/{id}
Content-Type: application/json

{
  "name": "Analytics (Updated)",
  "description": "Updated description"
}
```

#### Delete Project

Delete a project.

```
DELETE /api/v1/projects/{id}
```

### Environments

#### List Environments

Get all environments in the workspace.

```
GET /api/v1/environments
```

**Response:**
```json
{
  "environments": [
    {
      "id": "env_prod",
      "description": "Production",
      "defaultState": true,
      "toggleOnList": true,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Environment

Create a new environment.

```
POST /api/v1/environments
Content-Type: application/json

{
  "id": "env_staging",
  "description": "Staging",
  "defaultState": false,
  "toggleOnList": true
}
```

#### Update Environment

Update an environment.

```
POST /api/v1/environments/{id}
Content-Type: application/json

{
  "description": "Updated description",
  "defaultState": true
}
```

### Data Sources

#### List Data Sources

Get all data sources in the workspace.

```
GET /api/v1/data-sources
```

**Response:**
```json
{
  "dataSources": [
    {
      "id": "ds_123",
      "name": "Snowflake",
      "type": "snowflake",
      "description": "Main data warehouse",
      "settings": {...}
    }
  ]
}
```

**Common Types:**
- `snowflake`
- `bigquery`
- `postgres`
- `mysql`
- `redshift`
- `athena`
- `clickhouse`
- `mongodb`

## Error Handling

All error responses follow this format:

```json
{
  "status": 400,
  "message": "Invalid request",
  "errors": [
    {
      "field": "sql",
      "message": "Invalid SQL syntax"
    }
  ]
}
```

**Common Error Codes:**

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check API key and Bearer token format |
| 403 | Forbidden | API key lacks required permissions |
| 404 | Not Found | Resource doesn't exist or already deleted |
| 400 | Bad Request | Invalid request data or SQL syntax |
| 409 | Conflict | Duplicate name or ID |
| 422 | Unprocessable | Validation error (missing fields, type mismatch) |
| 429 | Rate Limited | Too many requests (see Rate Limiting) |
| 500 | Server Error | Temporary service issue, retry later |

## Rate Limiting

The GrowthBook API enforces rate limiting:

**Default Limits:**
- 60 requests per minute per API key
- 10,000 requests per hour per organization

**Response Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642291200
```

**Backoff Strategy:**
If you receive a 429 response:
1. Check `X-RateLimit-Reset` header for reset time
2. Wait until reset time before retrying
3. Use exponential backoff (1s, 2s, 4s, 8s, etc.)

gbsync automatically handles rate limiting with backoff.

## Filtering and Searching

### By Name

Filter resources by name (case-insensitive):

```
GET /api/v1/fact-tables?name=events
```

### By Tag

Filter resources by tag:

```
GET /api/v1/fact-metrics?tags=critical
```

### By Owner

Filter resources by owner email:

```
GET /api/v1/fact-tables?owner=team@company.com
```

### Pagination

Use `limit` and `offset` for pagination:

```
GET /api/v1/fact-metrics?limit=20&offset=0
GET /api/v1/fact-metrics?limit=20&offset=20
```

## Resource Relationships

### Hierarchy

```
Workspace
├── Projects
├── Environments
├── Data Sources
├── Fact Tables
│   ├── Filters
│   └── Columns
└── Fact Metrics
    ├── Numerator (references Fact Table)
    └── Denominator (references Fact Table)
```

### Rules

1. **Fact Metrics depend on Fact Tables:** A metric's numerator and denominator must reference existing fact tables
2. **Filters depend on Fact Tables:** A filter belongs to exactly one fact table
3. **Projects are independent:** Can be referenced by resources but not required
4. **Environments are independent:** Can be toggled independently

## API Sync Behavior

### Managed vs Manual

Resources can be marked with `managedBy: "api"`:

```json
{
  "id": "ft_123",
  "name": "Events",
  "managedBy": "api"
}
```

**API-managed resources:**
- Can be deleted by gbsync
- Can be updated by gbsync
- Should not be manually edited in UI

**User-created resources:**
- Ignored by gbsync delete operations
- Not updated by gbsync
- Safe to edit in UI

### Bulk Operations

gbsync batches API calls for efficiency:

1. Fetch all resources (tables, metrics, filters)
2. Compare with desired config
3. Create missing resources
4. Update changed resources
5. Delete resources marked `managedBy: "api"`

Typical workflow:
- 1 list call per resource type
- N create/update/delete calls (one per change)
- Total: 4-20 API calls for typical sync

## Best Practices

1. **Use specific API keys:** Create limited keys with only required permissions
2. **Store keys securely:** Never commit API keys to git
3. **Handle rate limits:** gbsync includes exponential backoff
4. **Test in non-prod:** Use staging environment first
5. **Monitor logs:** Check logs for API errors
6. **Validate SQL:** Test queries before adding to config
7. **Set managedBy:** Mark programmatically-created resources with `managedBy: api`
8. **Track changes:** Use fact table/metric IDs for consistency

## Next Steps

- See [CONFIG.md](./CONFIG.md) for configuration reference
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for API error solutions
- Visit https://docs.growthbook.io/api for full API documentation
