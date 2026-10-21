"""Legacy Excel 97-2003 (``.xls``) output via ``xlwt`` (``pip install 'marmir[xls]'``)."""

from __future__ import annotations

import datetime as dt
import io
import logging
import os
import tempfile
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ..colors import get_closest_rgb_match
from ..errors import MarmirError, MissingDependencyError
from ..fonts import string_width_chars
from ..style import Style
from ..types import (
    BaseFieldType,
    DateTimeFieldType,
    FormulaFieldType,
    HeaderFieldType,
    ImageFieldType,
    NoneFieldType,
    URLFieldType,
)
from .base import ComposerBase, cell_style, column_key_lookup, header_style, number_format
from .xlsx import safe_sheet_name

if TYPE_CHECKING:
    from ..document import Document

log = logging.getLogger(__name__)

__all__ = ["ComposerXLS"]

MAX_ROWS = 65536
MAX_COLS = 256
_HORZ = {"general": 0, "left": 1, "center": 2, "right": 3, "fill": 4, "justify": 5}
_VERT = {"top": 0, "center": 1, "bottom": 2}
_BORDER = {"thin": 1, "medium": 2, "dashed": 3, "dotted": 4, "thick": 5, "double": 6, "hair": 7}


def _xlwt() -> Any:
    try:
        import xlwt
    except ImportError as exc:
        raise MissingDependencyError("xlwt", "xls", "Legacy .xls output") from exc
    return xlwt


class ComposerXLS(ComposerBase):
    format_name = "xls"
    binary = True
    media_type = "application/vnd.ms-excel"

    def __init__(self, data_model: Any, grid: Any, document: Document):
        super().__init__(data_model, grid, document)
        self.xlwt = _xlwt()
        self._styles: dict[tuple[Style, str | None, bool], Any] = {}
        self._tempfiles: list[str] = []

    def run(self, child: Any = None) -> bytes | None:
        top = child is None
        workbook = self.xlwt.Workbook(encoding="utf-8", style_compression=2) if top else child
        used: set[str] = set()
        try:
            for index, document in enumerate(self.sheets(), start=1):
                name = safe_sheet_name(document.name, index, used)
                sheet = workbook.add_sheet(name, cell_overwrite_ok=True)
                self.write_sheet(sheet, document)
            if not top:
                return None
            buffer = io.BytesIO()
            workbook.save(buffer)
            return buffer.getvalue()
        finally:
            for path in self._tempfiles:
                os.unlink(path)

    def write_sheet(self, sheet: Any, document: Document) -> None:
        config = document.config
        titles = document.data_model.field_titles
        rows = document.grid.grid_data
        offset = 1 if config.get("headers", True) and titles else 0
        if len(rows) + offset > MAX_ROWS or len(titles) > MAX_COLS:
            raise MarmirError(
                f"XLS supports at most {MAX_ROWS} rows and {MAX_COLS} columns; use xlsx instead"
            )
        widths: dict[int, float] = {}
        if offset:
            hstyle = header_style(document)
            for col, title in enumerate(titles):
                sheet.write(0, col, str(title), self._xf(hstyle, None))
                widths[col] = string_width_chars(
                    str(title), hstyle.font_family, hstyle.font_size or 10, bool(hstyle.bold)
                )

        for data_row, row in enumerate(rows):
            for col, field in enumerate(row):
                style = cell_style(document, data_row, col, field)
                fmt = number_format(document, col, field, style)
                text = self.write_value(sheet, data_row + offset, col, field, style, fmt)
                if text:
                    width = string_width_chars(
                        text, style.font_family, style.font_size or 10, bool(style.bold)
                    )
                    widths[col] = max(widths.get(col, 0.0), width)

        freeze_row = int(config.get("freeze_row", 0) or 0)
        if not offset and freeze_row == 1:
            freeze_row = 0  # nothing to freeze without a header row
        freeze_col = int(config.get("freeze_col", 0) or 0)
        if freeze_row or freeze_col:
            sheet.panes_frozen = True
            sheet.horz_split_pos = freeze_row
            sheet.vert_split_pos = freeze_col

        fixed = config.get("column_widths") or {}
        lo = float(config.get("min_col_width", 0) or 0)
        hi = float(config.get("max_col_width", 255) or 255)
        for col, title in enumerate(titles):
            width = column_key_lookup(fixed, title, col)
            if width is None and config.get("adjust_all_col_width", True) and col in widths:
                width = min(hi, max(lo, widths[col] + 2))
            if width is not None:
                sheet.col(col).width = min(65535, int(float(width) * 256))

    def write_value(
        self, sheet: Any, row: int, col: int, field: BaseFieldType, style: Style, fmt: str | None
    ) -> str:
        xlwt = self.xlwt
        if isinstance(field, ImageFieldType):
            sheet.insert_bitmap(self._bitmap(field), row, col)
            return ""
        if isinstance(field, URLFieldType):
            url = str(field.data).replace('"', '""')
            label = str(field.displayname).replace('"', '""')
            sheet.write(
                row, col, xlwt.Formula(f'HYPERLINK("{url}";"{label}")'), self._xf(style, fmt, True)
            )
            return str(field.displayname)
        if isinstance(field, FormulaFieldType):
            sheet.write(row, col, xlwt.Formula(field.expression), self._xf(style, fmt))
            return ""
        if isinstance(field, NoneFieldType) or field.data is None:
            sheet.write(row, col, None, self._xf(style, fmt))
            return ""
        value: Any = field.data
        if isinstance(field, HeaderFieldType):
            value = str(value)
        elif isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, dt.timedelta):
            value = value.total_seconds() / 86400.0  # Excel durations are fractions of a day
        sheet.write(row, col, value, self._xf(style, fmt))
        if isinstance(field, DateTimeFieldType):
            return "0000-00-00 00:00:00"
        return field.display()

    def _bitmap(self, field: ImageFieldType) -> str:
        path = str(field.data)
        if path.lower().endswith(".bmp") and not (field.width or field.height):
            return path
        try:
            from PIL import Image
        except ImportError as exc:
            if path.lower().endswith(".bmp"):
                return path
            raise MissingDependencyError("pillow", "images", "Non-BMP images in XLS") from exc
        with Image.open(path) as img:
            img = img.convert("RGB")
            if field.width or field.height:
                img = img.resize((field.width or img.width, field.height or img.height))
            handle, tmp = tempfile.mkstemp(suffix=".bmp")
            os.close(handle)
            img.save(tmp, "BMP")
        self._tempfiles.append(tmp)
        return tmp

    def _xf(self, style: Style, fmt: str | None, link: bool = False) -> Any:
        key = (style, fmt, link)
        if key in self._styles:
            return self._styles[key]
        xlwt = self.xlwt
        xf = xlwt.XFStyle()
        font = xlwt.Font()
        font.name = style.font_family or "Arial"
        font.bold = bool(style.bold)
        font.italic = bool(style.italic)
        font.struck_out = bool(style.strike)
        font.height = int((style.font_size or 10) * 20)
        if style.underline or link:
            font.underline = xlwt.Font.UNDERLINE_SINGLE
        if style.color:
            font.colour_index = get_closest_rgb_match(style.color)
        elif link:
            font.colour_index = get_closest_rgb_match("0563C1")
        xf.font = font
        if style.background_color:
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = get_closest_rgb_match(style.background_color)
            xf.pattern = pattern
        alignment = xlwt.Alignment()
        alignment.horz = _HORZ.get(style.text_align or "general", 0)
        alignment.vert = _VERT.get(style.vertical_align or "bottom", 2)
        alignment.wrap = 1 if style.wrap else 0
        xf.alignment = alignment
        if style.border_style and style.border_style != "none":
            borders = xlwt.Borders()
            line = _BORDER.get(style.border_style, 1)
            borders.left = borders.right = borders.top = borders.bottom = line
            colour = get_closest_rgb_match(style.border_color or "000000")
            borders.left_colour = borders.right_colour = colour
            borders.top_colour = borders.bottom_colour = colour
            xf.borders = borders
        if fmt:
            xf.num_format_str = fmt
        self._styles[key] = xf
        return xf
