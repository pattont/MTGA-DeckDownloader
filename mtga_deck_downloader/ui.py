from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from mtga_deck_downloader.models import MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider
from mtga_deck_downloader.providers.registry import load_providers


def run_app() -> None:
    console = Console()
    providers = load_providers()

    if not providers:
        console.print("[bold red]No providers found. Add provider modules first.[/bold red]")
        return

    while True:
        provider = _pick_provider(console, providers)
        if provider is None:
            console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
            return

        while True:
            selected_format = _pick_format(console, provider)
            if selected_format is None:
                break

            _show_sources(console, provider, selected_format)
            choice = Prompt.ask(
                "\n[bold cyan]Next action[/bold cyan]",
                choices=["f", "s", "q"],
                default="f",
                show_choices=False,
            )
            if choice == "q":
                console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
                return
            if choice == "s":
                break


def _pick_provider(console: Console, providers: list[DeckProvider]) -> DeckProvider | None:
    while True:
        console.clear()
        header = Text("MTGA Deck Downloader", style="bold bright_cyan")
        subtitle = Text(
            "Select a source website. Modular providers can be added at any time.",
            style="white",
        )
        console.print(Panel(Text.assemble(header, "\n", subtitle), border_style="cyan"))

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", justify="right", style="bold")
        table.add_column("Site", style="bold green")
        table.add_column("Supports")
        table.add_column("Description")

        for idx, provider in enumerate(providers, start=1):
            formats = ", ".join(
                sorted(match_format.label for match_format in provider.supported_formats)
            )
            table.add_row(str(idx), provider.display_name, formats, provider.description)

        console.print(table)
        raw = Prompt.ask("\n[bold cyan]Select site number (or q to quit)[/bold cyan]")
        if raw.lower() == "q":
            return None
        if raw.isdigit():
            selection = int(raw)
            if 1 <= selection <= len(providers):
                return providers[selection - 1]
        console.print("[yellow]Invalid selection. Try again.[/yellow]")


def _pick_format(console: Console, provider: DeckProvider) -> MatchFormat | None:
    while True:
        console.clear()
        console.print(
            Panel(
                f"[bold green]{provider.display_name}[/bold green]\n"
                f"{provider.description}\n"
                f"[cyan]{provider.homepage}[/cyan]",
                title="Selected Site",
                border_style="green",
            )
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", justify="right", style="bold")
        table.add_column("Format")
        table.add_row("1", MatchFormat.ANY.label)
        table.add_row("2", MatchFormat.BO1.label)
        table.add_row("3", MatchFormat.BO3.label)
        console.print(table)

        raw = Prompt.ask("\n[bold cyan]Select format (or b to go back)[/bold cyan]")
        if raw.lower() == "b":
            return None
        if raw == "1":
            return MatchFormat.ANY
        if raw == "2":
            return MatchFormat.BO1
        if raw == "3":
            return MatchFormat.BO3
        console.print("[yellow]Invalid selection. Try again.[/yellow]")


def _show_sources(console: Console, provider: DeckProvider, selected_format: MatchFormat) -> None:
    sources = provider.list_sources(selected_format)
    console.clear()
    console.print(
        Panel(
            f"[bold green]{provider.display_name}[/bold green]\n"
            f"Format filter: [bold cyan]{selected_format.label}[/bold cyan]",
            title="Deck Source Endpoints",
            border_style="cyan",
        )
    )

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("URL", overflow="fold")

    if not sources:
        console.print("[yellow]No source endpoints match that format.[/yellow]")
    else:
        for idx, source in enumerate(sources, start=1):
            table.add_row(str(idx), source.name, source.description, source.url)
        console.print(table)

    console.print(
        "\n[dim]f = choose another format, s = choose another site, q = quit[/dim]"
    )
