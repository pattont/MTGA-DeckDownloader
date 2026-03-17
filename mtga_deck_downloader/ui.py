from __future__ import annotations

import shutil
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
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


def _render_site_header(console: Console) -> None:
    title = Text()
    title.append("Magic: ", style="bold white")
    title.append("The Gathering Arena", style="bold white")
    title.append("  |  ", style="dim")
    title.append("Deck Downloader", style="bold bright_yellow")
    
    icons = Text("🟡 🔵 ⚫ 🔴 🟢")

    subtitle = Text("Select a decklist source website to begin.", style="white")
    scope = Text(
        "Currently supports Standard BO1 and BO3 decklists - others coming soon.",
        style="bold yellow",
    )
    console.print(
        Panel(
            Text.assemble(title, "\n\n", icons, "\n\n", subtitle, "\n", scope),
            border_style="bright_black",
        )
    )


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

            selected_source = _pick_source(console, provider, selected_format)
            if selected_source == "b":
                _clear_screen(console)
                continue

            decks = _fetch_decks(
                console=console,
                provider=provider,
                selected_format=selected_format,
                limit=50,
                selected_source=selected_source,
            )
            if decks is None:
                console.input("\n[dim]Press Enter to continue[/dim]")
                continue

            action = _browse_decks(
                console,
                provider,
                selected_format,
                decks,
                selected_source=selected_source,
            )
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
    selected_source: DeckSource | None,
) -> list[DeckEntry] | None:
    _clear_screen(console)
    source_label = selected_source.name if selected_source else "all matching endpoints"
    try:
        with console.status(
            f"[bold cyan]Fetching deck data from {provider.display_name} ({source_label})...[/bold cyan]"
        ):
            decks = provider.fetch_decks(
                selected_format=selected_format,
                limit=limit,
                source=selected_source,
            )
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
    selected_source: DeckSource | None = None,
) -> str:
    is_untapped = provider.key == "untapped"
    while True:
        _show_deck_table(
            console,
            provider,
            selected_format,
            decks,
            selected_source=selected_source,
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
                        selected_source=selected_source,
                        archetype=selected,
                        variants=variants,
                    )
                    if variant_action in {"f", "s", "q"}:
                        return variant_action
                    continue

                detailed_deck = _show_deck_detail(console, provider, selected)
                decks[index - 1] = detailed_deck
                continue
        console.print("[yellow]Invalid input. Enter a deck number, f, s, or q.[/yellow]")


def _show_deck_table(
    console: Console,
    provider: DeckProvider,
    selected_format: MatchFormat,
    decks: list[DeckEntry],
    selected_source: DeckSource | None = None,
    title: str = "Scraped Deck Results",
    count_label: str = "Decks found",
    name_column_label: str = "Deck",
) -> None:
    _clear_screen(console)
    source_text = (
        f"Source endpoint: [bold cyan]{selected_source.name}[/bold cyan]\n"
        if selected_source is not None
        else ""
    )
    console.print(
        Panel(
            f"[bold green]{provider.display_name}[/bold green]\n"
            f"Format filter: [bold cyan]{selected_format.label}[/bold cyan]\n"
            f"{source_text}"
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
    selected_source: DeckSource | None = None,
) -> str:
    while True:
        _show_deck_table(
            console=console,
            provider=provider,
            selected_format=selected_format,
            decks=variants,
            selected_source=selected_source,
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
                detailed_deck = _show_deck_detail(console, provider, variants[index - 1])
                variants[index - 1] = detailed_deck
                continue
        console.print("[yellow]Invalid input. Enter a deck number, b, f, s, or q.[/yellow]")


def _show_deck_detail(console: Console, provider: DeckProvider, deck: DeckEntry) -> DeckEntry:
    hydrated = deck
    if hydrated.deck_text is None:
        try:
            with console.status("[bold cyan]Loading deck details...[/bold cyan]"):
                hydrated = provider.hydrate_deck(deck)
        except Exception as exc:
            console.print(f"[yellow]Could not load additional deck detail: {exc}[/yellow]")

    _clear_screen(console)
    info_lines = [
        f"[bold]Deck:[/bold] {hydrated.name}",
        f"[bold]Source:[/bold] {hydrated.source_site}",
    ]
    if hydrated.event_name:
        info_lines.append(f"[bold]Event:[/bold] {hydrated.event_name}")
    info_lines.extend(
        [
            f"[bold]URL:[/bold] {hydrated.source_url}",
            f"[bold]Format:[/bold] {hydrated.format_label}",
        ]
    )
    if hydrated.win_rate is not None:
        info_lines.append(f"[bold]Win Rate:[/bold] {_format_percent(hydrated.win_rate)}")
    if hydrated.matches is not None:
        info_lines.append(f"[bold]Matches:[/bold] {hydrated.matches}")
    if hydrated.event_date:
        info_lines.append(f"[bold]Event Date:[/bold] {hydrated.event_date}")
    if hydrated.notes:
        info_lines.append(f"[bold]Note:[/bold] {hydrated.notes}")

    console.print(Panel("\n".join(info_lines), title="Deck Details", border_style="green"))

    formatted_deck_text = _format_arena_import_text(hydrated.deck_text)
    if formatted_deck_text:
        console.print("\n[bold cyan]Arena Import Text[/bold cyan]\n")
        console.print(formatted_deck_text, soft_wrap=True)
    else:
        console.print(
            "[yellow]This source did not provide direct MTGA import text for this deck.[/yellow]"
        )

    while True:
        raw = (
            console.input(
                "\n[bold yellow]c=copy decklist to clipboard[/bold yellow], "
                "[bold cyan]Enter=go back to list (Enter)[/bold cyan]: "
            )
            .strip()
            .lower()
        )
        if raw == "":
            break
        if raw == "c":
            if not formatted_deck_text:
                console.print("[yellow]No Arena import text available to copy.[/yellow]")
                continue
            copied, error = _copy_to_clipboard(formatted_deck_text)
            if copied:
                console.print("[bold green]Copied decklist to clipboard.[/bold green]")
            else:
                console.print(
                    "[yellow]Could not copy automatically. Select the text manually.[/yellow]"
                )
                if error:
                    console.print(f"[dim]{error}[/dim]")
            continue
        console.print("[yellow]Invalid input. Press Enter or type c.[/yellow]")
    return hydrated


def _format_arena_import_text(deck_text: str | None) -> str | None:
    if not deck_text:
        return None

    section_headers = {"sideboard", "companion", "commander", "maybeboard"}
    lines = deck_text.splitlines()
    formatted: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() in section_headers:
            if formatted and formatted[-1].strip():
                formatted.append("")
            formatted.append(stripped)
            continue
        formatted.append(line.rstrip())

    return "\n".join(formatted).strip("\n")


def _copy_to_clipboard(text: str) -> tuple[bool, str | None]:
    if not text:
        return False, "No text to copy."

    def _run(cmd: list[str], use_shell: bool = False) -> tuple[bool, str | None]:
        try:
            subprocess.run(
                cmd if not use_shell else " ".join(cmd),
                input=text,
                text=True,
                check=True,
                shell=use_shell,
            )
            return True, None
        except Exception as exc:
            return False, str(exc)

    if sys.platform == "darwin":
        return _run(["pbcopy"])

    if sys.platform.startswith("win"):
        ok, _ = _run(
            ["powershell", "-NoProfile", "-Command", "Set-Clipboard"],
            use_shell=False,
        )
        if ok:
            return True, None
        return _run(["clip"], use_shell=True)

    if shutil.which("wl-copy"):
        return _run(["wl-copy"])
    if shutil.which("xclip"):
        return _run(["xclip", "-selection", "clipboard"])
    if shutil.which("xsel"):
        return _run(["xsel", "--clipboard", "--input"])

    return False, "No clipboard command found (tried pbcopy, powershell/clip, wl-copy, xclip, xsel)."


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
        _render_site_header(console)

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", justify="right", style="bold")
        table.add_column("Site", style="bold green")
        table.add_column("Description")

        for idx, provider in enumerate(providers, start=1):
            table.add_row(str(idx), provider.display_name, provider.description)

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


def _pick_source(
    console: Console, provider: DeckProvider, selected_format: MatchFormat
) -> DeckSource | str | None:
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
        return "b"

    for idx, source in enumerate(sources, start=1):
        table.add_row(str(idx), source.name, source.description, source.url)
    console.print(table)

    if len(sources) == 1:
        console.print("\n[dim]Only one endpoint matches this format. Using it automatically...[/dim]")
        return sources[0]

    while True:
        raw = Prompt.ask(
            "\n[bold cyan]Select endpoint #, a=all matching, b=back[/bold cyan]",
            default="a",
            show_choices=False,
        ).strip()
        lowered = raw.lower()
        if lowered == "b":
            return "b"
        if lowered == "a":
            return None
        if raw.isdigit():
            selection = int(raw)
            if 1 <= selection <= len(sources):
                return sources[selection - 1]
        console.print("[yellow]Invalid selection. Enter a source number, a, or b.[/yellow]")
