"""Text formats: CSV/TSV, JSON, Markdown, HTML and psql-style text tables.

Markdown and JSON are the formats to hand to an LLM: they are compact, keep types, and
JSON output is a valid workbook spec, so it round-trips through ``mm.from_spec``.
"""

from __future__ import annotations

import csv
import html
import io
import json
import logging
import unicodedata
from typing import TYPE_CHECKING, Any

from ..config import DEFAULTS
from ..types import (
    BaseFieldType,
    BoolFieldType,
    CurrencyFieldType,
    DateFieldType,
    DecimalFieldType,
    DurationFieldType,
    FloatFieldType,
    FormulaFieldType,
    ImageFieldType,
    IntFieldType,
    NoneFieldType,
    PercentFieldType,
    StringFieldType,
    TimeFieldType,
    URLFieldType,
)
from .base import ComposerBase, cell_style, header_style

if TYPE_CHECKING:
    from ..document import Document

log = logging.getLogger(__name__)

__all__ = [
    "ComposerCSV",
    "ComposerHTML",
    "ComposerJSON",
    "ComposerMarkdown",
    "ComposerTSV",
    "ComposerText",
]

_NUMERIC = (IntFieldType, FloatFieldType, DecimalFieldType)
_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")
# types whose JSON value already says what they are (no "type" hint needed)
_SELF_DESCRIBING = (
    StringFieldType,
    IntFieldType,
    FloatFieldType,
    BoolFieldType,
    FormulaFieldType,
    URLFieldType,
    ImageFieldType,
)


def _visible_rows(document: Document) -> tuple[list[list[BaseFieldType]], int]:
    rows = document.grid.grid_data
    limit = document.config.get("max_rows")
    if limit is not None and len(rows) > int(limit):
        return rows[: int(limit)], len(rows) - int(limit)
    return rows, 0


def _titles(document: Document) -> list[str]:
    return [str(t) for t in document.data_model.field_titles]


def _is_numeric_column(document: Document, col: int) -> bool:
    header = document.data_model.field_headers[col]
    return isinstance(header, type) and issubclass(header, (*_NUMERIC, DurationFieldType))


class _TextComposer(ComposerBase):
    binary = False
    media_type = "text/plain; charset=utf-8"

    def run(self, child: Any = None) -> str:
        parts = [self.render_sheet(doc, len(self.sheets()) > 1) for doc in self.sheets()]
        return self.join(parts)

    def join(self, parts: list[str]) -> str:
        return "\n\n".join(parts)

    def render_sheet(self, document: Document, multiple: bool) -> str:
        raise NotImplementedError


class ComposerCSV(_TextComposer):
    """CSV. Only the first sheet is written (CSV has no sheets)."""

    format_name = "csv"
    media_type = "text/csv; charset=utf-8"
    delimiter: str | None = None

    def run(self, child: Any = None) -> str:
        if self.document.children:
            log.warning(
                "CSV holds one sheet; %d child sheet(s) skipped", len(self.document.children)
            )
        return self.render_sheet(self.document, False)

    def render_sheet(self, document: Document, multiple: bool) -> str:
        config = document.config
        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter=self.delimiter or config.get("csv_delimiter", ","),
            lineterminator="\n",
        )
        escape = bool(config.get("escape_formula_strings", True))
        if config.get("headers", True):
            writer.writerow([_csv_escape(t, escape) for t in _titles(document)])
        rows, _ = _visible_rows(document)
        for row in rows:
            writer.writerow([self.value(cell, escape) for cell in row])
        return buffer.getvalue()

    @staticmethod
    def value(cell: BaseFieldType, escape: bool) -> str:
        if isinstance(cell, NoneFieldType) or cell.data is None:
            return ""
        if isinstance(cell, FormulaFieldType):
            return "=" + cell.expression
        if isinstance(cell, URLFieldType):
            return str(cell.data)
        if isinstance(cell, ImageFieldType):
            return str(cell.data)
        if isinstance(cell, (DateFieldType, TimeFieldType)):
            if cell.format and "%" in cell.format:
                return cell.display()
            return str(cell.data.isoformat())
        if isinstance(cell, _NUMERIC):
            return str(cell.data)
        if isinstance(cell, StringFieldType) or isinstance(cell.data, str):
            return _csv_escape(str(cell.data), escape)
        return cell.display()


class ComposerTSV(ComposerCSV):
    format_name = "tsv"
    media_type = "text/tab-separated-values; charset=utf-8"
    delimiter = "\t"


def _csv_escape(text: str, escape: bool) -> str:
    # CSV/formula injection guard (OWASP): text starting with a formula trigger is
    # prefixed with an apostrophe so spreadsheet apps show it as text.
    if escape and text.startswith(_FORMULA_TRIGGERS):
        return "'" + text
    return text


class ComposerJSON(_TextComposer):
    """JSON in the workbook-spec shape: ``{"sheets": [{"name", "columns", "rows"}]}``."""

    format_name = "json"
    media_type = "application/json"

    def run(self, child: Any = None) -> str:
        return json.dumps(self.to_spec(), indent=2, ensure_ascii=False, default=str)

    def to_spec(self) -> dict[str, Any]:
        spec: dict[str, Any] = {}
        config = self.document.config
        for key in ("title", "author", "description"):
            if config.get(key):
                spec[key] = config.get(key)
        spec["sheets"] = [self.sheet_spec(doc, index) for index, doc in enumerate(self.sheets(), 1)]
        return spec

    @staticmethod
    def sheet_spec(document: Document, index: int) -> dict[str, Any]:
        model = document.data_model
        rows, _ = _visible_rows(document)
        options = {
            k: v
            for k, v in document.config.changed().items()
            if k in DEFAULTS and k not in ("title", "author", "description")
        }
        sheet: dict[str, Any] = {
            "name": document.name or f"Sheet {index}",
            "columns": [
                {"name": _json_key(t), "type": h.type_name}
                for t, h in zip(model.field_titles, model.field_headers)
            ],
            "rows": [
                [_json_cell(cell, header) for cell, header in zip(row, model.field_headers)]
                for row in rows
            ],
        }
        if options:
            sheet["options"] = json.loads(json.dumps(options, default=str))
        return sheet


def _json_key(value: Any) -> Any:
    return value if isinstance(value, (str, int, float)) else str(value)


def _json_cell(cell: BaseFieldType, column_type: type) -> Any:
    value = cell.to_json()
    extras: dict[str, Any] = {}
    if isinstance(cell, PercentFieldType):
        if cell.decimals:
            extras["decimals"] = cell.decimals
    elif isinstance(cell, CurrencyFieldType):
        if cell.symbol != "$":
            extras["symbol"] = cell.symbol
        if cell.decimals != 2:
            extras["decimals"] = cell.decimals
    kind = type(cell)
    if extras or (kind is not column_type and kind not in (NoneFieldType, *_SELF_DESCRIBING)):
        extras = {"type": cell.type_name, **extras}
    if cell.format:
        extras["format"] = cell.format
    if cell.style:
        extras["style"] = cell.style
    if not extras:
        return value
    if isinstance(value, dict):
        return {**value, **extras}
    return {"value": value, **extras}


class ComposerMarkdown(_TextComposer):
    """GitHub-flavoured Markdown tables, one per sheet (``## name`` headings)."""

    format_name = "markdown"
    media_type = "text/markdown; charset=utf-8"

    def render_sheet(self, document: Document, multiple: bool) -> str:
        lines: list[str] = []
        if multiple or document.name:
            lines += [f"## {document.name or 'Sheet'}", ""]
        titles = _titles(document)
        if not titles:
            return "\n".join([*lines, "_(empty sheet)_"])
        lines.append("| " + " | ".join(_md(t) for t in titles) + " |")
        lines.append(
            "|"
            + "|".join(
                " ---: " if _is_numeric_column(document, i) else " --- " for i in range(len(titles))
            )
            + "|"
        )
        rows, hidden = _visible_rows(document)
        for row in rows:
            lines.append("| " + " | ".join(_md(self.value(c)) for c in row) + " |")
        if hidden:
            lines += ["", f"_... {hidden} more row(s) not shown_"]
        return "\n".join(lines)

    @staticmethod
    def value(cell: BaseFieldType) -> str:
        if isinstance(cell, URLFieldType) and cell.data:
            return f"[{cell.displayname}]({cell.data})"
        if isinstance(cell, ImageFieldType):
            return f"![image]({cell.data})"
        return cell.display()

    def join(self, parts: list[str]) -> str:
        return "\n\n".join(parts) + "\n"


def _md(text: str) -> str:
    return (
        text.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")
    )


class ComposerHTML(_TextComposer):
    """A standalone HTML page (or a fragment with ``html_fragment=True``) with styled tables."""

    format_name = "html"
    media_type = "text/html; charset=utf-8"

    def run(self, child: Any = None) -> str:
        sheets = self.sheets()
        body = "\n".join(self.render_sheet(doc, len(sheets) > 1) for doc in sheets)
        if self.document.config.get("html_fragment"):
            return body
        title = html.escape(
            str(self.document.config.get("title") or self.document.name or "Marmir")
        )
        return (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f"<title>{title}</title>\n"
            "<style>table{border-collapse:collapse;margin:1em 0}"
            "th,td{padding:4px 8px;border:1px solid #d0d0d0}"
            "caption{font-weight:bold;text-align:left;padding:4px 0}</style>\n"
            f"</head>\n<body>\n{body}\n</body>\n</html>\n"
        )

    def render_sheet(self, document: Document, multiple: bool) -> str:
        out = ['<table class="marmir">']
        if multiple or document.name:
            out.append(f"<caption>{html.escape(str(document.name or 'Sheet'))}</caption>")
        if document.config.get("headers", True):
            css = header_style(document).to_css()
            attr = f' style="{html.escape(css)}"' if css else ""
            header_cells = "".join(
                f'<th scope="col"{attr}>{html.escape(t)}</th>' for t in _titles(document)
            )
            out.append(f"<thead><tr>{header_cells}</tr></thead>")
        out.append("<tbody>")
        rows, hidden = _visible_rows(document)
        for data_row, row in enumerate(rows):
            cells = []
            for col, cell in enumerate(row):
                style = cell_style(document, data_row, col, cell)
                css = style.to_css()
                if style.text_align is None and isinstance(cell, _NUMERIC):
                    css = "; ".join(filter(None, [css, "text-align: right"]))
                attr = f' style="{html.escape(css)}"' if css else ""
                cells.append(f"<td{attr}>{self.value(cell)}</td>")
            out.append("<tr>" + "".join(cells) + "</tr>")
        out.append("</tbody>")
        if hidden:
            span = len(_titles(document))
            note = f"... {hidden} more row(s)"
            out.append(f'<tfoot><tr><td colspan="{span}">{note}</td></tr></tfoot>')
        out.append("</table>")
        return "\n".join(out)

    @staticmethod
    def value(cell: BaseFieldType) -> str:
        if isinstance(cell, URLFieldType) and cell.data:
            url = str(cell.data)
            label = html.escape(str(cell.displayname))
            if url.lower().startswith(("http://", "https://", "mailto:")):
                return f'<a href="{html.escape(url, quote=True)}">{label}</a>'
            return label
        if isinstance(cell, ImageFieldType):
            return f'<img src="{html.escape(str(cell.data), quote=True)}" alt="">'
        return html.escape(cell.display()).replace("\n", "<br>")


class ComposerText(_TextComposer):
    """psql-style plain-text tables."""

    format_name = "text"

    def render_sheet(self, document: Document, multiple: bool) -> str:
        titles = _titles(document)
        rows, hidden = _visible_rows(document)
        body = [[cell.display().replace("\n", " ") for cell in row] for row in rows]
        show_headers = document.config.get("headers", True)
        widths = [
            max([_width(t) if show_headers else 0] + [_width(r[i]) for r in body])
            for i, t in enumerate(titles)
        ]
        numeric = [_is_numeric_column(document, i) for i in range(len(titles))]
        rule = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        lines = []
        if multiple or document.name:
            lines.append(str(document.name or "Sheet"))
        lines.append(rule)
        if show_headers:
            lines.append(
                "|" + "|".join(f" {_pad(t, w, 'center')} " for t, w in zip(titles, widths)) + "|"
            )
            lines.append(rule)
        for row in body:
            lines.append(
                "|"
                + "|".join(
                    f" {_pad(v, w, 'right' if n else 'left')} "
                    for v, w, n in zip(row, widths, numeric)
                )
                + "|"
            )
        lines.append(rule)
        if hidden:
            lines.append(f"({hidden} more row(s) not shown)")
        return "\n".join(lines)


def _width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in text)


def _pad(text: str, width: int, align: str) -> str:
    gap = width - _width(text)
    if align == "right":
        return " " * gap + text
    if align == "center":
        left = gap // 2
        return " " * left + text + " " * (gap - left)
    return text + " " * gap
