from __future__ import annotations

import unittest

from mtga_deck_downloader.scrapers.moxfield import MoxfieldScraper


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class RecordingSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return self.response


class MoxfieldScraperTests(unittest.TestCase):
    def test_fetch_user_decks_uses_deck_search_author_filter(self) -> None:
        session = RecordingSession(
            FakeResponse(
                {
                    "data": [
                        {
                            "name": "Orzhov Offense Lifegain",
                            "publicUrl": "https://moxfield.com/decks/pjrbWDUR40CUnVEiZnrBPA",
                            "format": "standard",
                            "lastUpdatedAtUtc": "2026-05-16T14:57:39.457Z",
                        }
                    ]
                }
            )
        )
        scraper = MoxfieldScraper.__new__(MoxfieldScraper)
        scraper._session = session

        decks = scraper.fetch_user_decks("Ashlizzlle", limit=15)

        self.assertEqual(
            session.calls,
            [
                {
                    "url": "https://api2.moxfield.com/v2/decks/search",
                    "params": {
                        "pageNumber": 1,
                        "pageSize": 15,
                        "sortType": "updated",
                        "sortDirection": "descending",
                        "authorUserNames": "Ashlizzlle",
                        "showIllegal": True,
                    },
                    "timeout": 30,
                }
            ],
        )
        self.assertEqual(len(decks), 1)
        self.assertEqual(decks[0].name, "Orzhov Offense Lifegain")
        self.assertEqual(decks[0].source_url, "https://moxfield.com/decks/pjrbWDUR40CUnVEiZnrBPA")
        self.assertEqual(decks[0].format_label, "Standard")
        self.assertEqual(decks[0].event_date, "05/16/2026")


if __name__ == "__main__":
    unittest.main()
