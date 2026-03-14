from mtga_deck_downloader.models import DeckSource, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider


class UntappedProvider(DeckProvider):
    key = "untapped"
    display_name = "mtga.untapped.gg"
    description = "Arena meta decks with win-rate data."
    homepage = "https://mtga.untapped.gg/constructed/standard/meta"

    @property
    def sources(self) -> list[DeckSource]:
        return [
            DeckSource(
                name="Standard Meta (Bo1)",
                url="https://mtga.untapped.gg/constructed/standard/meta",
                description="Best of 1 Standard meta with win percentage.",
                formats=(MatchFormat.BO1,),
            ),
            DeckSource(
                name="Standard Meta (Bo3)",
                url="https://mtga.untapped.gg/constructed/standard/meta?wincon=bo3",
                description="Best of 3 Standard meta with win percentage.",
                formats=(MatchFormat.BO3,),
            ),
        ]


PROVIDER_CLASS = UntappedProvider
