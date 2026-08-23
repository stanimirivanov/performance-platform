"""Command-line interface for Performance Engineering Platform."""

import typer

app = typer.Typer(
    name="perfeng",
    help="Continuous Performance Engineering Platform CLI",
)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("PerfEng version 0.1.0")


@app.command()
def init() -> None:
    """Initialize performance test configuration."""
    typer.echo("Initializing performance test configuration...")


if __name__ == "__main__":
    app()
