from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from mtga_deck_downloader.models import DeckEntry, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider
from mtga_deck_downloader.providers.registry import load_providers


def _clear_screen(console: Console) -> None:
    console.clear()
    # Request scrollback purge on terminals that support CSI 3J.
    if console.is_terminal:
        try:
            console.file.write("\x1b[3J")
            console.file.flush()
        except Exception:
            pass


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
                _clear_screen(console)
                break

            _show_sources(console, provider, selected_format)
            decks = _fetch_decks(console, provider, selected_format, limit=50)
            if decks is None:
                console.input("\n[dim]Press Enter to continue[/dim]")
                continue

            action = _browse_decks(console, provider, selected_format, decks)
            if action == "q":
                _clear_screen(console)
                console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
                return
            if action == "s":
                _clear_screen(console)
                break
            if action == "f":
                _clear_screen(console)


def _fetch_decks(
    console: Console,
    provider: DeckProvider,
    selected_format: MatchFormat,
    limit: int,
) -> list[DeckEntry] | None:
    _clear_screen(console)
    try:
        with console.status(
            f"[bold cyan]Fetching deck data from {provider.display_name}...[/bold cyan]"
        ):
            decks = provider.fetch_decks(selected_format=selected_format, limit=limit)
    except Exception as exc:
        console.print(
            f"\n[bold red]Failed to fetch deck data from {provider.display_name}.[/bold red]"
        )
        console.print(f"[red]{exc}[/red]")
        return None

    if not decks:
        console.print("\n[yellow]No decks found for the selected filter.[/yellow]")
        return None
    return decks


def _browse_decks(
    console: Console,
    provider: DeckProvider,
    selected_format: MatchFormat,
    decks: list[DeckEntry],
) -> str:
    is_untapped = provider.key == "untapped"
    while True:
        _show_deck_table(
            console,
            provider,
            selected_format,
            decks,
            title="Scraped Deck Results",
            count_label="Archetypes found" if is_untapped else "Decks found",
            name_column_label="Archetype" if is_untapped else "Deck",
        )
        prompt = (
            "\n[bold cyan]Archetype # for variants, f=format, s=site, q=quit[/bold cyan]"
            if is_untapped
            else "\n[bold cyan]Deck # for details, f=format, s=site, q=quit[/bold cyan]"
        )
        raw = Prompt.ask(
            prompt,
            default="f",
            show_choices=False,
        ).strip()
        lowered = raw.lower()
        if lowered in {"f", "s", "q"}:
            return lowered
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(decks):
                selected = decks[index - 1]
                try:
                    _clear_screen(console)
                    with console.status(
                        f"[bold cyan]Fetching variant decks for {selected.name}...[/bold cyan]"
                    ):
                        variants = provider.fetch_deck_variants(
                            deck=selected,
                            selected_format=selected_format,
                            limit=50,
                        )
                except Exception as exc:
                    console.print(f"[red]Failed to load variant decks: {exc}[/red]")
                    console.input("\n[dim]Press Enter to return to results[/dim]")
                    continue

                if variants:
                    variant_action = _browse_variants(
                        console=console,
                        provider=provider,
                        selected_format=selected_format,
                        archetype=selected,
                        variants=variants,
                    )
                    if variant_action in {"f", "s", "q"}:
                        return variant_action
                    continue

                _show_deck_detail(console, selected)
                console.input("\n[dim]Press Enter to return to results[/dim]")
                continue
        console.print("[yellow]Invalid input. Enter a deck number, f, s, or q.[/yellow]")


def _show_deck_table(
    console: Console,
    provider: DeckProvider,
    selected_format: MatchFormat,
    decks: list[DeckEntry],
    title: str = "Scraped Deck Results",
    count_label: str = "Decks found",
    name_column_label: str = "Deck",
) -> None:
    _clear_screen(console)
    console.print(
        Panel(
            f"[bold green]{provider.display_name}[/bold green]\n"
            f"Format filter: [bold cyan]{selected_format.label}[/bold cyan]\n"
            f"{count_label}: [bold]{len(decks)}[/bold]",
            title=title,
            border_style="cyan",
        )
    )

    show_win_rate = any(deck.win_rate is not None for deck in decks)
    show_matches = any(deck.matches is not None for deck in decks)
    is_magic_gg = provider.key == "magic_gg"

    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("#", justify="right", style="bold")
    table.add_column(name_column_label, style="bold")
    if show_win_rate:
        table.add_column("Win %", justify="right")
    if show_matches:
        table.add_column("Matches", justify="right")
    table.add_column("Format", no_wrap=True)
    table.add_column(
        "Event/Notes",
        overflow="fold" if is_magic_gg else "ellipsis",
        max_width=72 if is_magic_gg else 44,
    )

    for idx, deck in enumerate(decks, start=1):
        note = _table_note(deck, truncate=not is_magic_gg)
        row = [
            str(idx),
            deck.name,
            deck.format_label,
            note,
        ]
        if show_win_rate:
            row.insert(2, _format_percent(deck.win_rate))
        if show_matches:
            row.insert(3 if show_win_rate else 2, str(deck.matches) if deck.matches is not None else "-")
        table.add_row(*row)
    console.print(table)


def _browse_variants(
    console: Console,
    provider: DeckProvider,
    selected_format: MatchFormat,
    archetype: DeckEntry,
    variants: list[DeckEntry],
) -> str:
    while True:
        _show_deck_table(
            console=console,
            provider=provider,
            selected_format=selected_format,
            decks=variants,
            title=f"{archetype.name} Variants",
            count_label="Deck variants",
            name_column_label="Deck",
        )
        raw = Prompt.ask(
            "\n[bold cyan]Deck # for details, b=back, f=format, s=site, q=quit[/bold cyan]",
            default="b",
            show_choices=False,
        ).strip()
        lowered = raw.lower()
        if lowered in {"b", "f", "s", "q"}:
            return lowered
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(variants):
                _show_deck_detail(console, variants[index - 1])
                console.input("\n[dim]Press Enter to return to variants[/dim]")
                continue
        console.print("[yellow]Invalid input. Enter a deck number, b, f, s, or q.[/yellow]")


def _show_deck_detail(console: Console, deck: DeckEntry) -> None:
    _clear_screen(console)
    info_lines = [
        f"[bold]Deck:[/bold] {deck.name}",
        f"[bold]Source:[/bold] {deck.source_site}",
    ]
    if deck.event_name:
        info_lines.append(f"[bold]Event:[/bold] {deck.event_name}")
    info_lines.extend(
        [
            f"[bold]URL:[/bold] {deck.source_url}",
            f"[bold]Format:[/bold] {deck.format_label}",
        ]
    )
    if deck.win_rate is not None:
        info_lines.append(f"[bold]Win Rate:[/bold] {_format_percent(deck.win_rate)}")
    if deck.matches is not None:
        info_lines.append(f"[bold]Matches:[/bold] {deck.matches}")
    if deck.event_date:
        info_lines.append(f"[bold]Event Date:[/bold] {deck.event_date}")
    if deck.notes:
        info_lines.append(f"[bold]Note:[/bold] {deck.notes}")

    console.print(Panel("\n".join(info_lines), title="Deck Details", border_style="green"))

    if deck.deck_text:
        console.print(Panel(deck.deck_text, title="Arena Import Text", border_style="cyan"))
    else:
        console.print(
            "[yellow]This source did not provide direct MTGA import text for this deck.[/yellow]"
        )


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}%"


def _table_note(deck: DeckEntry, truncate: bool) -> str:
    if deck.event_name:
        return _truncate(deck.event_name, 42) if truncate else deck.event_name
    if not deck.notes:
        return "-"
    note = deck.notes.replace("\n", " ").strip()
    return _truncate(note, 42) if truncate else note


def _truncate(value: str, limit: int) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _pick_provider(console: Console, providers: list[DeckProvider]) -> DeckProvider | None:
    while True:
        _clear_screen(console)
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
        _clear_screen(console)
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
    _clear_screen(console)
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

    console.print("\n[dim]Source endpoints detected. Fetching deck data next...[/dim]")
