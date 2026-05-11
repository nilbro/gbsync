"""Command-line interface for gbsync."""

import requests
import typer

from gbsync.client import GrowthBookSyncClient


def _create_sync_client(
    config_file: str, api_key: str, api_url: str
) -> GrowthBookSyncClient:
    """Create and validate a GrowthBook sync client."""
    if not api_key:
        typer.echo("Error: API key required (set GB_API_KEY or use --api-key)")
        raise typer.Exit(1)
    return GrowthBookSyncClient(api_url, api_key, config_file)


# Common options
CONFIG_FILE_OPTION = typer.Option(
    "gbsync.yaml",
    "--config",
    "-c",
    help="Path to metrics configuration file",
)
API_KEY_OPTION = typer.Option(
    None,
    "--api-key",
    envvar="GB_API_KEY",
    help="GrowthBook API key (or GB_API_KEY env var)",
)
API_URL_OPTION = typer.Option(
    None,
    "--api-url",
    envvar="GB_API_URL",
    help="GrowthBook API URL (or GB_API_URL env var)",
)

app = typer.Typer(help="GrowthBook metrics synchronization tool")


@app.command()
def plan(
    config_file: str = CONFIG_FILE_OPTION,
    api_key: str = API_KEY_OPTION,
    api_url: str = API_URL_OPTION,
) -> None:
    """Show what changes would be made to GrowthBook."""
    gb = _create_sync_client(config_file, api_key, api_url)
    gb.display_plan()


@app.command()
def apply(
    config_file: str = CONFIG_FILE_OPTION,
    api_key: str = API_KEY_OPTION,
    api_url: str = API_URL_OPTION,
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Apply changes to GrowthBook."""
    gb = _create_sync_client(config_file, api_key, api_url)
    gb.display_plan()

    # Ask for confirmation (unless auto-approve)
    if not auto_approve:
        if not typer.confirm("\nProceed with apply?"):
            typer.echo("Cancelled")
            raise typer.Exit(0)

    # Execute changes
    try:
        gb.execute_changes()
        typer.echo("\n✓ Applied successfully")
    except requests.RequestException as e:
        typer.echo(f"Error: Apply failed: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
