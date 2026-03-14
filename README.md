# MTGA Deck Downloader

Python console app scaffold for finding MTG Arena decks from multiple websites.

## Current status

- Rich UI with a menu of deck source sites.
- Provider architecture for modular source additions.
- Format filtering (`Bo1`, `Bo3`, or `Any`) on source endpoints.
- Starter providers for:
  - `magic.gg`
  - `mtga.untapped.gg`

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Add a new site provider

1. Create a new file in `mtga_deck_downloader/providers/`.
2. Add a class that extends `DeckProvider`.
3. Expose `PROVIDER_CLASS = YourProviderClass` at the bottom of the file.
4. Restart the app; the provider is auto-discovered.

## Next implementation steps

- Add scraping/fetch logic per provider to list actual decks.
- Add deck selection and full decklist export to clipboard.
- Evaluate browser automation for dynamic pages (`Playwright` is usually a better Python choice than Puppeteer).
