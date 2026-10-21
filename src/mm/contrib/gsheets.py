"""Publish a document to Google Sheets with ``gspread`` (``pip install 'marmir[gsheets]'``).

Replaces the legacy ``write_gdata`` (Google retired the gdata ClientLogin API).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from mm.errors import MissingDependencyError
from mm.types import BaseFieldType, FormulaFieldType, NoneFieldType, URLFieldType

if TYPE_CHECKING:
    from mm.document import Document

__all__ = ["sheet_values", "write_gsheet"]


def sheet_values(document: Document) -> list[list[Any]]:
    """Values for one sheet as Google Sheets expects them (``USER_ENTERED`` input)."""
    rows: list[list[Any]] = []
    if document.config.get("headers", True):
        rows.append([_value(BaseFieldType(str(t))) for t in document.data_model.field_titles])
    for row in document.grid.grid_data:
        rows.append([_value(cell) for cell in row])
    return rows


def _value(cell: BaseFieldType) -> Any:
    if isinstance(cell, NoneFieldType) or cell.data is None:
        return ""
    if isinstance(cell, FormulaFieldType):
        return "=" + cell.expression
    if isinstance(cell, URLFieldType):
        url = str(cell.data).replace('"', '""')
        label = str(cell.displayname).replace('"', '""')
        return f'=HYPERLINK("{url}", "{label}")'
    data = cell.data
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, dt.datetime):
        return data.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(data, (dt.date, dt.time)):
        return data.isoformat()
    if isinstance(data, dt.timedelta):
        return cell.display()
    if isinstance(data, str) and data.startswith(("=", "+", "-", "@")):
        return "'" + data
    return data


def write_gsheet(
    document: Document,
    title: str,
    *,
    credentials_file: str | None = None,
    client: Any = None,
    share_with: str | list[str] | None = None,
    folder_id: str | None = None,
) -> Any:
    """Create a Google Sheet (one worksheet per sheet) and return the gspread Spreadsheet.

    Args:
        document: the document to publish.
        title: spreadsheet title.
        credentials_file: service-account JSON key file (default gspread location if omitted).
        client: an authorised ``gspread.Client`` (overrides ``credentials_file``).
        share_with: e-mail address(es) to share the sheet with as writers.
        folder_id: Drive folder to create the spreadsheet in.
    """
    if client is None:
        try:
            import gspread
        except ImportError as exc:
            raise MissingDependencyError("gspread", "gsheets", "Google Sheets output") from exc
        client = (
            gspread.service_account(filename=credentials_file)
            if credentials_file
            else gspread.service_account()
        )

    spreadsheet = client.create(title, folder_id=folder_id) if folder_id else client.create(title)
    first = spreadsheet.sheet1
    for index, doc in enumerate(document.sheets):
        values = sheet_values(doc)
        rows = max(len(values), 1)
        cols = max((len(r) for r in values), default=1) or 1
        name = doc.name or f"Sheet {index + 1}"
        if index == 0:
            worksheet = first
            worksheet.update_title(name)
            worksheet.resize(rows=rows, cols=cols)
        else:
            worksheet = spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)
        if values:
            worksheet.update(values, "A1", value_input_option="USER_ENTERED")
        freeze = int(doc.config.get("freeze_row", 0) or 0) if doc.config.get("headers", True) else 0
        if freeze or doc.config.get("freeze_col"):
            worksheet.freeze(
                rows=freeze or None, cols=int(doc.config.get("freeze_col") or 0) or None
            )
    for email in [share_with] if isinstance(share_with, str) else share_with or []:
        spreadsheet.share(email, perm_type="user", role="writer")
    return spreadsheet
