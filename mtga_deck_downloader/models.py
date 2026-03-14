from dataclasses import dataclass
from enum import Enum


class MatchFormat(str, Enum):
    ANY = "any"
    BO1 = "bo1"
    BO3 = "bo3"

    @property
    def label(self) -> str:
        if self is MatchFormat.BO1:
            return "Best of 1 (Bo1)"
        if self is MatchFormat.BO3:
            return "Best of 3 (Bo3)"
        return "Any Format"


@dataclass(frozen=True)
class DeckSource:
    name: str
    url: str
    description: str
    formats: tuple[MatchFormat, ...]

    def supports(self, selected_format: MatchFormat) -> bool:
        if selected_format is MatchFormat.ANY:
            return True
        return selected_format in self.formats
