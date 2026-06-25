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

DEFAULT_AETHERHUB_CREATORS = (
    "MTGMalone",
)

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


@dataclass(frozen=True)
class CreatorConfig:
    name: str
    short_name: str | None = None

    @property
    def label(self) -> str:
        short_name = self.short_name.strip() if self.short_name else ""
        return short_name or self.name


@dataclass(frozen=True)
class AppConfig:
    moxfield_creators: tuple[CreatorConfig, ...]
    aetherhub_creators: tuple[CreatorConfig, ...] = ()
    tcgplayer_creators: tuple[CreatorConfig, ...] = ()

    @property
    def moxfield_names(self) -> tuple[str, ...]:
        return tuple(creator.name for creator in self.moxfield_creators)


MoxfieldCreator = CreatorConfig


def load_config() -> AppConfig:
    raw_moxfield_creators: list[CreatorConfig] = [
        CreatorConfig(name=name) for name in DEFAULT_MOXFIELD_NAMES
    ]
    raw_aetherhub_creators: list[CreatorConfig] = [
        CreatorConfig(name=name) for name in DEFAULT_AETHERHUB_CREATORS
    ]
    raw_tcgplayer_creators: list[CreatorConfig] = []

    if CONFIG_PATH.exists():
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            candidate_names = payload.get("MoxfieldNames")
            if isinstance(candidate_names, list):
                raw_moxfield_creators = [
                    creator
                    for item in candidate_names
                    if (creator := _parse_creator_config(item)) is not None
                ]

            candidate_aetherhub_creators = payload.get("AtherhubCreators")
            if isinstance(candidate_aetherhub_creators, list):
                raw_aetherhub_creators = [
                    creator
                    for item in candidate_aetherhub_creators
                    if (creator := _parse_creator_config(item)) is not None
                ]

            candidate_tcgplayer_creators = (
                payload.get("TcgplayerCreators")
                or payload.get("TCGPlayerCreators")
                or payload.get("TcgPlayerCreators")
            )
            if isinstance(candidate_tcgplayer_creators, list):
                raw_tcgplayer_creators = [
                    creator
                    for item in candidate_tcgplayer_creators
                    if (creator := _parse_creator_config(item)) is not None
                ]

    return AppConfig(
        moxfield_creators=_dedupe_creators(raw_moxfield_creators),
        aetherhub_creators=_dedupe_creators(raw_aetherhub_creators),
        tcgplayer_creators=_dedupe_creators(raw_tcgplayer_creators),
    )


def _dedupe_creators(creators: list[CreatorConfig]) -> tuple[CreatorConfig, ...]:
    deduped_creators: list[CreatorConfig] = []
    seen: set[str] = set()
    for creator in creators:
        lowered = creator.name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped_creators.append(creator)
    return tuple(deduped_creators)


def _parse_creator_config(item: object) -> CreatorConfig | None:
    if isinstance(item, str):
        name = item.strip()
        return CreatorConfig(name=name) if name else None

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
    return CreatorConfig(name=raw_name.strip(), short_name=short_name or None)
