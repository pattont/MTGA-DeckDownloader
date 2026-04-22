# MTGA Deck Downloader

Console app for finding playable Magic The Gathering Arena decklists from multiple sources for import to MTG Arena.

## What It Does

- Loads providers dynamically (modular source architecture).
- Lets you choose site + format (`Bo1`, `Bo3`, or `Any`).
- Lets you optionally choose a specific source endpoint/tab/section when a site exposes multiple feeds.
- Shows ranked results in a Rich terminal UI.
- Opens deck details, auto-copies Arena import text to the clipboard when available, and shows the raw import text in the terminal.
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
- Supports creator deck feeds as source options, currently including:
  - `MTGMalone`: `https://aetherhub.com/User/MtgMalone/Decks`
- Parses tournament event names and normalizes event dates to U.S. format (`MM/DD/YYYY`).
- Pulls direct Arena export text through Aetherhub's deck export endpoint.
- Creator deck exports are prefixed with `About / Name ... (Creator)` for easier Arena import lookup.

### `moxfield.com`

- Loads creator profiles from `config.json` via the `MoxfieldNames` array.
- Uses Moxfield public APIs to fetch the first 15 public decks from each configured creator.
- Opens full deck text from the public deck API when you select a deck.

### `tcgplayer.com`

- Uses TCGPlayer content APIs for:
  - Trending Decks
  - Latest Decks
  - Events
- Event selections open a second result screen with top-finishing decks, including place and player name.
- Deck details hydrate from TCGPlayer's deck API and build Arena import text from the returned card map.

## Requirements

- Python 3.10+
- Terminal that supports ANSI colors/controls (recommended for Rich UI)

Dependencies are listed in `requirements.txt`:

- `rich`
- `requests`
- `beautifulsoup4`
- `cloudscraper`

## Config

The repo root contains `config.json`. Moxfield creator profiles are configured here:

```json
{
  "MoxfieldNames": [
    "Ashlizzlle",
    "Swayzemtg",
    "covertgoblue",
    "carlomtg"
  ]
}
```

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

- Enter endpoint/source number to fetch only that tab/feed/section.
- `a` to fetch all matching sources when that provider supports it.
- `b` to go back to format selection.

Variant screens:

- Untapped: pick an archetype, then a variant deck.
- TCGPlayer Events: pick an event, then a top deck.
- Enter a number for deck details on the second screen.
- `b` to go back to the previous list.
- `f` / `s` / `q` as above.

Deck details:

- If direct Arena text is available, it is copied to your clipboard automatically.
- Press `Enter` to go back to the previous list.
- Press `q` to quit.

## Project Layout

```text
app.py
src/
  mtga_deck_downloader/
    providers/
      aetherhub.py
      base.py
      magic_gg.py
      moxfield.py
      tcgplayer.py
      untapped.py
      registry.py
    scrapers/
      aetherhub.py
      magic_gg.py
      moxfield.py
      tcgplayer.py
      untapped.py
      untapped_deckstring.py
    config.py
    ui.py
    models.py
```

## Add a New Source Provider

1. Create a new module in `src/mtga_deck_downloader/providers/`.
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
- TCGPlayer event deck resolution relies on event-name search plus deck-detail verification because the public event API does not expose the top-deck list directly.

## Next Steps

- Add refresh/pagination and optional rank/time-range filters.
- Add tests around parser and provider behavior.
- Add more config-driven sources beyond Moxfield.

---

This project is not affiliated with Wizards of the Coast.
