from dataclasses import replace

from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider
from mtga_deck_downloader.scrapers.aetherhub import AetherhubScraper


class AetherhubProvider(DeckProvider):
    key = "aetherhub"
    display_name = "aetherhub.com"
    description = "Tournament and MTGA metagame decks with direct MTGA export text."
    homepage = "https://aetherhub.com/Metagame/Standard-Events/"

    def __init__(self) -> None:
        self._scraper = AetherhubScraper()

    @property
    def sources(self) -> list[DeckSource]:
        return [
            DeckSource(
                name="Tournament",
                url="https://aetherhub.com/Events/Standard/",
                description="Latest Standard tournament deck placements.",
                formats=(MatchFormat.BO3,),
            ),
            DeckSource(
                name="Tournament Meta",
                url="https://aetherhub.com/Metagame/Standard-Events/",
                description="Top-performing Standard tournament archetypes.",
                formats=(MatchFormat.BO3,),
            ),
            DeckSource(
                name="MTGA BO1 Meta",
                url="https://aetherhub.com/Metagame/Standard-BO1/",
                description="Arena Standard Best-of-1 metagame.",
                formats=(MatchFormat.BO1,),
            ),
            DeckSource(
                name="MTGA BO3 Meta",
                url="https://aetherhub.com/Metagame/Standard-BO3/",
                description="Arena Standard Best-of-3 metagame.",
                formats=(MatchFormat.BO3,),
            ),
        ]

    def fetch_decks(
        self,
        selected_format: MatchFormat,
        limit: int = 50,
        source: DeckSource | None = None,
    ) -> list[DeckEntry]:
        source_urls = {source.url} if source is not None else None
        return self._scraper.fetch_decks(
            selected_format=selected_format,
            limit=limit,
            source_urls=source_urls,
        )

    def hydrate_deck(self, deck: DeckEntry) -> DeckEntry:
        if deck.source_site != "aetherhub.com" or deck.deck_text:
            return deck
        deck_text = self._scraper.fetch_deck_text(deck.source_url)
        if deck_text is None:
            return deck
        return replace(deck, deck_text=deck_text)


PROVIDER_CLASS = AetherhubProvider
