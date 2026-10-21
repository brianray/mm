"""Composer base class and helpers shared by every output format."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from ..formats import excel_date_format
from ..style import Style, merge_styles, parse_style
from ..types import (
    BaseFieldType,
    DateFieldType,
    DateTimeFieldType,
    DecimalFieldType,
    DurationFieldType,
    FloatFieldType,
    FormulaFieldType,
    HeaderFieldType,
    IntFieldType,
    TimeFieldType,
)

if TYPE_CHECKING:
    from ..document import Document

log = logging.getLogger(__name__)

__all__ = ["ComposerBase", "cell_style", "column_key_lookup", "header_style", "number_format"]

NUMERIC_TYPES = (IntFieldType, FloatFieldType, DecimalFieldType)


class ComposerBase:
    """Writes a ``Document`` (and its child sheets) in one output format.

    Subclasses implement ``run(child=None)``, returning ``bytes`` for binary formats and
    ``str`` for text formats. The legacy cell-by-cell hooks (``write_header``,
    ``iterate_grid``, ``start_new_row``, ``write_cell``, ``end_row``, ``finish``,
    ``set_option``) are still called by ``iterate_grid`` for composers that use them.
    """

    #: Registry name, e.g. ``"xlsx"``.
    format_name = "base"
    #: True when ``run`` returns bytes.
    binary = False
    #: MIME type of the output.
    media_type = "application/octet-stream"

    def __init__(self, data_model: Any, grid: Any, document: Document):
        self.data_model = data_model
        self.grid = grid
        self.document = document
        self.row_id = 0
        self.col_id = 0

    def run(self, child: Any = None) -> Any:
        raise NotImplementedError("Overwrite run() in subclass")

    # -- legacy cell-by-cell protocol --------------------------------------------------
    def row(self, row: list[BaseFieldType]) -> None:
        self.col_id = 0
        self.start_new_row(self.row_id)
        for cell in row:
            self.write_cell(self.row_id, self.col_id, cell)
            self.col_id += 1
        self.end_row(self.row_id)
        self.row_id += 1

    def iterate_grid(self) -> None:
        for row in self.grid.grid_data:
            self.row(row)

    def write_header(self) -> None:
        for index, title in enumerate(self.data_model.field_titles):
            self.write_cell(self.row_id, index, HeaderFieldType(data=title))
        self.row_id += 1

    def start_new_row(self, row_id: int) -> None:
        pass

    def end_row(self, row_id: int) -> None:
        pass

    def write_cell(self, row_id: int, col_id: int, cell: BaseFieldType) -> None:
        pass

    def set_option(self, key: str) -> None:
        log.debug("%s not supported with this composer %s", key, type(self).__name__)

    def finish(self) -> None:
        """Called after the grid is written; applies each config option via ``set_option``."""
        for key in self.document.config.to_dict():
            self.set_option(key)

    # -- helpers ---------------------------------------------------------------------
    def sheets(self) -> list[Document]:
        """This document followed by all of its (nested) children."""
        return self.document.sheets


def header_style(document: Document) -> Style:
    return parse_style(document.config.get("header_style", ""))


def column_key_lookup(mapping: dict[Any, Any] | None, title: Any, index: int) -> Any:
    """Look up a per-column setting by title, 0-based index or column letter."""
    if not mapping:
        return None
    for key in (title, str(title), index, _letter(index)):
        if key in mapping:
            return mapping[key]
    return None


def cell_style(document: Document, data_row: int, col_index: int, cell: BaseFieldType) -> Style:
    """Effective style: alternating row style, then column style, then the cell's own."""
    config = document.config
    row_styles = config.get("row_styles", ()) or ()
    row_css = row_styles[data_row % len(row_styles)] if row_styles else None
    title = document.data_model.field_titles[col_index]
    column_css = column_key_lookup(config.get("column_styles"), title, col_index)
    return _merge_css(row_css, column_css, cell.style)


@lru_cache(maxsize=4096)
def _merge_css(row_css: str | None, column_css: str | None, cell_css: str | None) -> Style:
    return merge_styles(row_css, column_css, cell_css)


def number_format(
    document: Document, col_index: int, cell: BaseFieldType, style: Style
) -> str | None:
    """The Excel number format for a cell, or ``None`` for "General"."""
    config = document.config
    title = document.data_model.field_titles[col_index]
    explicit = cell.format or style.number_format
    column_fmt = column_key_lookup(config.get("number_formats"), title, col_index)
    if isinstance(cell, DateTimeFieldType):
        return excel_date_format(explicit or column_fmt, config.get("datetime_format"), config)
    if isinstance(cell, DateFieldType):
        return excel_date_format(explicit or column_fmt, config.get("date_format"), config)
    if isinstance(cell, TimeFieldType):
        return excel_date_format(explicit or column_fmt, config.get("time_format"), config)
    if isinstance(cell, DurationFieldType):
        return explicit or column_fmt or config.get("duration_format")
    if isinstance(cell, (*NUMERIC_TYPES, FormulaFieldType)):
        # formulas usually compute numbers, so they take the column's number format
        return explicit or column_fmt or cell.default_format
    return explicit or column_fmt or cell.default_format


def _letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters
