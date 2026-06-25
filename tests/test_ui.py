from __future__ import annotations

import unittest

from mtga_deck_downloader.models import DeckSource, MatchFormat
from mtga_deck_downloader.ui import _split_creator_sources


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


if __name__ == "__main__":
    unittest.main()
