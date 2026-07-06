# Development Guide

This project is a Python console app with a source-layout package in `src/`.
Use the repo virtualenv for local development because system Python may not have
the scraper and Rich UI dependencies installed.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Run tests:

```bash
.venv/bin/python -m unittest discover
```

For one-off scripts that import the package without installing it, set
`PYTHONPATH=src`:

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from mtga_deck_downloader.providers.registry import load_providers
print([provider.display_name for provider in load_providers()])
PY
```

## Project Boundaries

- `app.py` only prepares `sys.path` and starts the Rich terminal UI.
- `src/mtga_deck_downloader/ui.py` owns terminal navigation, prompts, tables,
  clipboard copying, and deck hydration flow.
- `src/mtga_deck_downloader/providers/` adapts each site into the common
  provider contract.
- `src/mtga_deck_downloader/scrapers/` owns site-specific HTTP calls, parsing,
  and export/deck-text extraction.
- `src/mtga_deck_downloader/models.py` contains shared data shapes.
- `src/mtga_deck_downloader/config.py` reads creator configuration from
  `config.json`.

Keep provider code thin. If a change needs HTTP, HTML, JSON, or endpoint-specific
rules, put it in the scraper and expose it through the provider.

## Adding a Provider

1. Add a scraper under `src/mtga_deck_downloader/scrapers/`.
2. Add a provider under `src/mtga_deck_downloader/providers/`.
3. Subclass `DeckProvider` and implement:
   - `sources`
   - `fetch_decks(...)`
   - `hydrate_deck(...)` when deck text is lazy-loaded
   - `fetch_deck_variants(...)` for two-step flows
4. Export `PROVIDER_CLASS = YourProviderClass`.
5. Add tests for scraper parsing and provider behavior.
6. Run `.venv/bin/python -m unittest discover`.

Provider modules are discovered dynamically by
`mtga_deck_downloader.providers.registry.load_providers()`.

## UI Menu Conventions

- `q` always quits.
- `s` returns to site selection from result screens.
- `f` changes the current provider-specific filter. The prompt label should be
  provider-specific: format, creator, or section.
- `b` goes back one screen where a nested picker or variant list exists.
- `Enter` returns from deck details to the previous list.
- Numbered rows drill into the selected row.

When adding a new screen, keep prompt wording aligned with these controls and
add focused tests for helper behavior.

## Testing Scrapers

Prefer fake sessions and small fixture payloads over live network tests. Live
sites change often, and regression tests should isolate the parser or endpoint
contract that the code depends on.

When fixing a live-site breakage:

1. Reproduce the failure with the affected URL or payload.
2. Identify the site contract that changed.
3. Add a small failing test around that contract.
4. Patch the scraper or provider.
5. Run the focused test and the full suite.

## Configuration

`config.json` supports creator lists for Moxfield, Aetherhub, and TCGPlayer.
Entries can be strings or objects with `Name` and optional `ShortName`.

The Aetherhub key is currently spelled `AtherhubCreators` for compatibility with
the existing config file. Keep that spelling unless a migration path is added.

## Packaging

Installer planning lives in `docs/future_installer.md`. Do not add release
automation piecemeal; keep packaging changes tied to that plan so Windows and
macOS stay aligned.
