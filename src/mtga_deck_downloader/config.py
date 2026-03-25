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
class AppConfig:
    moxfield_names: tuple[str, ...]


def load_config() -> AppConfig:
    raw_names: list[str] = list(DEFAULT_MOXFIELD_NAMES)

    if CONFIG_PATH.exists():
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            candidate_names = payload.get("MoxfieldNames")
            if isinstance(candidate_names, list):
                raw_names = [
                    name.strip()
                    for name in candidate_names
                    if isinstance(name, str) and name.strip()
                ]

    deduped_names: list[str] = []
    seen: set[str] = set()
    for name in raw_names:
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped_names.append(name)

    return AppConfig(moxfield_names=tuple(deduped_names))
