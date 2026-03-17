# MTGA Deck Downloader

Console app for finding playable Magic The Gathering Arena decklists from multiple sources for import to MTG Arena.

## What It Does

- Loads providers dynamically (modular source architecture).
- Lets you choose site + format (`Bo1`, `Bo3`, or `Any`).
- Lets you optionally choose a specific source endpoint/tab when a site exposes multiple feeds.
- Shows ranked results in a Rich terminal UI.
- Opens deck details and displays Arena import text when available.
- Uses lazy deck-text loading for heavy sources so list and variant screens stay fast.

## Current Sources

### `magic.gg`

- Scrapes `https://magic.gg/decklists` and article decklist entries.
- Pulls event decklists, event metadata, and Arena deck text.
- Attempts to detect format from event/article context.

### `mtga.untapped.gg`

- Uses Untapped public endpoints for archetype + meta data.
- Falls back to API deck rows if archetype page variant rows are empty.
- Decodes Untapped deckstrings into Arena import text in-app.

Untapped flow in UI:

1. Select an archetype from the results table.
2. Select one of that archetype's variant decks.
3. View details and copy the Arena text.

### `aetherhub.com`

- Scrapes all requested Standard tabs:
  - Tournament: `https://aetherhub.com/Events/Standard/`
  - Tournament Meta: `https://aetherhub.com/Metagame/Standard-Events/`
  - MTGA BO1 Meta: `https://aetherhub.com/Metagame/Standard-BO1/`
  - MTGA BO3 Meta: `https://aetherhub.com/Metagame/Standard-BO3/`
- Parses tournament event names and normalizes event dates to U.S. format (`MM/DD/YYYY`).
- Pulls direct Arena export text through Aetherhub's deck export endpoint.

## Requirements

- Python 3.10+
- Terminal that supports ANSI colors/controls (recommended for Rich UI)

Dependencies are listed in `requirements.txt`:

- `rich`
- `requests`
- `beautifulsoup4`
- `cloudscraper`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Usage Controls

Main results screen:

- Enter a number to drill into the selected item.
- `f` to change format.
- `s` to change site.
- `q` to quit.

Source endpoint screen (multi-feed sites):

- Enter endpoint number to fetch only that tab/feed.
- `a` to fetch all endpoints matching the selected format.
- `b` to go back to format selection.

Variant screen (Untapped):

- Enter a number for deck details.
- `b` to go back to archetypes.
- `f` / `s` / `q` as above.

## Project Layout

```text
app.py
mtga_deck_downloader/
  providers/
    aetherhub.py
    base.py
    magic_gg.py
    untapped.py
    registry.py
  scrapers/
    aetherhub.py
    magic_gg.py
    untapped.py
    untapped_deckstring.py
  ui.py
  models.py
```

## Add a New Source Provider

1. Create a new module in `mtga_deck_downloader/providers/`.
2. Subclass `DeckProvider`.
3. Implement:
   - `sources`
   - `fetch_decks(...)`
   - optionally `fetch_deck_variants(...)` for multi-step flows
4. Export `PROVIDER_CLASS = YourProviderClass`.
5. Restart the app (providers are auto-discovered by `registry.py`).

## Known Limitations

- Untapped Bo3 win-rate fields may be unavailable in public payloads.
- External site markup/API contracts can change and break scraping.
- Clipboard integration is not implemented yet (copy is manual from console).

## Next Steps

- Add clipboard copy support for deck text.
- Add refresh/pagination and optional rank/time-range filters.
- Add tests around parser and provider behavior.

---

This project is not affiliated with Wizards of the Coast.
