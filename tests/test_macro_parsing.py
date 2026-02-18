import json

from macro_tibia import TibiaMacroRunner


def test_parse_macro_defaults() -> None:
    raw = {
        "name": "buff",
        "actions": [{"key": "f1"}],
    }

    macro = TibiaMacroRunner.parse_macro(raw)

    assert macro.name == "buff"
    assert macro.window_title_prefix == "Tibia - "
    assert macro.repeat == 1
    assert macro.interval_ms == 0
    assert macro.actions[0].key == "f1"
    assert macro.actions[0].delay_ms == 80


def test_load_macros_ignores_potion_settings(tmp_path) -> None:
    config = {
        "macros": [
            {
                "name": "heal",
                "actions": [{"key": "f1", "delay_ms": 100}],
            }
        ],
        "potion_settings": {
            "hp_threshold": 50,
            "mana_threshold": 40,
            "hp_key": "f4",
            "mana_key": "f5",
            "cooldown_ms": 300,
        },
    }
    config_path = tmp_path / "macros.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    macros = TibiaMacroRunner().load_macros(config_path)

    assert len(macros) == 1
    assert macros[0].name == "heal"
    assert macros[0].actions[0].key == "f1"
