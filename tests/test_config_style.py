from __future__ import annotations

import pytest

import mm
from mm import colors
from mm.config import DEFAULTS, Config, ConfigBase
from mm.style import Style, StyleBase, merge_styles, parse_style


def test_config_defaults_and_overrides():
    cfg = Config({"headers": False}, autofilter=True)
    assert cfg.headers is False
    assert cfg.autofilter is True
    assert cfg.freeze_row == DEFAULTS["freeze_row"]
    assert cfg.get("missing", "fallback") == "fallback"
    assert cfg.changed() == {"headers": False, "autofilter": True}
    assert "headers" in repr(cfg)


def test_config_legacy_alias_and_custom_keys():
    cfg = ConfigBase({"INGORE_DATA_MISMATCH": False, "my_option": 3})
    assert cfg.ignore_data_mismatch is False
    assert cfg.INGORE_DATA_MISMATCH is False
    assert cfg.get("my_option") == 3
    with pytest.raises(AttributeError):
        _ = cfg.not_there


def test_config_subclass_class_attributes():
    class MyConfig(ConfigBase):
        headers = False
        freeze_row = 0

    cfg = MyConfig()
    assert cfg.headers is False
    assert cfg.freeze_row == 0


def test_config_copy_is_independent():
    cfg = Config(column_widths={"a": 10})
    clone = cfg.copy()
    clone.column_widths["a"] = 99
    assert cfg.column_widths["a"] == 10


def test_config_row_styles_string():
    assert Config(row_styles="color: red").row_styles == ("color: red",)


def test_parse_style_full():
    style = parse_style(
        "color: #fff; background: rgb(0, 0, 128); font-family: 'Times New Roman', serif; "
        "font-size: 16px; font-weight: 700; font-style: italic; text-decoration: underline line-through; "
        "text-align: right; vertical-align: middle; white-space: normal; border: 2px dashed #ccc; "
        "number-format: '0.00'"
    )
    assert style.color == "FFFFFF"
    assert style.background_color == "000080"
    assert style.font_family == "Times New Roman"
    assert style.font_size == 12.0
    assert style.bold and style.italic and style.underline and style.strike
    assert style.text_align == "right"
    assert style.vertical_align == "center"
    assert style.wrap is True
    assert style.border_style == "dashed"
    assert style.border_color == "CCCCCC"
    assert style.number_format == "0.00"


def test_parse_style_legacy_and_bad_input(caplog):
    style = parse_style(
        "font-style: bold; font-family: Times-New-Roman; nonsense; color: notacolor; zzz: 1"
    )
    assert style.bold is True
    assert style.font_family == "Times New Roman"
    assert style.color is None
    assert parse_style("") == Style()
    assert parse_style(None).is_empty()


def test_style_roundtrip_and_merge():
    css = "color: #FF0000; font-weight: bold; text-align: center; border: thin"
    style = parse_style(css)
    assert parse_style(style.to_css()) == style
    merged = merge_styles("color: red; font-size: 10pt", None, Style(color="0000FF"))
    assert merged.color == "0000FF"
    assert merged.font_size == 10


def test_style_base_legacy():
    legacy = StyleBase()
    legacy.style_from_string("color: #ffffff; font-size: 12pt; background-color: #0000B3; bogus: 1")
    assert legacy.font_size == 12
    assert legacy.to_style().background_color == "0000B3"
    legacy.font_size = "abc"
    assert legacy.font_size is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [("#abc", "AABBCC"), ("navy", "000080"), ("rgb(300, 1, 5)", "FF0105"), ("FF00FF00", "00FF00")],
)
def test_parse_color(value, expected):
    assert colors.parse_color(value) == expected


def test_color_helpers():
    with pytest.raises(ValueError):
        colors.parse_color("nope")
    assert colors.rgb("#102030") == (16, 32, 48)
    assert colors.to_hex("red") == "#FF0000"
    assert colors.get_closest_rgb_match("#FE0101") == 0x0A
    assert (
        colors.get_closest_rgb_match("#0000B3") == 0x0C
        or colors.get_closest_rgb_match("#0000B3") == 0x12
    )


def test_public_config_alias():
    assert mm.Config is Config
