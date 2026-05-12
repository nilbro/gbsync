# Contributing to gbsync

Thank you for your interest in contributing to gbsync! This guide explains how to set up the development environment, run tests, and submit changes.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Making Changes](#making-changes)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Architecture](#architecture)

## Development Setup

### Requirements

- Python 3.12 or higher
- Git
- pip or uv (recommended)

### Installing Dependencies

1. Clone the repository:
```bash
git clone https://github.com/growthbook/gbsync.git
cd gbsync
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -e ".[dev]"
```

3. Set up environment variables:
```bash
export GB_API_KEY="test_key"
export GB_API_URL="https://api.growthbook.io"
```

### Project Structure

```
gbsync/
├── gbsync/              # Main package
│   ├── cli.py           # Command-line interface
│   ├── client.py        # GrowthBook API client
│   ├── models.py        # Pydantic models
│   └── yaml_loader.py   # YAML parsing
├── tests/               # Test suite
├── examples/            # Example configs
├── docs/                # Documentation
├── pyproject.toml       # Project metadata
├── README.md            # User guide
└── LICENSE              # MIT License
```

### IDE Setup

**VS Code:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

**PyCharm:**
1. Open Settings → Project → Python Interpreter
2. Add interpreter from virtual environment
3. Enable Ruff inspections

## Running Tests

### Unit Tests

Run the full test suite:
```bash
uv run pytest
```

Run specific test file:
```bash
uv run pytest tests/test_models.py
```

Run specific test:
```bash
uv run pytest tests/test_models.py::test_fact_table_config
```

Run with coverage:
```bash
uv run pytest --cov=gbsync --cov-report=html
```

### Test Organization

Tests are organized by module:

```
tests/
├── test_models.py           # Configuration model tests
├── test_client.py           # API client tests
├── test_yaml_loader.py      # YAML parsing tests
└── fixtures/                # Shared test data
    └── configs/             # Example configs
```

### Writing Tests

Test template:
```python
import pytest
from gbsync.models import FactTableConfig

def test_fact_table_config_valid():
    """Test valid fact table configuration."""
    config = FactTableConfig(
        name="Events",
        datasource="ds_123",
        userIdTypes=["user_id"],
        sql="SELECT * FROM events"
    )
    assert config.name == "Events"
    assert config.datasource == "ds_123"

def test_fact_table_config_missing_required_field():
    """Test validation of required fields."""
    with pytest.raises(ValueError):
        FactTableConfig(
            name="Events"
            # Missing: datasource, userIdTypes, sql
        )
```

### Testing with Mock Data

Mock API responses:
```python
import pytest
from unittest.mock import Mock, patch
from gbsync.client import GrowthBookSyncClient

@pytest.fixture
def mock_client():
    """Create mock GrowthBook client."""
    with patch('gbsync.client.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "factTables": [
                {
                    "id": "ft_123",
                    "name": "Events",
                    "datasource": "ds_456",
                    "userIdTypes": ["user_id"],
                    "sql": "SELECT * FROM events"
                }
            ]
        }
        client = GrowthBookSyncClient(
            api_url="https://api.example.com",
            api_key="test_key",
            config_file="gbsync.yaml"
        )
        yield client
```

## Code Quality

### Style Guide

Follow PEP 8 with these conventions:

**Type hints:**
```python
def validate_fact_table(config: dict[str, Any]) -> FactTableConfig:
    """Validate and parse fact table configuration."""
    return FactTableConfig(**config)
```

**Docstrings:**
```python
def create_fact_table(
    table_config: FactTableConfig
) -> ResourceState:
    """Create a fact table in GrowthBook.

    Args:
        table_config: Fact table configuration with name and SQL.

    Returns:
        ResourceState with the created table ID and metadata.

    Raises:
        requests.RequestException: If API request fails.
    """
```

**Variable naming:**
- Use descriptive names: `fact_tables` not `ft`
- Use `_` prefix for private: `_internal_method`
- Use UPPER_CASE for constants: `API_TIMEOUT = 30`

### Linting

Run Ruff linter:
```bash
uv run ruff check gbsync/
```

Fix issues automatically:
```bash
uv run ruff check --fix gbsync/
```

Configure in `pyproject.toml`:
```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

### Type Checking

Run mypy for type checking:
```bash
uv run mypy gbsync/
```

Configure in `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Code Formatting

Format with Black:
```bash
uv run black gbsync/
```

Configure in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ["py312"]
```

### Pre-commit Hooks

Install hooks:
```bash
pre-commit install
```

Run manually:
```bash
pre-commit run --all-files
```

Configure in `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

## Making Changes

### Creating a Feature Branch

```bash
git checkout -b feat/description
# or
git checkout -b fix/issue-number
```

### Commit Discipline

Make focused commits:
```bash
# Good: Focused change
git commit -m "feat: add metric type validation"

# Bad: Too broad
git commit -m "updated multiple things"
```

### Local Testing

Test before committing:
```bash
# Run tests
uv run pytest

# Check style
uv run ruff check gbsync/

# Check types
uv run mypy gbsync/

# Manual testing
uv run gbsync plan --config examples/gbsync.yaml
```

## Commit Messages

Follow conventional commits format:

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code formatting
- `refactor`: Code restructure
- `perf`: Performance improvement
- `test`: Test addition/modification
- `chore`: Tooling/dependency update

**Examples:**

```
feat: add support for quantile metrics

Implement quantile metric type with percentile configuration.
Adds quantileSettings validation and API integration.

Closes #42
```

```
fix: handle SQL template variables correctly

Preserve {{ startDate }} and {{ endDate }} variables during
config rendering instead of replacing with empty strings.

Fixes #123
```

```
docs: update configuration schema documentation

Add examples for CUPED regression adjustment and capping settings.
```

## Pull Request Process

### Before Submitting

1. **Update main branch:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run full test suite:**
   ```bash
   uv run pytest --cov=gbsync
   ```

3. **Check style:**
   ```bash
   uv run ruff check gbsync/
   uv run mypy gbsync/
   ```

4. **Update documentation:**
   - Update `docs/` if behavior changes
   - Update `README.md` for user-facing changes
   - Update `CHANGELOG.md` with summary

5. **Test manually:**
   ```bash
   # Test with example config
   uv run gbsync plan --config examples/gbsync.yaml

   # Test with real API (if credentials available)
   export GB_API_KEY="..."
   export GB_API_URL="..."
   uv run gbsync plan
   ```

### Creating Pull Request

1. Push branch to GitHub:
   ```bash
   git push origin feat/description
   ```

2. Open PR with description:
   - Explain what changed and why
   - Link related issues: "Fixes #42"
   - Include testing notes

3. PR title format:
   ```
   [type] Short description
   Examples:
   - [feat] Add quantile metric support
   - [fix] Handle template variables
   - [docs] Update configuration guide
   ```

### PR Template

```markdown
## Description
Brief description of changes.

## Related Issues
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass locally

## Checklist
- [ ] Code follows PEP 8
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Documentation updated
```

### Review Process

1. Automated checks run (tests, linting, type checking)
2. Code review by maintainers
3. Address review feedback
4. Merge once approved

## Architecture

### Core Components

**Models** (`gbsync/models.py`):
- Configuration models (Pydantic-based)
- State models for API responses
- Change plan tracking

**Client** (`gbsync/client.py`):
- GrowthBook API integration
- Sync state management
- Change detection and application

**CLI** (`gbsync/cli.py`):
- Command-line interface
- User interaction
- Output formatting

**YAML Loader** (`gbsync/yaml_loader.py`):
- Custom YAML parsing
- File inclusion support
- Template variable preservation

### Data Flow

```
Config File (YAML)
    ↓
YAML Loader (parse config)
    ↓
Models (validate and normalize)
    ↓
Client (fetch GrowthBook state)
    ↓
Change Detection (compare states)
    ↓
Display Plan (show changes)
    ↓
User Confirmation
    ↓
API Operations (create/update/delete)
```

### Extension Points

**Adding new resource types:**

1. Add model in `models.py`:
```python
class NewResourceConfig(BaseModel):
    name: str
    description: str | None = None
```

2. Add to `DesiredState`:
```python
class DesiredState(BaseModel):
    new_resources: dict[str, NewResourceConfig]
```

3. Add API methods in `client.py`:
```python
def _get_new_resources(self) -> dict[str, ResourceState]:
    """Fetch new resources from API."""
```

4. Add sync logic in `execute_changes()`.

## Performance Considerations

### API Calls

Minimize API calls:
- Batch creates/updates
- Single list call per resource type
- No unnecessary validation calls

### Memory

For large configs:
- Stream YAML parsing for big files
- Pagination for API responses
- Generator-based change detection

### Timeout Handling

Set reasonable timeouts:
```python
timeout = 30  # seconds
response = requests.get(url, timeout=timeout)
```

## Security Considerations

### Secrets Management

- Never commit API keys
- Use environment variables
- Rotate keys regularly
- Use limited-scope API keys

### SQL Injection

- Validate user-provided SQL
- Use parameterized queries (if needed)
- Document SQL restrictions

### Dependencies

- Pin dependency versions
- Regularly update for security patches
- Review dependency changes

## Troubleshooting Development

### Import errors

```bash
# Reinstall package in dev mode
uv sync
```

### Test failures

```bash
# Run specific test with verbose output
uv run pytest -vv tests/test_models.py::test_name

# Run with print debugging
uv run pytest -s tests/test_models.py::test_name
```

### Type checking errors

```bash
# Check specific file
uv run mypy gbsync/client.py

# Ignore specific errors (temporary)
# type: ignore
```

## Getting Help

- Check [docs/](../) for documentation
- Review [examples/](../examples/) for patterns
- Check GitHub issues for known problems
- Ask in discussions

## Release Process

*For maintainers only*

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Tag release: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. CI/CD builds and publishes to PyPI

## Code of Conduct

Be respectful and constructive. We welcome diverse perspectives and backgrounds.

## License

By contributing, you agree your contributions are licensed under the same MIT license as the project.

## Next Steps

- See [CONFIG.md](./CONFIG.md) for configuration reference
- See [API.md](./API.md) for API details
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
