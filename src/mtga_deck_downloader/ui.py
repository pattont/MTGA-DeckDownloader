from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider, ResultViewConfig
from mtga_deck_downloader.providers.registry import LAST_PROVIDER_ERRORS, load_providers

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"


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
        "Currently supports Standard BO1/BO3 sources, configurable Moxfield creators, and TCGPlayer Standard feeds.",
        style="bold yellow",
    )
    console.print(
        Panel(
            Text.assemble(title, "\n\n", icons, "\n\n", subtitle, "\n", scope),
            border_style="bright_black",
        )
    )


def _missing_runtime_modules() -> list[str]:
    required = {
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "cloudscraper": "cloudscraper",
    }
    missing: list[str] = []
    for module_name, package_name in required.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return missing


def _render_dependency_error(console: Console, missing_packages: list[str]) -> None:
    install_cmd = f"{sys.executable} -m pip install -r {REQUIREMENTS_PATH}"
    lines = [
        "[bold red]Missing Python dependencies for this interpreter.[/bold red]",
        "",
        f"[bold]Python:[/bold] {sys.executable}",
        f"[bold]Missing:[/bold] {', '.join(missing_packages)}",
        "",
        "[bold]Fix:[/bold]",
        install_cmd,
    ]

    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists() and Path(sys.executable) != venv_python:
        lines.extend(
            [
                "",
                "[bold]Repo virtualenv:[/bold]",
                f"{venv_python} {REPO_ROOT / 'app.py'}",
            ]
        )

    console.print(
        Panel(
            "\n".join(lines),
            title="Missing Dependencies",
            border_style="red",
        )
    )


def _continue_or_quit(console: Console, message: str) -> bool:
    raw = console.input(f"\n[dim]{message}[/dim] ").strip().lower()
    return raw == "q"


def run_app() -> None:
    console = Console()
    missing_packages = _missing_runtime_modules()
    if missing_packages:
        _render_dependency_error(console, missing_packages)
        return

    providers = load_providers()

    if not providers:
        if LAST_PROVIDER_ERRORS:
            console.print(
                Panel(
                    "\n".join(LAST_PROVIDER_ERRORS),
                    title="Provider Load Errors",
                    border_style="yellow",
                )
            )
        console.print("[bold red]No providers found. Add provider modules first.[/bold red]")
        return

    while True:
        provider = _pick_provider(console, providers)
        if provider is None:
            console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
            return

        while True:
            format_selection = _pick_format(console, provider)
            if format_selection == "q":
                _clear_screen(console)
                console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
                return
            if format_selection is None:
                _clear_screen(console)
                break

            if isinstance(format_selection, DeckSource):
                selected_format = MatchFormat.ANY
                selected_source = format_selection
            else:
                selected_format = format_selection
                selected_source = _pick_source(console, provider, selected_format)
                if selected_source == "q":
                    _clear_screen(console)
                    console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
                    return
                if selected_source == "b":
                    _clear_screen(console)
                    if provider.supported_formats == {MatchFormat.ANY}:
                        break
                    continue

            decks = _fetch_decks(
                console=console,
                provider=provider,
                selected_format=selected_format,
                limit=50,
                selected_source=selected_source,
            )
            if decks is None:
                if _continue_or_quit(console, "Press Enter to continue or q to quit"):
                    _clear_screen(console)
                    console.print("\n[bold]Exiting MTGA Deck Downloader.[/bold]")
                    return
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
    view_config = provider.result_view_config(selected_source)
    change_label = provider.change_label
    while True:
        _show_deck_table(
            console,
            provider,
            selected_format,
            decks,
            selected_source=selected_source,
            title=view_config.title,
            count_label=view_config.count_label,
            name_column_label=view_config.name_column_label,
        )
        prompt = (
            f"\n[bold cyan]{view_config.selection_label} # for {view_config.selection_action}, "
            f"f={change_label}, s=site, q=quit[/bold cyan]"
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
                    if _continue_or_quit(console, "Press Enter to return to results or q to quit"):
                        return "q"
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
                if detailed_deck == "q":
                    return "q"
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
    suppress_event_names = (
        provider.key == "tcgplayer"
        and selected_source is not None
        and selected_source.name == "Events"
        and title.endswith("Top Decks")
    )
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
    show_player = any(deck.player_name is not None for deck in decks)
    show_placing = any(deck.placing is not None for deck in decks)
    is_magic_gg = provider.key == "magic_gg"

    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("#", justify="right", style="bold")
    table.add_column(name_column_label, style="bold")
    if show_win_rate:
        table.add_column("Win %", justify="right")
    if show_matches:
        table.add_column("Matches", justify="right")
    if show_placing:
        table.add_column("Place", no_wrap=True)
    if show_player:
        table.add_column("Player", overflow="fold", max_width=20)
    table.add_column("Format", no_wrap=True)
    table.add_column(
        "Event/Notes",
        overflow="fold" if is_magic_gg else "ellipsis",
        max_width=72 if is_magic_gg else 44,
    )

    for idx, deck in enumerate(decks, start=1):
        note = _table_note(
            deck,
            truncate=not is_magic_gg,
            include_event_name=not suppress_event_names,
        )
        row = [str(idx), deck.name]
        if show_win_rate:
            row.append(_format_percent(deck.win_rate))
        if show_matches:
            row.append(str(deck.matches) if deck.matches is not None else "-")
        if show_placing:
            row.append(deck.placing or "-")
        if show_player:
            row.append(deck.player_name or "-")
        row.extend([deck.format_label, note])
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
    view_config = provider.result_view_config(
        selected_source,
        variants=True,
        parent=archetype,
    )
    change_label = provider.change_label
    while True:
        _show_deck_table(
            console=console,
            provider=provider,
            selected_format=selected_format,
            decks=variants,
            selected_source=selected_source,
            title=view_config.title,
            count_label=view_config.count_label,
            name_column_label=view_config.name_column_label,
        )
        raw = Prompt.ask(
            f"\n[bold cyan]{view_config.selection_label} # for {view_config.selection_action}, "
            f"b=back, f={change_label}, s=site, q=quit[/bold cyan]",
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
                if detailed_deck == "q":
                    return "q"
                variants[index - 1] = detailed_deck
                continue
        console.print("[yellow]Invalid input. Enter a deck number, b, f, s, or q.[/yellow]")


def _show_deck_detail(console: Console, provider: DeckProvider, deck: DeckEntry) -> DeckEntry | str:
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
    if hydrated.placing:
        info_lines.append(f"[bold]Place:[/bold] {hydrated.placing}")
    if hydrated.player_name:
        info_lines.append(f"[bold]Player:[/bold] {hydrated.player_name}")
    if hydrated.event_date:
        info_lines.append(f"[bold]Event Date:[/bold] {hydrated.event_date}")
    if hydrated.notes:
        info_lines.append(f"[bold]Note:[/bold] {hydrated.notes}")

    console.print(Panel("\n".join(info_lines), title="Deck Details", border_style="green"))

    formatted_deck_text = _format_arena_import_text(hydrated.deck_text)
    if formatted_deck_text:
        console.print("\n[bold cyan]Arena Import Text[/bold cyan]\n")
        console.print(formatted_deck_text, soft_wrap=True)
        copied, error = _copy_to_clipboard(formatted_deck_text)
        if copied:
            console.print("\n[bold green]Decklist copied to clipboard automatically.[/bold green]")
        else:
            console.print(
                "\n[yellow]Could not copy automatically. Select the text manually.[/yellow]"
            )
            if error:
                console.print(f"[dim]{error}[/dim]")
    else:
        console.print(
            "[yellow]This source did not provide direct MTGA import text for this deck.[/yellow]"
        )

    while True:
        raw = (
            console.input(
                "\n[bold cyan]Enter=go back to list (Enter), q=quit[/bold cyan]: "
            )
            .strip()
            .lower()
        )
        if raw == "":
            break
        if raw == "q":
            return "q"
        console.print("[yellow]Invalid input. Press Enter to go back or q to quit.[/yellow]")
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


def _table_note(deck: DeckEntry, truncate: bool, include_event_name: bool = True) -> str:
    note_parts: list[str] = []
    if include_event_name and deck.event_name:
        note_parts.append(deck.event_name)
    if deck.notes:
        note_parts.append(deck.notes)
    if not note_parts:
        return "-"
    note = " | ".join(note_parts).replace("\n", " ").strip()
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


def _pick_format(console: Console, provider: DeckProvider) -> MatchFormat | DeckSource | str | None:
    if provider.supported_formats == {MatchFormat.ANY}:
        return MatchFormat.ANY

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

        format_screen_sources = provider.format_screen_sources
        if format_screen_sources:
            creator_table = Table(show_header=True, header_style="bold magenta")
            creator_table.add_column("#", justify="right", style="bold")
            creator_table.add_column("Creator")
            for idx, source in enumerate(format_screen_sources, start=4):
                creator_table.add_row(str(idx), source.name.removeprefix("Creator: ").strip() or source.name)
            console.print()
            console.print(creator_table)

        raw = Prompt.ask(
            "\n[bold cyan]Select format or creator (or b to go back, q to quit)[/bold cyan]"
        )
        if raw.lower() == "q":
            return "q"
        if raw.lower() == "b":
            return None
        if raw == "1":
            return MatchFormat.ANY
        if raw == "2":
            return MatchFormat.BO1
        if raw == "3":
            return MatchFormat.BO3
        if raw.isdigit() and format_screen_sources:
            selection = int(raw)
            creator_index = selection - 4
            if 0 <= creator_index < len(format_screen_sources):
                return format_screen_sources[creator_index]
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
            title=provider.source_picker_title,
            border_style="cyan",
        )
    )

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Name", style="bold")
    table.add_column("URL", overflow="fold")

    if not sources:
        console.print("[yellow]No source endpoints match that format.[/yellow]")
        return "b"

    for idx, source in enumerate(sources, start=1):
        table.add_row(str(idx), source.name, source.url)
    console.print(table)

    if len(sources) == 1:
        console.print(
            f"\n[dim]Only one {provider.source_picker_item_label} matches this filter. "
            "Using it automatically...[/dim]"
        )
        return sources[0]

    while True:
        options = [
            f"Select {provider.source_picker_item_label} #",
        ]
        if provider.allow_all_sources:
            options.append(f"a={provider.source_picker_all_label}")
        options.append("b=back")
        options.append("q=quit")
        raw = Prompt.ask(
            f"\n[bold cyan]{', '.join(options)}[/bold cyan]",
            default="a" if provider.allow_all_sources else "b",
            show_choices=False,
        ).strip()
        lowered = raw.lower()
        if lowered == "q":
            return "q"
        if lowered == "b":
            return "b"
        if lowered == "a" and provider.allow_all_sources:
            return None
        if raw.isdigit():
            selection = int(raw)
            if 1 <= selection <= len(sources):
                return sources[selection - 1]
        valid_choices = "a, b, or q" if provider.allow_all_sources else "b or q"
        console.print(
            f"[yellow]Invalid selection. Enter a number, {valid_choices}.[/yellow]"
        )
