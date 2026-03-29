"""CLI entry point for content-downloader (stub — will be fully implemented in Task 8)."""

import click


@click.group()
@click.version_option()
def main() -> None:
    """Unified content downloader — give a URL, get standardized local files."""


# Subcommands will be registered in Task 8
