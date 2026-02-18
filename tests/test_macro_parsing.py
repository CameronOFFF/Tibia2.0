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
