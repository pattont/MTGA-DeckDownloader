from dataclasses import replace

from mtga_deck_downloader.models import DeckEntry, DeckSource, MatchFormat
from mtga_deck_downloader.providers.base import DeckProvider
from mtga_deck_downloader.scrapers.aetherhub import AetherhubScraper


class AetherhubProvider(DeckProvider):
    key = "aetherhub"
    display_name = "aetherhub.com"
    description = "Tournament and MTGA metagame decks with direct MTGA export text."
    homepage = "https://aetherhub.com/Metagame/Standard-Events/"
    CREATOR_SOURCES = (
        ("MTGMalone", "MtgMalone"),
    )

    def __init__(self) -> None:
        self._scraper = AetherhubScraper()

    @property
    def format_screen_sources(self) -> list[DeckSource]:
        return [source for source in self.sources if source.name.startswith("Creator: ")]

    @property
    def sources(self) -> list[DeckSource]:
        sources = [
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
        for label, username in self.CREATOR_SOURCES:
            sources.append(
                DeckSource(
                    name=f"Creator: {label}",
                    url=f"https://aetherhub.com/User/{username}/Decks",
                    description=f"Latest creator decks from {label}.",
                    formats=(MatchFormat.BO1, MatchFormat.BO3),
                )
            )
        return sources

    def fetch_decks(
        self,
        selected_format: MatchFormat,
        limit: int = 50,
        source: DeckSource | None = None,
    ) -> list[DeckEntry]:
        if source is not None and "/User/" in source.url and "/Decks" in source.url:
            return self._scraper.fetch_creator_decks(
                source.url,
                selected_format=selected_format,
                limit=limit,
                creator_label=source.name.removeprefix("Creator:").strip(),
            )

        if source is None:
            decks = self._scraper.fetch_decks(
                selected_format=selected_format,
                limit=limit,
                source_urls=None,
            )
            remaining = limit - len(decks)
            if remaining <= 0:
                return decks[:limit]
            for creator_source in self.sources:
                if remaining <= 0:
                    break
                if "/User/" not in creator_source.url or not creator_source.supports(selected_format):
                    continue
                creator_decks = self._scraper.fetch_creator_decks(
                    creator_source.url,
                    selected_format=selected_format,
                    limit=remaining,
                    creator_label=creator_source.name.removeprefix("Creator:").strip(),
                )
                seen_urls = {deck.source_url for deck in decks}
                for deck in creator_decks:
                    if deck.source_url in seen_urls:
                        continue
                    decks.append(deck)
                    seen_urls.add(deck.source_url)
                    remaining -= 1
                    if remaining <= 0:
                        break
            return decks[:limit]

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
        creator_name = self._creator_name_from_notes(deck.notes)
        if creator_name:
            deck_text = f"About\nName {deck.name} ({creator_name})\n\n{deck_text}"
        return replace(deck, deck_text=deck_text)

    @staticmethod
    def _creator_name_from_notes(notes: str | None) -> str | None:
        if not notes:
            return None
        for part in notes.split("|"):
            cleaned = part.strip()
            if cleaned.startswith("Creator:"):
                name = cleaned.removeprefix("Creator:").strip()
                return name or None
        return None


PROVIDER_CLASS = AetherhubProvider
