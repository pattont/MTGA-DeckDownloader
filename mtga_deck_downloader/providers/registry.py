from __future__ import annotations

import importlib
import pkgutil

import mtga_deck_downloader.providers as providers_pkg
from mtga_deck_downloader.providers.base import DeckProvider


def load_providers() -> list[DeckProvider]:
    providers: list[DeckProvider] = []

    for module_info in pkgutil.iter_modules(
        providers_pkg.__path__, f"{providers_pkg.__name__}."
    ):
        if module_info.name.endswith(".base") or module_info.name.endswith(".registry"):
            continue

        module = importlib.import_module(module_info.name)
        provider_class = getattr(module, "PROVIDER_CLASS", None)
        if provider_class and issubclass(provider_class, DeckProvider):
            providers.append(provider_class())

    return sorted(providers, key=lambda provider: provider.display_name.lower())
