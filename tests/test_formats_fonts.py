from __future__ import annotations

import pytest

from mm import fonts
from mm.config import Config
from mm.errors import UnsupportedFormatCodeException
from mm.formats import excel_date_format, to_excel_from_C_codes


@pytest.mark.parametrize(
    ("c_codes", "excel"),
    [
        ("%Y-%m-%d", "yyyy-mm-dd"),
        ("%Y-%m-%dT%H:%M:%S", 'yyyy-mm-dd"T"hh:mm:ss'),
        ("%d %B %Y", "dd mmmm yyyy"),
        ("%a %b %d", "ddd mmm dd"),
        ("%I:%M %p", "hh:mm AM/PM"),
        ("%H:%M:%S.%f", "hh:mm:ss.000"),
        ("100%%", '"100""%"'),
        ("%y", "yy"),
    ],
)
def test_c_codes(c_codes, excel):
    assert to_excel_from_C_codes(c_codes) == excel


def test_config_codes():
    cfg = Config(date_format="DD/MM/YYYY", time_format="h:mm", datetime_format="x")
    assert to_excel_from_C_codes("%x %X", cfg) == "DD/MM/YYYY h:mm"
    assert to_excel_from_C_codes("%c", {"datetime_format": "zz"}) == "zz"


@pytest.mark.parametrize("code", ["%j", "%U", "%w", "%W", "%z", "%Z", "%Q"])
def test_unsupported(code):
    with pytest.raises(UnsupportedFormatCodeException):
        to_excel_from_C_codes(f"%Y {code}")


def test_excel_date_format_passthrough():
    assert excel_date_format(None, "M/D/YY") == "M/D/YY"
    assert excel_date_format("yyyy", "M/D/YY") == "yyyy"
    assert excel_date_format("%Y", "M/D/YY") == "yyyy"


def test_font_widths():
    assert "Arial" in fonts.available_fonts()
    narrow = fonts.get_string_width("Arial", 10, "iiii")
    wide = fonts.get_string_width("Arial", 10, "WWWW")
    assert wide > narrow > 0
    assert fonts.get_string_width("Arial", 20, "abc") == pytest.approx(
        2 * fonts.get_string_width("Arial", 10, "abc")
    )
    assert fonts.get_string_width("arial", 10, "abc", bold=True) > fonts.get_string_width(
        "Arial", 10, "abc"
    )
    # unknown fonts fall back to Arial
    assert fonts.get_string_width("No Such Font", 10, "abc") == fonts.get_string_width(
        "Arial", 10, "abc"
    )
    # wide CJK characters count double
    assert fonts.get_string_width("Arial", 10, "日") > fonts.get_string_width("Arial", 10, "\x01")
    assert fonts.string_width_chars("line one\nmuch longer line two") == fonts.string_width_chars(
        "much longer line two"
    )
    assert 8 < fonts.string_width_chars("0000000000") < 12
