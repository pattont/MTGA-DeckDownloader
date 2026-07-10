from __future__ import annotations

import unittest

from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
from mtga_deck_downloader.ui import (
    _date_column_label,
    _notes_column_label,
    _show_player_column,
    _show_notes_column,
    _show_posted_date_column,
    _source_context_label,
    _split_creator_sources,
    _table_note,
)


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

    def test_table_note_shows_only_tags_for_aetherhub_creator_source(self) -> None:
        creator_source = DeckSource(
            name="Creator: ManaMan",
            url="https://aetherhub.com/User/ManaMan/Decks",
            description="Creator decks",
            formats=(MatchFormat.BO1, MatchFormat.BO3),
        )
        deck = DeckEntry(
            name="Big Boros Burn",
            source_site="aetherhub.com",
            source_url="https://aetherhub.com/Deck/big-boros-burn",
            format_label="Standard / Bo3",
            notes="Creator: ManaMan | Tags: Control | Exports: 20 | Views: 76",
        )

        self.assertEqual(
            _table_note(deck, truncate=False, selected_source=creator_source),
            "Control",
        )

    def test_posted_date_column_is_only_shown_for_aetherhub_rows_with_dates(self) -> None:
        class AetherhubProvider:
            key = "aetherhub"

        class MoxfieldProvider:
            key = "moxfield"

        dated_deck = DeckEntry(
            name="Big Boros Burn",
            source_site="aetherhub.com",
            source_url="https://aetherhub.com/Deck/big-boros-burn",
            format_label="Standard / Bo3",
            event_date="07/09/2026",
        )
        undated_deck = DeckEntry(
            name="Boros Burn",
            source_site="aetherhub.com",
            source_url="https://aetherhub.com/Deck/boros-burn",
            format_label="Standard / Bo3",
        )

        self.assertTrue(_show_posted_date_column(AetherhubProvider(), [dated_deck]))
        self.assertFalse(_show_posted_date_column(AetherhubProvider(), [undated_deck]))
        self.assertFalse(_show_posted_date_column(MoxfieldProvider(), [dated_deck]))

    def test_tcgplayer_hides_player_column_and_uses_created_date_column(self) -> None:
        class TCGPlayerProvider:
            key = "tcgplayer"

        creator_source = DeckSource(
            name="Creator: Arne Huschenbeth",
            url="https://www.tcgplayer.com/content/author/Arne%20Huschenbeth/",
            description="Creator decks",
            formats=(MatchFormat.ANY,),
        )
        deck = DeckEntry(
            name="Jeskai Lessons",
            source_site="tcgplayer.com",
            source_url="https://www.tcgplayer.com/magic-the-gathering/deck/Jeskai-Lessons/546993",
            format_label="Standard",
            player_name="Arne Huschenbeth",
            event_date="06/12/2026",
            notes="Created: 06/12/2026 | Creator: Arne Huschenbeth",
        )

        self.assertFalse(_show_player_column(TCGPlayerProvider(), [deck]))
        self.assertFalse(_show_notes_column(TCGPlayerProvider()))
        self.assertEqual(_date_column_label(TCGPlayerProvider(), creator_source, [deck]), "Created")
        self.assertEqual(
            _table_note(deck, truncate=False, selected_source=creator_source),
            "-",
        )

        event_deck = DeckEntry(
            name="Regional Championship",
            source_site="tcgplayer.com",
            source_url="https://www.tcgplayer.com/content/magic-the-gathering/decks/event/regional-championship",
            format_label="Standard",
            event_date="06/12/2026",
            notes="128 players",
        )
        self.assertIsNone(_date_column_label(TCGPlayerProvider(), None, [event_deck]))

    def test_moxfield_uses_updated_notes_column_without_creator_text(self) -> None:
        class MoxfieldProvider:
            key = "moxfield"

        deck = DeckEntry(
            name="Orzhov Offense Lifegain",
            source_site="moxfield.com",
            source_url="https://moxfield.com/decks/pjrbWDUR40CUnVEiZnrBPA",
            format_label="Standard",
            event_date="05/16/2026",
            notes="Creator: Ashlizzlle | Updated: 05/16/2026",
        )

        self.assertEqual(_notes_column_label(MoxfieldProvider()), "Updated")
        self.assertTrue(_show_notes_column(MoxfieldProvider()))
        self.assertIsNone(_date_column_label(MoxfieldProvider(), None, [deck]))
        self.assertEqual(_table_note(deck, truncate=False), "05/16/2026")


if __name__ == "__main__":
    unittest.main()
