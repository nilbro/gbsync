"""Pydantic models for GrowthBook sync state management."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectConfig(BaseModel):
    """User-specified project configuration."""

    name: str
    description: str | None = None
    settings: str | None = None

    model_config = ConfigDict(extra="allow")


class EnvironmentConfig(BaseModel):
    """User-specified environment configuration."""

    description: str | None = None
    defaultState: bool = True
    toggleOnList: bool = True

    model_config = ConfigDict(extra="allow")


class MetricOperand(BaseModel):
    """Operand for a fact metric (numerator or denominator)."""

    factTableId: str
    column: str | None = None  # Required for ratio, optional for proportion
    filters: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class FactTableConfig(BaseModel):
    """User-specified fact table configuration."""

    name: str
    datasource: str
    userIdTypes: list[str]
    tags: list[str] = Field(default_factory=list)
    sql: str
    description: str | None = None
    owner: str | None = None
    projects: list[str] = Field(default_factory=list)
    eventName: str | None = None
    managedBy: str | None = None

    model_config = ConfigDict(extra="allow")


class FactTableFilterConfig(BaseModel):
    """User-specified filter configuration."""

    name: str
    value: str  # SQL WHERE clause
    description: str | None = None
    managedBy: str | None = None

    model_config = ConfigDict(extra="allow")


class FactMetricConfig(BaseModel):
    """User-specified metric configuration."""

    name: str
    metricType: Literal["proportion", "ratio", "mean", "quantile", "dailyParticipation"]
    numerator: MetricOperand
    denominator: MetricOperand | None = None
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    owner: str | None = None
    projects: list[str] = Field(default_factory=list)
    inverse: bool | None = None
    displayAsPercentage: bool | None = None
    managedBy: str | None = None
    cappingSettings: dict[str, Any] | None = None
    windowSettings: dict[str, Any] | None = None
    priorSettings: dict[str, Any] | None = None
    regressionAdjustmentSettings: dict[str, Any] | None = None

    model_config = ConfigDict(extra="allow")

    @field_validator("denominator")
    @classmethod
    def validate_denominator(
        cls, v: MetricOperand | None, info
    ) -> MetricOperand | None:
        """Ensure ratio metrics have a denominator."""
        metric_type = info.data.get("metricType")
        if metric_type == "ratio" and v is None:
            raise ValueError("Ratio metrics require a denominator")
        return v


class ResourceState(BaseModel):
    """Snapshot of a GrowthBook resource (table/filter/metric) as fetched from the API."""

    id: str
    name: str
    parent_id: str | None = None  # For filters
    data: dict[str, Any] = Field(default_factory=dict)  # Full response

    model_config = ConfigDict(frozen=False)


class SyncState(BaseModel):
    """Current state from GrowthBook API."""

    tables: dict[str, ResourceState] = Field(default_factory=dict)
    filters: dict[str, ResourceState] = Field(default_factory=dict)
    metrics: dict[str, ResourceState] = Field(default_factory=dict)
    projects: dict[str, ResourceState] = Field(default_factory=dict)
    environments: dict[str, ResourceState] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=False)


class DesiredState(BaseModel):
    """Desired state from config with typed models."""

    tables: dict[str, FactTableConfig] = Field(default_factory=dict)
    filters: dict[str, FactTableFilterConfig] = Field(default_factory=dict)
    metrics: dict[str, FactMetricConfig] = Field(default_factory=dict)
    projects: dict[str, ProjectConfig] = Field(default_factory=dict)
    environments: dict[str, EnvironmentConfig] = Field(default_factory=dict)

    # Store original config IDs for reference
    table_ids: dict[str, str] = Field(default_factory=dict)
    filter_ids: dict[str, str] = Field(default_factory=dict)
    metric_ids: dict[str, str] = Field(default_factory=dict)
    project_ids: dict[str, str] = Field(default_factory=dict)
    environment_ids: dict[str, str] = Field(default_factory=dict)

    # Store parent relationships
    filter_table_ids: dict[str, str] = Field(
        default_factory=dict
    )  # filter_name -> table_config_id

    @property
    def table_names(self) -> set[str]:
        """Get all table names."""
        return set(self.tables.keys())

    @property
    def filter_names(self) -> set[str]:
        """Get all filter names."""
        return set(self.filters.keys())

    @property
    def metric_names(self) -> set[str]:
        """Get all metric names."""
        return set(self.metrics.keys())

    @property
    def project_names(self) -> set[str]:
        """Get all metric names."""
        return set(self.projects.keys())

    @property
    def environment_names(self) -> set[str]:
        """Get all environment names."""
        return set(self.environments.keys())

    @staticmethod
    def _validate_metric_operand(
        operand: MetricOperand,
        operand_type: str,  # "numerator" or "denominator"
        metric_name: str,
        table_ids: dict[str, str],
        filter_names: set[str],
        filter_table_ids: dict[str, str],
    ) -> None:
        """Validate a metric operand's references."""
        # Validation 1: Check operand's factTableId references an actual table
        if operand.factTableId not in table_ids.values():
            available = sorted(table_ids.values())
            raise ValueError(
                f"Metric '{metric_name}' {operand_type} references unknown table ID "
                f"'{operand.factTableId}'. Available table IDs: {', '.join(available)}"
            )

        # Validation 2: Check all filters exist
        for filter_name in operand.filters:
            if filter_name not in filter_names:
                available = sorted(filter_names)
                raise ValueError(
                    f"Metric '{metric_name}' {operand_type} references unknown filter "
                    f"'{filter_name}'. Available filters: {', '.join(available)}"
                )

            # Validation 3: Check filter belongs to same table as operand
            filter_table_id = filter_table_ids[filter_name]
            if filter_table_id != operand.factTableId:
                raise ValueError(
                    f"Metric '{metric_name}' {operand_type} uses filter '{filter_name}' "
                    f"from table '{filter_table_id}', but operand uses table "
                    f"'{operand.factTableId}'"
                )

    @staticmethod
    def _check_duplicate_id(
        config_id: str,
        id_dict: dict[str, str],
        resource_type: str
    ) -> None:
        """Check if a config ID is already in use."""
        if config_id in id_dict.values():
            existing_resource = next(
                name for name, cid in id_dict.items() if cid == config_id
            )
            raise ValueError(
                f"Duplicate {resource_type} ID '{config_id}' found. "
                f"Already used by {resource_type} '{existing_resource}'."
            )

    @staticmethod
    def _check_duplicate_name(
        name: str,
        name_dict: dict[str, Any],
        resource_type: str
    ) -> None:
        """Check if a resource name is already in use."""
        if name in name_dict:
            raise ValueError(
                f"Duplicate {resource_type} name '{name}' found. "
                f"Each {resource_type} must have a unique name."
            )

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "DesiredState":
        """Parse config dict into typed DesiredState models."""
        projects = {}
        # project_ids = {}
        for project_entry in config.get("projects", []):
            project_config = ProjectConfig(**project_entry)
            name = project_config.name

            # check for duplicate name
            cls._check_duplicate_name(name, projects, "project")

            projects[name] = project_config

        tables = {}
        table_ids = {}
        for table_entry in config.get("factTables", []):
            config_id = table_entry["id"]
            data = table_entry.get("data", {})
            table_config = FactTableConfig(**data)
            name = table_config.name

            # check for duplicate config ID and name
            cls._check_duplicate_id(config_id, table_ids, "table")
            cls._check_duplicate_name(name, tables, "table")

            tables[name] = table_config
            table_ids[name] = config_id

        filters = {}
        filter_ids = {}
        filter_table_ids = {}
        for filter_entry in config.get("factTableFilters", []):
            config_id = filter_entry["id"]
            fact_table_id = filter_entry["factTableId"]
            data = filter_entry.get("data", {})
            filter_config = FactTableFilterConfig(**data)
            name = filter_config.name

            # check for duplicate config ID and name
            cls._check_duplicate_id(config_id, filter_ids, "filter")
            cls._check_duplicate_name(name, filters, "filter")

            # check that factTableId references an actual table
            if fact_table_id not in table_ids.values():
                available = sorted(table_ids.values())
                raise ValueError(
                    f"Filter '{name}' (id: {config_id}) references unknown table ID "
                    f"'{fact_table_id}'. Available table IDs: {', '.join(available)}"
                )

            filters[name] = filter_config
            filter_ids[name] = config_id
            filter_table_ids[name] = fact_table_id  # Track parent table

        metrics = {}
        metric_ids = {}
        for metric_entry in config.get("factMetrics", []):
            config_id = metric_entry["id"]
            data = metric_entry.get("data", {})
            metric_config = FactMetricConfig(**data)
            name = metric_config.name

            # check for duplicate config ID and name
            cls._check_duplicate_id(config_id, metric_ids, "metric")
            cls._check_duplicate_name(name, metrics, "metric")

            # validate numerator operand
            cls._validate_metric_operand(
                operand=metric_config.numerator,
                operand_type="numerator",
                metric_name=name,
                table_ids=table_ids,
                filter_names=set(filters.keys()),
                filter_table_ids=filter_table_ids,
            )

            # validate denominator operand if present
            if metric_config.denominator is not None:
                cls._validate_metric_operand(
                    operand=metric_config.denominator,
                    operand_type="denominator",
                    metric_name=name,
                    table_ids=table_ids,
                    filter_names=set(filters.keys()),
                    filter_table_ids=filter_table_ids,
                )

            metrics[name] = metric_config
            metric_ids[name] = config_id

        environments = {}
        environment_ids = {}
        for env_entry in config.get("environments", []):
            config_id = env_entry["id"]
            data = env_entry.get("data", {})
            env_config = EnvironmentConfig(**data)

            # check for duplicate config ID
            cls._check_duplicate_id(config_id, environment_ids, "environment")

            environments[config_id] = env_config
            environment_ids[config_id] = config_id  # id == config_id for environments

        return cls(
            projects=projects,
            tables=tables,
            filters=filters,
            metrics=metrics,
            environments=environments,
            table_ids=table_ids,
            filter_ids=filter_ids,
            metric_ids=metric_ids,
            environment_ids=environment_ids,
            filter_table_ids=filter_table_ids,
        )

    model_config = ConfigDict(frozen=False)


class ChangePlan(BaseModel):
    """Changes to be applied."""

    projects_to_create: set[str] = Field(default_factory=set)
    projects_to_update: set[str] = Field(default_factory=set)
    projects_to_delete: set[str] = Field(default_factory=set)

    tables_to_create: set[str] = Field(default_factory=set)
    tables_to_update: set[str] = Field(default_factory=set)
    tables_to_delete: set[str] = Field(default_factory=set)

    filters_to_create: set[str] = Field(default_factory=set)
    filters_to_update: set[str] = Field(default_factory=set)
    filters_to_delete: set[str] = Field(default_factory=set)

    metrics_to_create: set[str] = Field(default_factory=set)
    metrics_to_update: set[str] = Field(default_factory=set)
    metrics_to_delete: set[str] = Field(default_factory=set)

    environments_to_create: set[str] = Field(default_factory=set)
    environments_to_update: set[str] = Field(default_factory=set)

    @property
    def has_changes(self) -> bool:
        """Determine if the current and desired states differ."""
        return any(
            getattr(self, field_name)
            for field_name in self.__class__.model_fields
            if field_name.endswith(('_to_create', '_to_update', '_to_delete'))
        )

    model_config = ConfigDict(frozen=False)
