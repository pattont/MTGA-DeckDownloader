from __future__ import annotations

import unittest

from mtga_deck_downloader.scrapers.aetherhub import AetherhubScraper


class FakeResponse:
    def __init__(
        self,
        *,
        payload: dict[str, object] | None = None,
        text: str = "",
    ) -> None:
        self._payload = payload or {}
        self.content = text.encode("utf-8")
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class RecordingSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        params = kwargs.get("params")
        if isinstance(params, dict) and url.endswith("/Deck/FetchMtgaDeckJson"):
            deck_id = params.get("deckId")
            if deck_id == "1415774":
                return FakeResponse(
                    payload={
                        "convertedDeck": [
                            {
                                "quantity": 4,
                                "name": "Gran-Gran",
                                "set": "TLA",
                                "number": "12",
                            }
                        ]
                    }
                )
            return FakeResponse(payload={"convertedDeck": []})

        return FakeResponse(text='<a id="drawSim" data-deckid="1415774"></a>')


class AetherhubScraperTests(unittest.TestCase):
    def test_fetch_deck_text_falls_back_to_page_id_when_slug_ends_with_digit(self) -> None:
        scraper = AetherhubScraper.__new__(AetherhubScraper)
        scraper._session = RecordingSession()
        scraper._deck_text_cache = {}
        scraper._deck_id_cache = {}

        deck_text = scraper.fetch_deck_text(
            "https://aetherhub.com/Deck/thor-turns-tier-1-to-tier-0"
        )

        self.assertEqual(deck_text, "4 Gran-Gran (TLA) 12")
        self.assertEqual(
            [call["url"] for call in scraper._session.calls],
            [
                "https://aetherhub.com/Deck/FetchMtgaDeckJson",
                "https://aetherhub.com/Deck/thor-turns-tier-1-to-tier-0",
                "https://aetherhub.com/Deck/FetchMtgaDeckJson",
            ],
        )


if __name__ == "__main__":
    unittest.main()
