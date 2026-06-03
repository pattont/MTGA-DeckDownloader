from __future__ import annotations

import unittest

from mtga_deck_downloader.config import AppConfig, CreatorConfig
from mtga_deck_downloader.models import DeckEntry, MatchFormat
from mtga_deck_downloader.providers import aetherhub as provider_module
from mtga_deck_downloader.providers.aetherhub import AetherhubProvider


class FakeScraper:
    def fetch_creator_decks(
        self,
        user_url: str,
        selected_format: MatchFormat,
        limit: int = 50,
        creator_label: str | None = None,
    ) -> list[DeckEntry]:
        return [
            DeckEntry(
                name="Boros Mouse Offense",
                source_site="aetherhub.com",
                source_url=user_url,
                format_label=selected_format.label,
                notes=f"Creator: {creator_label}",
            )
        ]

    def fetch_deck_text(self, source_url: str) -> str | None:
        return "Deck\n4 Heartfire Hero"


class AetherhubProviderTests(unittest.TestCase):
    def test_creator_sources_and_import_names_use_configured_short_names(self) -> None:
        original_load_config = provider_module.load_config
        provider_module.load_config = lambda: AppConfig(
            moxfield_creators=(),
            aetherhub_creators=(CreatorConfig(name="MTGMalone", short_name="Malone"),),
        )
        provider = AetherhubProvider.__new__(AetherhubProvider)
        provider._scraper = FakeScraper()
        try:
            creator_sources = [source for source in provider.sources if source.name.startswith("Creator: ")]
            decks = provider.fetch_decks(MatchFormat.BO1, limit=1, source=creator_sources[0])
            hydrated = provider.hydrate_deck(decks[0])
        finally:
            provider_module.load_config = original_load_config

        self.assertEqual(creator_sources[0].name, "Creator: MTGMalone")
        self.assertEqual(creator_sources[0].url, "https://aetherhub.com/User/MTGMalone/Decks")
        self.assertEqual(decks[0].name, "Boros Mouse Offense")
        self.assertEqual(
            hydrated.deck_text,
            "About\nName Boros Mouse Offense (Malone)\n\nDeck\n4 Heartfire Hero",
        )


if __name__ == "__main__":
    unittest.main()
