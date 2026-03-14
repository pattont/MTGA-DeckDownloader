from mtga_deck_downloader.models import DeckSource, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider


class MagicGGProvider(DeckProvider):
    key = "magic_gg"
    display_name = "magic.gg"
    description = "Decklists from premier events and pro-level tournaments."
    homepage = "https://magic.gg/decklists"

    @property
    def sources(self) -> list[DeckSource]:
        return [
            DeckSource(
                name="Event Decklists",
                url="https://magic.gg/decklists",
                description="Official decklists with event results and standings.",
                formats=(MatchFormat.BO1, MatchFormat.BO3),
            )
        ]


PROVIDER_CLASS = MagicGGProvider
