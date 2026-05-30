from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MOXFIELD_NAMES = (
    "Ashlizzlle",
    "Swayzemtg",
    "covertgoblue",
    "carlomtg",
)

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


@dataclass(frozen=True)
class MoxfieldCreator:
    name: str
    short_name: str | None = None

    @property
    def label(self) -> str:
        short_name = self.short_name.strip() if self.short_name else ""
        return short_name or self.name


@dataclass(frozen=True)
class AppConfig:
    moxfield_creators: tuple[MoxfieldCreator, ...]

    @property
    def moxfield_names(self) -> tuple[str, ...]:
        return tuple(creator.name for creator in self.moxfield_creators)


def load_config() -> AppConfig:
    raw_creators: list[MoxfieldCreator] = [
        MoxfieldCreator(name=name) for name in DEFAULT_MOXFIELD_NAMES
    ]

    if CONFIG_PATH.exists():
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            candidate_names = payload.get("MoxfieldNames")
            if isinstance(candidate_names, list):
                raw_creators = [
                    creator
                    for item in candidate_names
                    if (creator := _parse_moxfield_creator(item)) is not None
                ]

    deduped_creators: list[MoxfieldCreator] = []
    seen: set[str] = set()
    for creator in raw_creators:
        lowered = creator.name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped_creators.append(creator)

    return AppConfig(moxfield_creators=tuple(deduped_creators))


def _parse_moxfield_creator(item: object) -> MoxfieldCreator | None:
    if isinstance(item, str):
        name = item.strip()
        return MoxfieldCreator(name=name) if name else None

    if not isinstance(item, dict):
        return None

    raw_name = item.get("Name") or item.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return None

    raw_short_name = (
        item.get("ShortName")
        or item.get("shortName")
        or item.get("short_name")
        or item.get("Short")
        or item.get("short")
    )
    short_name = raw_short_name.strip() if isinstance(raw_short_name, str) else None
    return MoxfieldCreator(name=raw_name.strip(), short_name=short_name or None)
