from __future__ import annotations

import unittest

from mtga_deck_downloader.models import DeckSource, MatchFormat
from mtga_deck_downloader.ui import _source_context_label, _split_creator_sources


class UISourceTests(unittest.TestCase):
    def test_split_creator_sources_keeps_creators_in_trailing_group(self) -> None:
        latest = DeckSource(
            name="Latest Decks",
            url="https://example.test/latest",
            description="Latest",
            formats=(MatchFormat.ANY,),
        )
        creator = DeckSource(
            name="Creator: Arne Huschenbeth",
            url="https://example.test/arne",
            description="Creator",
            formats=(MatchFormat.ANY,),
        )
        events = DeckSource(
            name="Events",
            url="https://example.test/events",
            description="Events",
            formats=(MatchFormat.ANY,),
        )

        regular_sources, creator_sources = _split_creator_sources([latest, creator, events])

        self.assertEqual(regular_sources, [latest, events])
        self.assertEqual(creator_sources, [creator])

    def test_source_context_label_uses_provider_item_label(self) -> None:
        class FakeProvider:
            source_picker_item_label = "section"

        self.assertEqual(_source_context_label(FakeProvider()), "Section")


if __name__ == "__main__":
    unittest.main()
