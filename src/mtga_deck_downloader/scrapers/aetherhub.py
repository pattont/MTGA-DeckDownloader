from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from mtga_deck_downloader.models import DeckEntry, MatchFormat
from mtga_deck_downloader.scrapers.common import ScrapeError


class AetherhubScraper:
    BASE_URL = "https://aetherhub.com"
    TOURNAMENT_URL = "https://aetherhub.com/Events/Standard/"
    TOURNAMENT_META_URL = "https://aetherhub.com/Metagame/Standard-Events/"
    BO1_META_URL = "https://aetherhub.com/Metagame/Standard-BO1/"
    BO3_META_URL = "https://aetherhub.com/Metagame/Standard-BO3/"
    DATE_TOKEN_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
    DECK_ID_RE = re.compile(r"-(\d+)(?:[/?#]|$)")
    MATCHES_RE = re.compile(r"(\d+)\s+matches", flags=re.IGNORECASE)
    ENGLISH_LANG_ID = 0

    def __init__(self) -> None:
        try:
            import cloudscraper
        except ImportError as exc:
            raise ScrapeError(
                "Aetherhub scraping requires cloudscraper. Install dependencies from requirements.txt."
            ) from exc

        self._session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "mobile": False}
        )
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self._deck_text_cache: dict[str, str | None] = {}

    def fetch_decks(
        self,
        selected_format: MatchFormat,
        limit: int = 50,
        source_urls: set[str] | None = None,
    ) -> list[DeckEntry]:
        feeds = self._feeds_for_format(selected_format)
        if source_urls:
            feeds = [feed for feed in feeds if feed[0] in source_urls]
        if not feeds:
            return []

        results: list[DeckEntry] = []
        seen_urls: set[str] = set()
        per_feed_limit = max(1, limit // len(feeds)) if selected_format is MatchFormat.ANY else limit

        for idx, (url, format_label) in enumerate(feeds):
            remaining = limit - len(results)
            if remaining <= 0:
                break

            feed_limit = remaining
            if selected_format is MatchFormat.ANY:
                feed_limit = min(remaining, per_feed_limit)
                # Let the final feed use any remaining slots.
                if idx == len(feeds) - 1:
                    feed_limit = remaining

            html = self._get_text(url)
            if url == self.TOURNAMENT_URL:
                parsed = self._parse_tournament_page(html=html, limit=feed_limit)
            else:
                parsed = self._parse_meta_page(html=html, format_label=format_label, limit=feed_limit)

            for deck in parsed:
                if deck.source_url in seen_urls:
                    continue
                seen_urls.add(deck.source_url)
                results.append(deck)
                if len(results) >= limit:
                    break

        return results[:limit]

    def _feeds_for_format(self, selected_format: MatchFormat) -> list[tuple[str, str]]:
        if selected_format is MatchFormat.BO1:
            return [(self.BO1_META_URL, "Standard / Bo1")]
        if selected_format is MatchFormat.BO3:
            return [
                (self.TOURNAMENT_URL, "Standard / Bo3"),
                (self.TOURNAMENT_META_URL, "Standard / Bo3"),
                (self.BO3_META_URL, "Standard / Bo3"),
            ]
        return [
            (self.TOURNAMENT_URL, "Standard / Bo3"),
            (self.TOURNAMENT_META_URL, "Standard / Bo3"),
            (self.BO1_META_URL, "Standard / Bo1"),
            (self.BO3_META_URL, "Standard / Bo3"),
        ]

    def _get_text(self, url: str) -> str:
        response = self._session.get(url, timeout=40)
        response.raise_for_status()
        return response.text

    def _parse_tournament_page(self, html: str, limit: int) -> list[DeckEntry]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", id="metalist")
        if table is None:
            raise ScrapeError("Aetherhub tournament table was not found.")

        results: list[DeckEntry] = []
        event_name: str | None = None
        event_date: str | None = None
        event_note: str | None = None

        for row in table.find_all("tr"):
            if row.find("th"):
                event_name, event_date, event_note = self._parse_tournament_header(row)
                continue

            entry = self._parse_tournament_deck_row(
                row=row,
                event_name=event_name,
                event_date=event_date,
                event_note=event_note,
            )
            if entry is None:
                continue
            results.append(entry)
            if len(results) >= limit:
                break

        return results

    def _parse_tournament_header(self, row: Tag) -> tuple[str | None, str | None, str | None]:
        event_link = row.find("a", href=re.compile(r"^/Events/Standard/"))
        raw_name = ""
        if isinstance(event_link, Tag):
            raw_name = event_link.get_text(" ", strip=True)
        if not raw_name:
            first_cell = row.find("th")
            raw_name = first_cell.get_text(" ", strip=True) if isinstance(first_cell, Tag) else ""

        normalized_name, event_date = self._normalize_event_name(raw_name)
        small = row.find("small")
        note = small.get_text(" ", strip=True) if isinstance(small, Tag) else None
        if note:
            note = " ".join(note.split())

        return normalized_name, event_date, note

    def _parse_tournament_deck_row(
        self,
        row: Tag,
        event_name: str | None,
        event_date: str | None,
        event_note: str | None,
    ) -> DeckEntry | None:
        if "deckdata" not in (row.get("class") or []):
            return None

        relative_url = str(row.get("data-url") or "").strip()
        if not relative_url:
            link = row.find("a", href=re.compile(r"/Metagame/.+/Deck/"))
            if not isinstance(link, Tag):
                return None
            relative_url = str(link.get("href") or "").strip()
        if not relative_url:
            return None

        source_url = urljoin(self.BASE_URL, relative_url)
        deck_name = str(row.get("data-name") or "").strip()
        if not deck_name:
            title_link = row.find("td", class_=re.compile("ae-decktitle"))
            if isinstance(title_link, Tag):
                deck_name = title_link.get_text(" ", strip=True)
        if not deck_name:
            links = row.find_all("a", href=True)
            if len(links) >= 2:
                deck_name = links[1].get_text(" ", strip=True)
        if not deck_name:
            return None

        placement = str(row.get("data-place") or "").strip()
        player = str(row.get("data-player") or "").strip()
        notes = self._join_notes(
            [f"{placement} - {player}" if placement and player else placement or player, event_note]
        )

        return DeckEntry(
            name=deck_name,
            source_site="aetherhub.com",
            source_url=source_url,
            format_label="Standard / Bo3",
            event_name=event_name,
            event_date=event_date,
            deck_text=None,
            notes=notes,
        )

    def _parse_meta_page(self, html: str, format_label: str, limit: int) -> list[DeckEntry]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="metagame-table")
        if table is None:
            raise ScrapeError("Aetherhub metagame table was not found.")

        rows = table.find_all("tr", class_="ae-deck-row")
        results: list[DeckEntry] = []
        for row in rows:
            deck_title_cell = row.find("td", class_=re.compile(r"ae-decktitle"))
            deck_link: Tag | None = None
            if isinstance(deck_title_cell, Tag):
                link = deck_title_cell.find("a", href=re.compile(r"/Metagame/.+/Deck/"))
                if isinstance(link, Tag):
                    deck_link = link
            if deck_link is None:
                link = row.find("a", href=re.compile(r"/Metagame/.+/Deck/"))
                if isinstance(link, Tag):
                    deck_link = link
            if not isinstance(deck_link, Tag):
                continue

            deck_name = deck_link.get_text(" ", strip=True)
            if not deck_name:
                continue
            source_url = urljoin(self.BASE_URL, str(deck_link.get("href") or "").strip())

            matches_text = ""
            matches_cell = row.find("td", class_=re.compile(r"ae-deckmatches"))
            if isinstance(matches_cell, Tag):
                matches_text = matches_cell.get_text(" ", strip=True)
            matches = self._extract_matches(matches_text)

            meta_row = row.find_next_sibling("tr")
            metagame_share = None
            change_note = None
            if isinstance(meta_row, Tag):
                share_span = meta_row.find("span", class_="percent-metagame")
                change_span = meta_row.find("div", class_="diffright")
                if isinstance(share_span, Tag):
                    metagame_share = " ".join(share_span.get_text(" ", strip=True).split())
                if isinstance(change_span, Tag):
                    change_note = " ".join(change_span.get_text(" ", strip=True).split())

            notes = self._join_notes([metagame_share, f"Weekly change: {change_note}" if change_note else None])

            results.append(
                DeckEntry(
                    name=deck_name,
                    source_site="aetherhub.com",
                    source_url=source_url,
                    format_label=format_label,
                    matches=matches,
                    deck_text=None,
                    notes=notes,
                )
            )
            if len(results) >= limit:
                break

        return results

    def fetch_deck_text(self, source_url: str) -> str | None:
        deck_id = self._extract_deck_id(source_url)
        return self._fetch_mtga_deck_text(deck_id)

    def _fetch_mtga_deck_text(self, deck_id: str) -> str | None:
        if not deck_id:
            return None
        if deck_id in self._deck_text_cache:
            return self._deck_text_cache[deck_id]
        try:
            response = self._session.get(
                urljoin(self.BASE_URL, "/Deck/FetchMtgaDeckJson"),
                params={"deckId": deck_id, "langId": self.ENGLISH_LANG_ID, "simple": "true"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            self._deck_text_cache[deck_id] = None
            return None

        if not isinstance(payload, dict):
            self._deck_text_cache[deck_id] = None
            return None
        cards = payload.get("convertedDeck")
        if not isinstance(cards, list) or not cards:
            self._deck_text_cache[deck_id] = None
            return None

        lines: list[str] = []
        for row in cards:
            if not isinstance(row, dict):
                continue
            quantity = row.get("quantity")
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            if isinstance(quantity, int):
                line = f"{quantity} {name}"
                set_code = str(row.get("set") or "").strip()
                number = str(row.get("number") or "").strip()
                if set_code and number:
                    line = f"{line} ({set_code}) {number}"
            else:
                line = name
            lines.append(line)
        if not lines:
            self._deck_text_cache[deck_id] = None
            return None
        deck_text = "\n".join(lines)
        self._deck_text_cache[deck_id] = deck_text
        return deck_text

    def _normalize_event_name(self, raw_name: str) -> tuple[str | None, str | None]:
        clean = " ".join(raw_name.split())
        if not clean:
            return None, None
        match = self.DATE_TOKEN_RE.search(clean)
        if not match:
            return clean, None
        us_date = self._to_us_date(match.group(1))
        if not us_date:
            return clean, None
        normalized = f"{clean[:match.start()]}{us_date}{clean[match.end():]}".strip()
        return normalized, us_date

    @staticmethod
    def _to_us_date(token: str) -> str | None:
        parts = token.split("/")
        if len(parts) != 3:
            return None
        day_raw, month_raw, year_raw = parts
        try:
            day = int(day_raw)
            month = int(month_raw)
            year = int(year_raw)
        except ValueError:
            return None
        if year < 100:
            year += 2000
        try:
            parsed = datetime(year=year, month=month, day=day)
        except ValueError:
            return None
        return parsed.strftime("%m/%d/%Y")

    def _extract_deck_id(self, url: str) -> str:
        match = self.DECK_ID_RE.search(url)
        return match.group(1) if match else ""

    def _extract_matches(self, text: str) -> int | None:
        match = self.MATCHES_RE.search(text or "")
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _join_notes(parts: list[str | None]) -> str | None:
        values = [part.strip() for part in parts if part and part.strip()]
        if not values:
            return None
        return " | ".join(values)
