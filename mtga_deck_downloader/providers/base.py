from __future__ import annotations

from abc import ABC

from mtga_deck_downloader.models import DeckSource, MatchFormat


class DeckProvider(ABC):
    key: str
    display_name: str
    description: str
    homepage: str

    def list_sources(self, selected_format: MatchFormat) -> list[DeckSource]:
        return [source for source in self.sources if source.supports(selected_format)]

    @property
    def sources(self) -> list[DeckSource]:
        raise NotImplementedError("Providers must expose sources.")

    @property
    def supported_formats(self) -> set[MatchFormat]:
        formats: set[MatchFormat] = set()
        for source in self.sources:
            formats.update(source.formats)
        return formats
