from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from app.config import get_config
from app.main import run_web_app
from app.mcp_server import run_mcp_server
from app.testing.dummy_vlm_server import run_dummy_vlm_server

CLI_THEME = Theme(
    {
        "accent": "bold cyan",
        "headline": "bold bright_white",
        "muted": "bright_black",
        "success": "bold green",
        "warning": "bold yellow",
        "info": "bold blue",
    }
)

FISH_ART = r"""
            __
       _.-~  )
    _.-~    /  
 .-~      _/   
/  _   _-~      
\_/ |_|         
"""


def create_parser() -> argparse.ArgumentParser:
    """Create the OpenFish command-line parser."""
    parser = argparse.ArgumentParser(
        prog="openfish",
        description="OpenFish command deck for the web app, MCP server, and local test tools.",
    )
    parser.add_argument("--plain", action="store_true", help="Disable ANSI color styling.")
    parser.add_argument("--no-banner", action="store_true", help="Skip the startup fish banner.")

    subparsers = parser.add_subparsers(dest="command")

    ui_parser = subparsers.add_parser("ui", help="Run the OpenFish web workspace.")
    ui_parser.add_argument("--host", default="127.0.0.1")
    ui_parser.add_argument("--port", type=int, default=8000)
    ui_parser.add_argument("--reload", action=argparse.BooleanOptionalAction, default=True)

    mcp_parser = subparsers.add_parser("mcp", help="Run the OpenFish MCP server.")
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )

    dummy_parser = subparsers.add_parser("dummy-vlm", help="Run the dummy OpenAI-compatible VLM server.")
    dummy_parser.add_argument("--host", default="127.0.0.1")
    dummy_parser.add_argument("--port", type=int, default=8010)

    subparsers.add_parser("doctor", help="Show the current OpenFish local configuration.")
    return parser


def _console(plain: bool) -> Console:
    return Console(theme=CLI_THEME, color_system=None if plain else "auto")


def render_banner(console: Console) -> None:
    """Render the OpenFish startup banner."""
    fish_text = Text(FISH_ART, style="accent")
    subtitle = Text("Personal AI Poker Assistant", style="success")
    panel = Panel.fit(
        Text.assemble(
            fish_text,
            ("\nOpenFish Command Deck\n", "headline"),
            (subtitle.plain, "success"),
        ),
        border_style="accent",
        title="[headline]Welcome Aboard[/headline]",
    )
    console.print(panel)


def render_welcome(console: Console, parser: argparse.ArgumentParser) -> None:
    """Render the default OpenFish CLI welcome screen."""
    command_table = Table(show_header=True, header_style="headline", border_style="accent")
    command_table.add_column("Command", style="accent")
    command_table.add_column("Purpose", style="muted")
    command_table.add_row("openfish ui", "Launch the browser workspace on localhost.")
    command_table.add_row("openfish mcp", "Expose OpenFish tools over MCP.")
    command_table.add_row("openfish dummy-vlm", "Run the fake OpenAI-compatible VLM server.")
    command_table.add_row("openfish doctor", "Inspect local config and solver wiring.")

    console.print(command_table)
    console.print(
        Panel.fit(
            "Choose a command to get started. Example: [accent]openfish ui[/accent]",
            border_style="info",
            title="[info]Next Step[/info]",
        )
    )
    parser.print_help()


def render_status(console: Console, title: str, body: str) -> None:
    """Render a friendly status panel for a command launch."""
    console.print(Panel.fit(body, border_style="success", title=f"[success]{title}[/success]"))


def run_doctor(console: Console) -> int:
    """Print the current OpenFish runtime configuration."""
    config = get_config()
    table = Table(show_header=True, header_style="headline", border_style="accent")
    table.add_column("Setting", style="accent")
    table.add_column("Value")
    table.add_column("Status", style="muted")

    solver_bin = Path(config.texassolver_bin) if config.texassolver_bin else None
    solver_resources = Path(config.texassolver_resource_dir) if config.texassolver_resource_dir else None

    table.add_row("VLM base URL", config.base_url, "configured")
    table.add_row("VLM model", config.model, "configured")
    table.add_row("Solver mode", config.solver_mode, "configured")
    table.add_row(
        "TexasSolver binary",
        str(solver_bin) if solver_bin else "<unset>",
        "present" if solver_bin and solver_bin.exists() else "missing",
    )
    table.add_row(
        "TexasSolver resources",
        str(solver_resources) if solver_resources else "<unset>",
        "present" if solver_resources and solver_resources.exists() else "missing",
    )
    table.add_row("Solver cache dir", config.solver_cache_dir, "local")
    table.add_row("Solver work dir", config.solver_work_dir, "local")

    console.print(table)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the OpenFish command-line interface."""
    parser = create_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    console = _console(args.plain)

    if not args.no_banner:
        render_banner(console)

    if args.command is None:
        render_welcome(console, parser)
        return 0

    if args.command == "ui":
        render_status(
            console,
            "Launching Workspace",
            f"Serving OpenFish on http://{args.host}:{args.port} with reload={'on' if args.reload else 'off'}.",
        )
        run_web_app(host=args.host, port=args.port, reload=args.reload)
        return 0

    if args.command == "mcp":
        render_status(
            console,
            "Launching MCP",
            f"Starting the MCP server with [accent]{args.transport}[/accent] transport.",
        )
        run_mcp_server(transport=args.transport)
        return 0

    if args.command == "dummy-vlm":
        render_status(
            console,
            "Launching Dummy VLM",
            f"Starting the dummy VLM server on http://{args.host}:{args.port}.",
        )
        run_dummy_vlm_server(host=args.host, port=args.port)
        return 0

    if args.command == "doctor":
        render_status(console, "Running Doctor", "Inspecting local OpenFish configuration.")
        return run_doctor(console)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
