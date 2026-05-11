"""GrowthBook API client for synchronizing growthbook resources."""

import json
import logging

import requests
import typer
import yaml
from rich.console import Console
from rich.table import Table

from gbsync.models import (
    ChangePlan,
    DesiredState,
    ResourceState,
    SyncState,
)
from gbsync.yaml_loader import IncludeLoader

logger = logging.getLogger(__name__)


class GrowthBookSyncClient:
    """Client for synchronizing GrowthBook metrics and fact tables"""

    def __init__(self, api_url: str, api_key: str, config_file: str) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        self.config_file = config_file
        self.config: dict | None = None
        self.state: SyncState | None = None
        self.desired_state: DesiredState | None = None
        self.changes: ChangePlan | None = None

    def _get_fact_metrics(self) -> dict[str, ResourceState]:
        """Get existing fact metrics with full data."""
        metrics_resp = requests.get(
            f"{self.api_url}/api/v1/fact-metrics?limit=100", headers=self.headers
        )
        metrics_resp.raise_for_status()
        metrics_list = metrics_resp.json().get("factMetrics", [])

        resources = {}
        for metric in metrics_list:
            name = metric.get("name", metric["id"])
            resources[name] = ResourceState(id=metric["id"], name=name, data=metric)

        return resources

    def _get_fact_tables(self) -> dict[str, ResourceState]:
        """Get existing fact tables with full data."""
        tables_resp = requests.get(
            f"{self.api_url}/api/v1/fact-tables?limit=100", headers=self.headers
        )
        tables_resp.raise_for_status()
        tables_list = tables_resp.json().get("factTables", [])

        resources = {}
        for table in tables_list:
            name = table.get("name", table["id"])
            resources[name] = ResourceState(id=table["id"], name=name, data=table)

        return resources

    def _get_projects(self) -> dict[str, ResourceState]:
        """Get existing projects with full data."""
        projects_resp = requests.get(
            f"{self.api_url}/api/v1/projects", headers=self.headers
        )
        projects_resp.raise_for_status()
        projects_list = projects_resp.json().get("projects", [])

        resources = {}
        for project in projects_list:
            name = project.get("name", project["id"])
            resources[name] = ResourceState(id=project["id"], name=name, data=project)

        return resources

    def _get_environments(self) -> dict[str, ResourceState]:
        """Get existing environments with full data."""
        envs_resp = requests.get(
            f"{self.api_url}/api/v1/environments", headers=self.headers
        )
        envs_resp.raise_for_status()
        envs_list = envs_resp.json().get("environments", [])

        resources = {}
        for env in envs_list:
            env_id = env["id"]
            resources[env_id] = ResourceState(id=env_id, name=env_id, data=env)

        return resources

    @staticmethod
    def _api_managed_names(resources: dict[str, ResourceState]) -> set[str]:
        """Return names of resources that are API-managed (managedBy == 'api')."""
        return {name for name, rs in resources.items() if rs.data.get("managedBy") == "api"}

    def _get_fact_table_filters(self) -> dict[str, ResourceState]:
        """Get existing fact table filters from all fact tables."""
        if not self.state or not self.state.tables:
            logger.debug("Skipping filter fetch: no state or tables available")
            return {}

        resources = {}

        # Iterate over each fact table and get its filters
        for table_name, table_state in self.state.tables.items():
            table_id = table_state.id

            try:
                filters_resp = requests.get(
                    f"{self.api_url}/api/v1/fact-tables/{table_id}/filters?limit=100",
                    headers=self.headers,
                )
                filters_resp.raise_for_status()
                filters_list = filters_resp.json().get("factTableFilters", [])

                for filter_obj in filters_list:
                    name = filter_obj.get("name", filter_obj["id"])
                    resources[name] = ResourceState(
                        id=filter_obj["id"],
                        name=name,
                        parent_id=table_id,  # Track parent table
                        data=filter_obj,
                    )
            except requests.RequestException as e:
                typer.echo(
                    f"  Warning: Failed to get filters for table {table_name}: {e}"
                )
                continue

        return resources

    def _delete_tables(self, table_names_to_delete: set[str]) -> None:
        """Delete fact tables. Deletion happens via ids."""
        if not self.state:
            logger.debug("Skipping table deletion: no state available")
            return

        for name in sorted(table_names_to_delete):
            if name not in self.state.tables:
                typer.echo(f"  Warning: Table '{name}' not found in state")
                continue
            tid = self.state.tables[name].id
            requests.delete(
                f"{self.api_url}/api/v1/fact-tables/{tid}",
                headers=self.headers,
            )
            typer.echo(f"  Deleted table: {name}")

    def _delete_projects(self, project_names_to_delete: set[str]) -> None:
        """Delete Projects. Deletion happens via ids."""
        if not self.state:
            logger.debug("Skipping project deletion: no state available")
            return

        for name in sorted(project_names_to_delete):
            if name not in self.state.projects:
                typer.echo(f"  Warning: Project '{name}' not found in state")
                continue
            tid = self.state.projects[name].id
            requests.delete(
                f"{self.api_url}/api/v1/projects/{tid}",
                headers=self.headers,
            )
            typer.echo(f"  Deleted project: {name}")

    def _delete_metrics(self, metric_names_to_delete: set[str]) -> None:
        """Delete fact metrics. Deletion happens via ids."""
        if not self.state:
            logger.debug("Skipping metric deletion: no state available")
            return

        for name in sorted(metric_names_to_delete):
            if name not in self.state.metrics:
                typer.echo(f"  Warning: Metric '{name}' not found in state")
                continue
            mid = self.state.metrics[name].id
            requests.delete(
                f"{self.api_url}/api/v1/fact-metrics/{mid}",
                headers=self.headers,
            )
            typer.echo(f"  Deleted metric: {name}")

    def _delete_filters(self, filter_names_to_delete: set[str]) -> None:
        """Delete fact table filters using nested endpoint."""
        if not self.state:
            logger.debug("Skipping filter deletion: no state available")
            return

        for name in sorted(filter_names_to_delete):
            if name not in self.state.filters:
                typer.echo(f"  Warning: Filter '{name}' not found in state")
                continue

            filter_state = self.state.filters[name]
            filter_id = filter_state.id
            fact_table_id = filter_state.parent_id

            if not fact_table_id:
                typer.echo(
                    f"  Warning: Filter '{name}' has no parent table ID, skipping"
                )
                continue

            try:
                requests.delete(
                    f"{self.api_url}/api/v1/fact-tables/{fact_table_id}/filters/{filter_id}",
                    headers=self.headers,
                )
                typer.echo(f"  Deleted filter: {name}")
            except requests.RequestException as e:
                typer.echo(f"  Error deleting filter '{name}': {e}")

    def _load_config(self) -> dict:
        """Load local config."""
        try:
            with open(self.config_file, encoding="utf-8") as f:
                return yaml.load(f, Loader=IncludeLoader)
        except FileNotFoundError:
            typer.echo(f"Error: Config file not found: {self.config_file}")
            raise typer.Exit(1)
        except yaml.YAMLError as e:
            typer.echo(f"Error: Invalid YAML: {e}")
            raise typer.Exit(1)

    def load_config_and_fetch_state(self) -> None:
        """Load local config and fetch remote state from GrowthBook."""
        # Lazy load config on first use
        if self.config is None:
            self.config = self._load_config()

        # Parse config into typed DesiredState models
        self.desired_state = DesiredState.from_config(self.config)

        # Fetch existing resources - ORDER MATTERS!
        try:
            existing_projects = self._get_projects()
            existing_tables = self._get_fact_tables()
            existing_environments = self._get_environments()

            # Create partial state for filter fetching (filters need tables loaded)
            self.state = SyncState(tables=existing_tables)

            # Now fetch filters (needs tables to be in self.state)
            existing_filters = self._get_fact_table_filters()
            existing_metrics = self._get_fact_metrics()

            # Update state with all resources (no reconstruction needed - not frozen!)
            self.state.filters = existing_filters
            self.state.metrics = existing_metrics
            self.state.projects = existing_projects
            self.state.environments = existing_environments
        except requests.RequestException as e:
            typer.echo(f"Error: API request failed: {e}")
            raise typer.Exit(1)

    def compute_changes(self) -> None:
        """Compute what needs to be created/updated/deleted."""
        if self.state is None or self.desired_state is None:
            typer.echo(
                "Error: State not loaded. Call load_config_and_fetch_state() first"
            )
            raise typer.Exit(1)

        current_project_names = set(self.state.projects.keys())
        desired_project_names = self.desired_state.project_names

        current_table_names = set(self.state.tables.keys())
        desired_table_names = self.desired_state.table_names

        current_metric_names = set(self.state.metrics.keys())
        desired_metric_names = self.desired_state.metric_names

        # projects
        all_current_project_names = set(self.state.projects.keys())
        api_managed_project_names = self._api_managed_names(self.state.projects)

        projects_to_create = desired_project_names - all_current_project_names
        projects_to_delete = api_managed_project_names - desired_project_names
        projects_in_both = api_managed_project_names & desired_project_names

        # Check for updates in existing projects (only API-managed)
        projects_to_update = set()
        for name in projects_in_both:
            current_data = self.state.projects[name].data
            desired_data = self.desired_state.projects[name].model_dump(
                exclude_none=True
            )
            if self._has_changes(current_data, desired_data):
                projects_to_update.add(name)

        # Tables
        all_current_table_names = set(self.state.tables.keys())
        api_managed_table_names = self._api_managed_names(self.state.tables)

        tables_to_create = desired_table_names - all_current_table_names
        tables_to_delete = api_managed_table_names - desired_table_names
        tables_in_both = api_managed_table_names & desired_table_names

        # Check for updates in existing tables (only API-managed)
        tables_to_update = set()
        for name in tables_in_both:
            current_data = self.state.tables[name].data
            desired_data = self.desired_state.tables[name].model_dump(exclude_none=True)
            if self._has_changes(current_data, desired_data):
                tables_to_update.add(name)

        # Filters
        all_current_filter_names = set(self.state.filters.keys())
        api_managed_filter_names = self._api_managed_names(self.state.filters)
        desired_filter_names = self.desired_state.filter_names

        filters_to_create = desired_filter_names - all_current_filter_names
        filters_to_delete = api_managed_filter_names - desired_filter_names
        filters_in_both = api_managed_filter_names & desired_filter_names

        # Check for updates in existing filters (only API-managed)
        filters_to_update = set()
        for name in filters_in_both:
            current_data = self.state.filters[name].data
            desired_data = self.desired_state.filters[name].model_dump(
                exclude_none=True
            )
            if self._has_changes(current_data, desired_data):
                filters_to_update.add(name)

        # Metrics
        all_current_metric_names = set(self.state.metrics.keys())
        api_managed_metric_names = self._api_managed_names(self.state.metrics)

        metrics_to_create = desired_metric_names - all_current_metric_names
        metrics_to_delete = api_managed_metric_names - desired_metric_names
        metrics_in_both = api_managed_metric_names & desired_metric_names

        # Check for updates in existing metrics (only API-managed)
        metrics_to_update = set()
        for name in metrics_in_both:
            current_data = self.state.metrics[name].data
            desired_data = self.desired_state.metrics[name].model_dump(
                exclude_none=True
            )
            if self._has_changes(current_data, desired_data):
                metrics_to_update.add(name)

        # Environments (no API-managed filtering, no deletion)
        all_current_env_ids = set(self.state.environments.keys())
        desired_env_ids = self.desired_state.environment_names

        envs_to_create = desired_env_ids - all_current_env_ids

        envs_to_update = set()
        for env_id in desired_env_ids & all_current_env_ids:
            current_data = self.state.environments[env_id].data
            desired_data = self.desired_state.environments[env_id].model_dump(
                exclude_none=True
            )
            if self._has_changes(current_data, desired_data):
                envs_to_update.add(env_id)

        self.changes = ChangePlan(
            projects_to_create=projects_to_create,
            projects_to_update=projects_to_update,
            projects_to_delete=projects_to_delete,
            tables_to_create=tables_to_create,
            tables_to_update=tables_to_update,
            tables_to_delete=tables_to_delete,
            filters_to_create=filters_to_create,
            filters_to_update=filters_to_update,
            filters_to_delete=filters_to_delete,
            metrics_to_create=metrics_to_create,
            metrics_to_update=metrics_to_update,
            metrics_to_delete=metrics_to_delete,
            environments_to_create=envs_to_create,
            environments_to_update=envs_to_update,
        )

    def _filter_by_structure(self, current, desired):
        """Recursively filter current data to match desired structure.

        Only includes fields and nested structures that are present in desired,
        effectively ignoring API metadata at all nesting levels.
        """
        # If desired is a dict, recursively filter nested dicts
        if isinstance(desired, dict):
            if not isinstance(current, dict):
                return current

            filtered = {}
            for key in desired.keys():
                if key in current:
                    # Recursively filter nested values
                    filtered[key] = self._filter_by_structure(
                        current[key], desired[key]
                    )
                else:
                    # Key in desired but not in current (missing field)
                    filtered[key] = None
            return filtered

        # If desired is a list, return current list as-is
        # (we want to compare the full list, including order)
        elif isinstance(desired, list):
            return current

        # For primitives, return current value
        else:
            return current

    def _has_changes(self, current: dict, desired: dict) -> bool:
        """Compare two resource objects to detect changes.

        Only compares fields present in the desired config, recursively filtering
        nested structures to ignore API metadata at all levels.
        """
        # Recursively filter current to match desired structure
        current_filtered = self._filter_by_structure(current, desired)

        # Compare JSON representations to catch any field-level differences
        current_json = json.dumps(current_filtered, sort_keys=True, default=str)
        desired_json = json.dumps(desired, sort_keys=True, default=str)
        return current_json != desired_json

    def display_plan(self) -> None:
        """Display the execution plan."""
        self.load_config_and_fetch_state()
        self.compute_changes()

        if self.state is None or self.desired_state is None or self.changes is None:
            return

        self._display_plan_summary(self.state, self.desired_state, self.changes)

    def _display_plan_summary(
        self,
        state: SyncState,
        desired_state: DesiredState,
        changes: ChangePlan,
    ) -> None:
        """Display plan summary."""
        console = Console()

        typer.echo(
            f"\nConfig: {len(desired_state.table_names)} table(s), "
            f"{len(desired_state.filter_names)} filter(s), "
            f"{len(desired_state.metric_names)} metric(s), "
            f"{len(desired_state.project_names)} project(s), "
            f"{len(desired_state.environment_names)} environment(s)"
        )

        # Calculate API-managed vs ignored counts
        api_tables = len(self._api_managed_names(state.tables))
        ignored_tables = len(state.tables) - api_tables
        api_filters = len(self._api_managed_names(state.filters))
        ignored_filters = len(state.filters) - api_filters
        api_metrics = len(self._api_managed_names(state.metrics))
        ignored_metrics = len(state.metrics) - api_metrics
        api_projects = len(self._api_managed_names(state.projects))
        ignored_projects = len(state.projects) - api_projects

        # Create and display breakdown table
        table = Table(title="GrowthBook Resources")
        table.add_column("Resource Type")
        table.add_column("Total")
        table.add_column("API-Managed")
        table.add_column("Ignored")

        table.add_row("Tables", str(len(state.tables)), str(api_tables), str(ignored_tables))
        table.add_row("Filters", str(len(state.filters)), str(api_filters), str(ignored_filters))
        table.add_row("Metrics", str(len(state.metrics)), str(api_metrics), str(ignored_metrics))
        table.add_row("Projects", str(len(state.projects)), str(api_projects), str(ignored_projects))
        table.add_row("Environments", str(len(state.environments)), str(len(state.environments)), "0")

        console.print(table)

        typer.echo("\nChanges to be applied:")

        if changes.has_changes:
            self._display_creates(changes)
            self._display_updates(changes)
            self._display_deletions(changes)
        else:
            typer.echo("  No changes detected")

    @staticmethod
    def _display_creates(changes: ChangePlan) -> None:
        """Display resources to be created."""
        console = Console()
        total_creates = (
            len(changes.tables_to_create)
            + len(changes.filters_to_create)
            + len(changes.metrics_to_create)
            + len(changes.projects_to_create)
            + len(changes.environments_to_create)
        )
        if total_creates > 0:
            console.print(
                f"\n  To create: {len(changes.tables_to_create)} table(s), "
                f"{len(changes.filters_to_create)} filter(s), "
                f"{len(changes.metrics_to_create)} metric(s), "
                f"{len(changes.projects_to_create)} project(s), "
                f"{len(changes.environments_to_create)} environment(s)",
                style="green"
            )
            for name in sorted(changes.tables_to_create):
                console.print(f"    - Table: {name}", style="green")
            for name in sorted(changes.filters_to_create):
                console.print(f"    - Filter: {name}", style="green")
            for name in sorted(changes.metrics_to_create):
                console.print(f"    - Metric: {name}", style="green")
            for name in sorted(changes.projects_to_create):
                console.print(f"    - Project: {name}", style="green")
            for name in sorted(changes.environments_to_create):
                console.print(f"    - Environment: {name}", style="green")

    @staticmethod
    def _display_updates(changes: ChangePlan) -> None:
        """Display resources to be updated."""
        console = Console()
        total_updates = (
            len(changes.tables_to_update)
            + len(changes.filters_to_update)
            + len(changes.metrics_to_update)
            + len(changes.projects_to_update)
            + len(changes.environments_to_update)
        )
        if total_updates > 0:
            console.print(
                f"\n  To update: {len(changes.tables_to_update)} table(s), "
                f"{len(changes.filters_to_update)} filter(s), "
                f"{len(changes.metrics_to_update)} metric(s), "
                f"{len(changes.projects_to_update)} project(s), "
                f"{len(changes.environments_to_update)} environment(s)",
                style="yellow"
            )
            for name in sorted(changes.tables_to_update):
                console.print(f"    - Table: {name}", style="yellow")
            for name in sorted(changes.filters_to_update):
                console.print(f"    - Filter: {name}", style="yellow")
            for name in sorted(changes.metrics_to_update):
                console.print(f"    - Metric: {name}", style="yellow")
            for name in sorted(changes.projects_to_update):
                console.print(f"    - Project: {name}", style="yellow")
            for name in sorted(changes.environments_to_update):
                console.print(f"    - Environment: {name}", style="yellow")

    @staticmethod
    def _display_deletions(changes: ChangePlan) -> None:
        """Display resources to be deleted."""
        console = Console()
        total_deletes = (
            len(changes.tables_to_delete)
            + len(changes.filters_to_delete)
            + len(changes.metrics_to_delete)
            + len(changes.projects_to_delete)
        )
        if total_deletes > 0:
            console.print(
                f"\n  To delete: {len(changes.tables_to_delete)} tables, "
                f"{len(changes.filters_to_delete)} filters, "
                f"{len(changes.metrics_to_delete)} metrics, "
                f"{len(changes.projects_to_delete)} projects",
                style="red"
            )
            for name in sorted(changes.tables_to_delete):
                console.print(f"    - Table: {name}", style="red")
            for name in sorted(changes.filters_to_delete):
                console.print(f"    - Filter: {name}", style="red")
            for name in sorted(changes.metrics_to_delete):
                console.print(f"    - Metric: {name}", style="red")
            for name in sorted(changes.projects_to_delete):
                console.print(f"    - Project: {name}", style="red")

    def execute_changes(self) -> None:
        """Execute the changes."""
        if self.changes is None:
            typer.echo("Error: No changes computed. Call compute_changes() first")
            raise typer.Exit(1)

        typer.echo("\nApplying changes...")

        # Delete
        # Respect dependency ordering for metrics, filters and factTables
        self._delete_metrics(self.changes.metrics_to_delete)  # depend on filters
        self._delete_filters(self.changes.filters_to_delete)  # depend on tables
        self._delete_tables(self.changes.tables_to_delete)
        self._delete_projects(self.changes.projects_to_delete)

        # update
        self._update_projects()
        self._update_environments()

        # create
        self._create_projects()
        self._create_environments()
        self._bulk_import()  # creates and updates all factTables, factTableFilters and metrics

    def _update_projects(self) -> None:
        """Update existing projects."""
        if not self.changes or not self.state:
            logger.debug("Skipping project update: no changes or state available")
            return

        for name in sorted(self.changes.projects_to_update):
            if name not in self.desired_state.projects:
                typer.echo(f"  Warning: Project '{name}' not found in desired state")
                continue

            if name not in self.state.projects:
                typer.echo(f"  Warning: Project '{name}' not found in current state")
                continue

            project_id = self.state.projects[name].id
            project_config = self.desired_state.projects[name]
            project_data = {
                "name": project_config.name,
                "description": project_config.description or "",
            }

            try:
                res = requests.put(
                    f"{self.api_url}/api/v1/projects/{project_id}",
                    headers=self.headers,
                    json=project_data,
                )
                res.raise_for_status()
                typer.echo(f"  Updated project: {name}")
            except requests.RequestException as e:
                typer.echo(f"  Error updating project '{name}': {e}")

    def _create_projects(self) -> None:
        """Create new projects."""
        if not self.changes:
            logger.debug("Skipping project creation: no changes available")
            return

        for name in sorted(self.changes.projects_to_create):
            if name not in self.desired_state.projects:
                typer.echo(f"  Warning: Project '{name}' not found in desired state")
                continue

            project_config = self.desired_state.projects[name]
            project_data = {
                "name": project_config.name,
                "description": project_config.description or "",
            }

            try:
                res = requests.post(
                    f"{self.api_url}/api/v1/projects",
                    headers=self.headers,
                    json=project_data,
                )
                res.raise_for_status()
                typer.echo(f"  Created project: {name}")
            except requests.RequestException as e:
                typer.echo(f"  Error creating project '{name}': {e}")

    def _create_environments(self) -> None:
        """Create new environments."""
        if not self.changes:
            logger.debug("Skipping environment creation: no changes available")
            return

        for env_id in sorted(self.changes.environments_to_create):
            if env_id not in self.desired_state.environments:
                typer.echo(f"  Warning: Environment '{env_id}' not found in desired state")
                continue

            env_config = self.desired_state.environments[env_id]
            env_data = {
                "id": env_id,
                "description": env_config.description or "",
                "defaultState": env_config.defaultState,
                "toggleOnList": env_config.toggleOnList,
            }

            try:
                res = requests.post(
                    f"{self.api_url}/api/v1/environments",
                    headers=self.headers,
                    json=env_data,
                )
                res.raise_for_status()
                typer.echo(f"  Created environment: {env_id}")
            except requests.RequestException as e:
                typer.echo(f"  Error creating environment '{env_id}': {e}")

    def _update_environments(self) -> None:
        """Update existing environments."""
        if not self.changes or not self.state:
            logger.debug("Skipping environment update: no changes or state available")
            return

        for env_id in sorted(self.changes.environments_to_update):
            if env_id not in self.desired_state.environments:
                typer.echo(f"  Warning: Environment '{env_id}' not found in desired state")
                continue

            if env_id not in self.state.environments:
                typer.echo(f"  Warning: Environment '{env_id}' not found in current state")
                continue

            env_config = self.desired_state.environments[env_id]
            env_data = {
                "description": env_config.description or "",
                "defaultState": env_config.defaultState,
                "toggleOnList": env_config.toggleOnList,
            }

            try:
                res = requests.put(
                    f"{self.api_url}/api/v1/environments/{env_id}",
                    headers=self.headers,
                    json=env_data,
                )
                res.raise_for_status()
                typer.echo(f"  Updated environment: {env_id}")
            except requests.RequestException as e:
                typer.echo(f"  Error updating environment '{env_id}': {e}")

    def _bulk_import(self) -> None:
        """Perform bulk import of fact metrics and tables."""
        try:
            metrics_data = {
                "factTables": self.config.get("factTables", []),
                "factTableFilters": self.config.get("factTableFilters", []),
                "factMetrics": self.config.get("factMetrics", []),
            }
            logger.debug(f"Bulk import payload: {json.dumps(metrics_data, indent=2, default=str)}")
            res = requests.post(
                f"{self.api_url}/api/v1/bulk-import/facts",
                headers=self.headers,
                json=metrics_data,
            )
            res.raise_for_status()
        except requests.RequestException as e:
            error_msg = f"Bulk import failed: {e}"
            try:
                response_body = res.json()
                error_msg += f"\nAPI Response: {json.dumps(response_body, indent=2)}"
            except (AttributeError, ValueError):
                pass
            typer.echo(f"Error: {error_msg}")
            raise typer.Exit(1)
