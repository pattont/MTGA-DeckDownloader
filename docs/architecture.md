# Architecture

MTGA Deck Downloader is organized around a small provider contract. The terminal
UI only knows how to ask providers for sources, decks, variants, and hydrated
deck text. Each provider hides the details of its website behind that contract.

## Runtime Flow

```text
app.py
  -> run_app()
    -> load_providers()
    -> pick site
    -> pick format/source/creator/section
    -> provider.fetch_decks(...)
    -> browse result rows
    -> provider.fetch_deck_variants(...) when the row is a parent item
    -> provider.hydrate_deck(...) when deck text is needed
    -> copy/display Arena import text
```

## Core Modules

`app.py` is the executable entry point. It adds `src/` to `sys.path` for direct
repo execution and then calls `run_app()`.

`ui.py` owns terminal interaction. It renders Rich panels and tables, handles
navigation keys, clears screens, lazy-loads deck details, and copies MTGA import
text to the clipboard.

`providers/base.py` defines the `DeckProvider` contract and `ResultViewConfig`.
Providers can customize source picker labels, result table labels, and whether
all sources can be fetched together.

`providers/registry.py` dynamically imports provider modules and instantiates
classes exported as `PROVIDER_CLASS`.

`models.py` defines the shared `MatchFormat`, `DeckSource`, and `DeckEntry`
objects that move through the app.

`config.py` reads creator configuration from `config.json`, normalizes strings
and object entries, and deduplicates creators case-insensitively.

## Provider And Scraper Responsibilities

Providers translate app-level choices into site-specific scraper calls. They
also add app-specific behavior such as creator import names, provider labels,
variant support, and source filtering.

Scrapers handle external contracts: HTTP sessions, endpoint parameters, HTML
parsing, JSON parsing, deck id extraction, and Arena export text construction.
They should not know about terminal navigation.

Keep this split intact:

- If the change is about how a website is fetched or parsed, change a scraper.
- If the change is about how a site appears in the app, change a provider.
- If the change is about shared navigation, prompts, or output, change `ui.py`.

## Current Providers

`magic_gg` scrapes Magic.gg decklist pages and article decklist content.

`untapped` uses Untapped public data for archetypes and variant decklists. Its
main result rows are archetypes, and variants are loaded as a second step.

`aetherhub` combines tournament/meta feeds and configured creator feeds. Deck
text is lazy-loaded from Aetherhub export endpoints when a user opens details.

`moxfield` reads configured creator profiles and lazy-loads full deck text from
Moxfield public APIs.

`tcgplayer` supports trending decks, latest decks, events, and configured
creator feeds. Event rows drill into top-deck rows before deck detail hydration.

## Data Flow

`DeckSource` represents a selectable feed, tab, creator, or section. Providers
choose the wording through `source_picker_item_label`, so UI text can say
endpoint, creator, or section accurately.

`DeckEntry` represents both real decks and intermediate rows such as Untapped
archetypes or TCGPlayer events. Providers signal the next step by returning
variants from `fetch_deck_variants(...)`; otherwise the UI opens deck details.

`deck_text` may be `None` on list screens. The UI calls `hydrate_deck(...)` only
when the user opens a detail screen, keeping list browsing fast.

## Error Handling

Provider loading errors are collected in `LAST_PROVIDER_ERRORS` and displayed
when no providers can load.

Fetch failures are caught in the UI and shown without crashing the app. The user
can continue or quit.

Scrapers should raise `ScrapeError` when a required page shape or payload is
missing. Optional deck text extraction should return `None` when a source cannot
provide import text.

## Test Strategy

Tests should focus on stable contracts:

- config parsing and deduplication
- provider source lists and import-name behavior
- scraper parsing with fake sessions or fixture payloads
- UI helper behavior for labels and source grouping
- random-deck selection logic

Avoid live network tests in the main suite. Use live URLs manually to reproduce
site breakage, then encode the observed contract in a fake response test.
