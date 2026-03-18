from __future__ import annotations

from dataclasses import replace

from mtga_deck_downloader.config import load_config
from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider
from mtga_deck_downloader.scrapers.moxfield import MoxfieldScraper


class MoxfieldProvider(DeckProvider):
    key = "moxfield"
    display_name = "moxfield.com"
    description = "Config-driven creator decks from public Moxfield profiles."
    homepage = "https://moxfield.com/"

    def __init__(self) -> None:
        self._scraper = MoxfieldScraper()

    @property
    def sources(self) -> list[DeckSource]:
        config = load_config()
        return [
            DeckSource(
                name=username,
                url=f"https://moxfield.com/users/{username}",
                description="First 15 public decks from this creator's All Decks list.",
                formats=(MatchFormat.ANY,),
            )
            for username in config.moxfield_names
        ]

    def fetch_decks(
        self,
        selected_format: MatchFormat,
        limit: int = 50,
        source: DeckSource | None = None,
    ) -> list[DeckEntry]:
        sources = [source] if source is not None else self.sources
        decks: list[DeckEntry] = []
        for item in sources:
            decks.extend(self._scraper.fetch_user_decks(item.name, limit=min(limit, 15)))
            if len(decks) >= limit:
                break
        return decks[:limit]

    def hydrate_deck(self, deck: DeckEntry) -> DeckEntry:
        if deck.source_site != "moxfield.com" or deck.deck_text:
            return deck
        deck_text = self._scraper.fetch_deck_text(deck.source_url)
        if deck_text is None:
            return deck
        return replace(deck, deck_text=deck_text)


PROVIDER_CLASS = MoxfieldProvider
