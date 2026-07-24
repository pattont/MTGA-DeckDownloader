# AGENTS.md

Instructions for coding agents working in this repository. These rules apply to
the entire repository unless a more specific `AGENTS.md` is added below a
subdirectory.

## Project Summary

MTGA Deck Downloader is a Python 3.10+ Rich console application that collects
public Magic: The Gathering Arena decklists from several sites and converts
them into Arena import text. It uses a source-layout package under `src/` and is
packaged for Windows and macOS.

Read these files before broad changes:

- `README.md` for user-visible behavior and controls.
- `DEVELOPMENT.md` for contributor setup and provider conventions.
- `docs/architecture.md` for module boundaries and runtime flow.
- `docs/releasing.md` for installer and release work.

## Commands

Use the repository virtual environment when it exists:

```bash
.venv/bin/python app.py
.venv/bin/python -m unittest discover
.venv/bin/mtga-deck-downloader --diagnose
```

Run a focused test while iterating, then run the full suite before finishing:

```bash
.venv/bin/python -m unittest tests.test_ui
.venv/bin/python -m unittest tests.test_untapped_scraper
.venv/bin/python -m unittest discover
git diff --check
```

CI installs the package with `python -m pip install -e .`, runs the full
`unittest` suite, and runs the offline `--diagnose` command on Python 3.12.
Keep the declared Python 3.10 minimum compatible even if local Python is newer.

## Ownership Boundaries

- `app.py`: direct-repository launcher only.
- `src/mtga_deck_downloader/__main__.py`: CLI flags and offline diagnostics.
- `src/mtga_deck_downloader/ui.py`: Rich rendering, prompts, navigation,
  pagination, clipboard behavior, and detail flow.
- `src/mtga_deck_downloader/providers/`: thin adapters from app choices to a
  site's scraper, plus provider-specific labels and flow configuration.
- `src/mtga_deck_downloader/scrapers/`: HTTP, HTML/JSON parsing, endpoint
  contracts, sorting, deck export extraction, and deckstring decoding.
- `src/mtga_deck_downloader/models.py`: shared data passed between layers.
- `src/mtga_deck_downloader/config.py`: config discovery, parsing, defaults,
  aliases, and deduplication.
- `packaging/`: PyInstaller payload and platform installer logic.

Keep HTTP and site-markup knowledge out of providers and UI. Keep terminal
rendering and prompt logic out of scrapers.

## Provider Contract

All providers subclass `DeckProvider` and export `PROVIDER_CLASS`. Provider
modules are loaded dynamically; an import-time exception can remove a site from
the application.

Preserve these behaviors:

- `sources` describes selectable feeds with accurate `MatchFormat` support.
- `fetch_decks(..., source=None)` has an intentional and tested meaning.
- `uses_source_picker=False` means format selection proceeds directly to data.
- `format_screen_sources` is for creator rows shown beside format choices.
- `fetch_deck_variants(...)` supports intermediate rows such as archetypes and
  events. Return no variants for rows that should open deck details directly.
- `hydrate_deck(...)` performs expensive deck-text work only when details open.
- `result_view_config(...)` customizes labels and notes without adding provider
  branches throughout the browsing loop.

List screens should return `DeckEntry(deck_text=None)` when deck text is costly.
Use a stable, canonical `source_url`, sort results explicitly, and respect the
requested limit.

## Scraper Rules

External HTML and undocumented APIs change frequently. Treat each parsed field
as a contract that needs a focused regression test.

- Use the shared session and decoding helpers in `scrapers/common.py`.
- Use JSON and HTML parsers instead of regex or string slicing when structured
  data is available.
- Set request timeouts and raise `ScrapeError` for missing required payloads.
- Return `None` for optional Arena import text that cannot be extracted.
- Do not silently invent win rates, dates, formats, event names, or player data.
- Aggregate and sort using source timestamps or ordering rules, not incidental
  dictionary or DOM order.
- Avoid authenticated/private endpoints, credentials, and browser session data.
- Do not add live-network calls to the test suite.

When a live source breaks, reproduce it manually, save only the smallest useful
payload shape in a fake response, write the failing test, then patch the parser.

## Terminal UI Invariants

All screens must remain usable without scrolling back to find the prompt.

- Every interactive prompt has a meaningful default.
- `q` quits, `s` returns to site selection, `f` changes the provider filter,
  and `b` goes back one nested screen.
- Numbered rows perform the action named in the prompt.
- Deck and variant lists are paged at `DECK_PAGE_SIZE` (currently 20).
- Pagination uses global row numbers and only accepts numbers visible on the
  current page. `n` and `p` appear only when valid.
- Use the full result set when determining columns so columns do not shift
  between pages.
- Clear the screen before rendering a replacement full-screen view.
- Keep prompt wording, panel context, table labels, and accepted keys aligned.
- Add UI tests for changed defaults, navigation, pagination, or column rules.

Current presentation contracts are deliberate:

- Aetherhub creator rows show tags without repeating the creator name; posted
  dates use a separate column.
- Magic.gg hides `Event/Notes`, shows dates separately, and labels Traditional
  Standard as `Standard (Bo3)`.
- Moxfield uses `Updated` and does not repeat the creator name.
- TCGPlayer hides `Player` and `Event/Notes`; creator dates use `Created`.
- Untapped archetypes show variant counts; variant rows hide notes.

Do not add a generic column globally to solve one provider's data problem. Use
provider configuration or the existing UI helpers.

## Configuration

Configuration resolution order is explicit path, the
`MTGA_DECK_DOWNLOADER_CONFIG` environment variable, the installed user's config,
the repository `config.json`, then bundled `default_config.json`.

- Creator entries may be strings or objects with `Name` and `ShortName` aliases.
- Preserve case-insensitive deduplication.
- `AtherhubCreators` is intentionally misspelled for compatibility. Do not
  rename it without a migration and tests.
- When changing bundled defaults, keep root `config.json` and
  `src/mtga_deck_downloader/default_config.json` intentionally synchronized.
- Config parser changes require `tests/test_config.py` coverage and diagnostic
  updates when counts or categories change.

## Tests

Use standard-library `unittest`. Match test scope to the layer being changed:

- scraper tests: fake sessions and representative HTML/JSON payloads;
- provider tests: sources, filtering, labels, and delegation;
- UI tests: rendered output, menu defaults, navigation, and table decisions;
- config tests: path precedence, aliases, invalid input, and deduplication;
- CLI tests: offline provider discovery and packaged-resource diagnostics.

Tests must be deterministic and offline. Do not weaken an assertion merely
because a live site changed; update the fixture and implementation to describe
the new verified contract.

## Packaging And Documentation

Runtime files must work from source, an editable install, and a frozen
PyInstaller build. Do not assume the process working directory is the repository
root. If adding package data, update `pyproject.toml` and the PyInstaller payload
as needed.

The `Build installers` GitHub Actions workflow produces three self-contained
artifacts: Windows x64, macOS Apple Silicon, and macOS Intel. Unsigned installers
are the supported default and must build without signing secrets. Signing and
notarization remain optional, secret-gated enhancements.

Preserve these release behaviors:

- Manual workflow runs upload each installer with a portable SHA-256 manifest.
- A matching `v*` tag creates a draft release only after every platform passes.
- Draft releases clearly disclose that installers are unsigned.
- macOS DMG creation retries transient `hdiutil` failures without hiding a
  persistent failure.
- Installer filenames, checksum entries, `pyproject.toml`, and the requested
  release version remain consistent.

Update user documentation when behavior changes:

- `README.md`: sources, configuration, controls, and known limitations.
- `DEVELOPMENT.md`: contributor workflow and coding conventions.
- `docs/architecture.md`: ownership boundaries or runtime flow.
- `docs/releasing.md`: packaging, signing, or release process.

Version changes must keep `pyproject.toml`, release tags, and installer inputs
consistent.

## Completion Checklist

Before handing off a change:

1. Inspect `git diff` and preserve unrelated user changes.
2. Run focused tests for the changed behavior.
3. Run `.venv/bin/python -m unittest discover`.
4. Run `.venv/bin/mtga-deck-downloader --diagnose` for provider, config, CLI,
   package-data, or packaging changes.
5. For packaging changes, validate applicable shell/workflow syntax and build
   the local platform artifact when practical.
6. Run `git diff --check`.
7. Report any test, live-source, platform, or packaging verification that could
   not be performed.
