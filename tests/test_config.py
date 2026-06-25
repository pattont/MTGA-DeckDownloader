from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mtga_deck_downloader import config as config_module


class ConfigTests(unittest.TestCase):
    def test_load_config_supports_moxfield_short_names(self) -> None:
        original_path = config_module.CONFIG_PATH
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "MoxfieldNames": [
                            {"Name": "Ashlizzlle", "ShortName": "Ash"},
                            "SwayzeMTG",
                        ],
                        "AtherhubCreators": [
                            {"Name": "MTGMalone", "ShortName": "Malone"},
                        ],
                        "TcgplayerCreators": [
                            {"Name": "Arne Huschenbeth", "ShortName": "Arne"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config_module.CONFIG_PATH = config_path
            try:
                config = config_module.load_config()
            finally:
                config_module.CONFIG_PATH = original_path

        self.assertEqual(
            [(creator.name, creator.short_name, creator.label) for creator in config.moxfield_creators],
            [
                ("Ashlizzlle", "Ash", "Ash"),
                ("SwayzeMTG", None, "SwayzeMTG"),
            ],
        )
        self.assertEqual(config.moxfield_names, ("Ashlizzlle", "SwayzeMTG"))
        self.assertEqual(
            [(creator.name, creator.short_name, creator.label) for creator in config.aetherhub_creators],
            [("MTGMalone", "Malone", "Malone")],
        )
        self.assertEqual(
            [(creator.name, creator.short_name, creator.label) for creator in config.tcgplayer_creators],
            [("Arne Huschenbeth", "Arne", "Arne")],
        )


if __name__ == "__main__":
    unittest.main()
