from __future__ import annotations

import unittest

import mtga_deck_downloader.ui as ui_module
from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
from mtga_deck_downloader.ui import (
    _date_column_label,
    _notes_column_label,
    _pick_format,
    _pick_provider,
    _show_player_column,
    _show_notes_column,
    _show_posted_date_column,
    _source_context_label,
    _split_creator_sources,
    _table_note,
)


class FakeConsole:
    is_terminal = False

    def clear(self) -> None:
        return None

    def print(self, *args: object, **kwargs: object) -> None:
        return None


class UISourceTests(unittest.TestCase):
    def test_top_level_menu_has_quit_default(self) -> None:
        class FakeProvider:
            display_name = "Example"
            description = "Example decks"

        calls: list[dict[str, object]] = []
        original_ask = ui_module.Prompt.ask

        def fake_ask(prompt: str, **kwargs: object) -> str:
            calls.append(kwargs)
            return str(kwargs["default"])

        ui_module.Prompt.ask = fake_ask
        try:
            selected = _pick_provider(FakeConsole(), [FakeProvider()])
        finally:
            ui_module.Prompt.ask = original_ask

        self.assertIsNone(selected)
        self.assertEqual(calls[0]["default"], "q")
        self.assertFalse(calls[0]["show_choices"])

    def test_format_menu_defaults_to_back(self) -> None:
        class FakeProvider:
            display_name = "untapped.gg"
            description = "Arena archetypes"
            homepage = "https://mtga.untapped.gg/constructed/standard/meta"
            supported_formats = {MatchFormat.ANY, MatchFormat.BO1, MatchFormat.BO3}
            format_screen_sources: list[DeckSource] = []

        calls: list[dict[str, object]] = []
        original_ask = ui_module.Prompt.ask

        def fake_ask(prompt: str, **kwargs: object) -> str:
            calls.append(kwargs)
            return str(kwargs["default"])

        ui_module.Prompt.ask = fake_ask
        try:
            selected = _pick_format(FakeConsole(), FakeProvider())
        finally:
            ui_module.Prompt.ask = original_ask

        self.assertIsNone(selected)
        self.assertEqual(calls[0]["default"], "b")
        self.assertFalse(calls[0]["show_choices"])

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

    def test_magic_gg_ranked_decklists_use_date_column_and_hide_ranked_title(self) -> None:
        class MagicGGProvider:
            key = "magic_gg"

        deck = DeckEntry(
            name="Patchwork Beastie + Rapid Rescue",
            source_site="magic.gg",
            source_url="https://magic.gg/decklists/traditional-standard-ranked-decklists-july-6-2026",
            format_label="Standard (Bo3)",
            event_name="Traditional Standard Ranked Decklists: July 6, 2026",
            event_date="July 6, 2026",
            notes="Traditional (Bo3)",
        )

        self.assertFalse(_show_notes_column(MagicGGProvider()))
        self.assertEqual(_date_column_label(MagicGGProvider(), None, [deck]), "Date")
        self.assertEqual(_table_note(deck, truncate=False), "-")


if __name__ == "__main__":
    unittest.main()
