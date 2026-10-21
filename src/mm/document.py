"""``Document``: the object you build from data and write out in any format."""

from __future__ import annotations

import inspect
import io
import logging
import os
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, Any

from .composers import ComposerBase, format_for_path, get_composer_class
from .config import Config
from .grid import GridBase, Serializer
from .model import DataModel
from .types import FormulaFieldType

log = logging.getLogger(__name__)

__all__ = ["Document", "DocumentWriter"]


class DocumentWriter:
    """Mixin that runs a composer to produce output (legacy name kept for subclasses)."""

    composer_class: type[ComposerBase] | None = None
    composer: ComposerBase | None = None

    # attributes provided by Document
    data_model: Any
    grid: Any
    config: Config

    def get_composer(self, format: str | None = None) -> ComposerBase:
        """Instantiate the composer for ``format`` (or the configured/default one)."""
        if format is not None:
            composer_class = get_composer_class(format)
        elif self.composer_class is not None:
            composer_class = self.composer_class
        else:
            composer_class = get_composer_class("xlsx")
        return composer_class(self.data_model, self.grid, self)  # type: ignore[arg-type]

    def writestr(self, format: str | None = None, *, child: Any = None) -> Any:
        """Render the document and return it.

        Binary formats (``xlsx``, ``xls``) return ``bytes``; text formats return ``str``.
        Without ``format`` the composer set with ``set_composer_class`` is used, else XLSX.
        """
        self.composer = self.get_composer(format)
        return self.composer.run(child=child)

    def to_bytes(self, format: str = "xlsx") -> bytes:
        """Render to bytes in any format (text formats are UTF-8 encoded)."""
        out = self.writestr(format)
        return out if isinstance(out, bytes) else str(out).encode("utf-8")

    def write(self, target: str | os.PathLike[str] | IO[Any], format: str | None = None) -> Any:
        """Write to a path or file object. The format comes from ``format``, the file
        extension, ``set_composer_class`` or defaults to XLSX. Returns the path/file."""
        fmt = format
        if fmt is None and isinstance(target, (str, os.PathLike)):
            fmt = format_for_path(target)
            if fmt:
                log.debug("Setting output format to %s, based on file extension", fmt)
        if fmt is None and self.composer_class is None:
            fmt = "xlsx"
        out = self.writestr(fmt)
        data = out if isinstance(out, bytes) else str(out).encode("utf-8")
        if isinstance(target, (str, os.PathLike)):
            Path(target).write_bytes(data)
            log.debug("wrote file: %s", os.fspath(target))
        elif isinstance(target, io.TextIOBase):
            if isinstance(out, bytes):
                raise TypeError("binary formats need a file opened in binary mode ('wb')")
            target.write(out)
        else:
            target.write(data)
        return target

    def write_gsheet(self, title: str, **kwargs: Any) -> Any:
        """Publish as a Google Sheet. See ``mm.contrib.gsheets.write_gsheet``."""
        from .contrib.gsheets import write_gsheet

        return write_gsheet(self, title, **kwargs)  # type: ignore[arg-type]

    def write_gdata(
        self,
        name: str,
        username: str | None = None,
        password: str | None = None,
        auth_token: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Deprecated: Google retired the gdata ClientLogin API. Use ``write_gsheet``."""
        warnings.warn(
            "write_gdata() is deprecated; Google retired gdata/ClientLogin. "
            "Use write_gsheet(title, credentials_file=...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.write_gsheet(name, **kwargs)


class Document(DocumentWriter):
    """A sheet of data (plus optional child sheets) ready to be written.

    Args:
        data: rows as dicts, lists (with ``order``), dataclasses, a DataFrame, a DB-API
            cursor or a column dict. See ``mm.model.normalize_data``.
        data_model_class: optional class that defines the columns (legacy extension point).
        grid_class: optional grid class that turns rows into typed cells.
        serializer_class: optional serializer pairing the model and the data.
        config: a ``Config`` instance.
        config_dict: option overrides as a dict (legacy).
        order: column order / titles (required for list rows).
        column_types: ``{"column": mm.Date}`` or ``{"column": "date"}`` to force types.
        name: sheet name.
        **options: option overrides, e.g. ``Document(rows, autofilter=True)``.

    Example::

        doc = mm.Document([{"id": 1, "msg": "hi"}], name="Greetings")
        doc.write("greetings.xlsx")
    """

    def __init__(
        self,
        data: Any,
        data_model_class: type | None = None,
        grid_class: type | None = None,
        serializer_class: type | None = None,
        config: Config | None = None,
        config_dict: Mapping[str, Any] | None = None,
        order: Sequence[Any] | None = None,
        column_types: Mapping[Any, Any] | None = None,
        name: str | None = None,
        **options: Any,
    ):
        self.data = data
        self.config = config if config is not None else Config()
        if config_dict:
            self.config.set_dict(dict(config_dict))
        if options:
            self.config.set_dict(options)
        self.name = name
        self.children: list[Document] = []

        self.data_model_class = data_model_class or DataModel
        self.data_model = self._build_model(order, column_types)

        serializer = (serializer_class or Serializer)(
            self.data_model, self.data, self.config, grid_class=grid_class or GridBase
        )
        self.grid = serializer.serialize()
        log.debug("Document created")

    def _build_model(
        self, order: Sequence[Any] | None, column_types: Mapping[Any, Any] | None
    ) -> Any:
        params = inspect.signature(self.data_model_class).parameters
        kwargs: dict[str, Any] = {"order": order, "column_types": column_types}
        if "config" in params or any(p.kind is p.VAR_KEYWORD for p in params.values()):
            kwargs["config"] = self.config
        return self.data_model_class(self.data, **kwargs)

    # -- legacy API --------------------------------------------------------------------
    def set_composer_class(self, composer_class: type[ComposerBase] | str) -> None:
        """Choose the default output composer (a class or a format name)."""
        if isinstance(composer_class, str):
            composer_class = get_composer_class(composer_class)
        self.composer_class = composer_class

    def set_composer(self, composer: ComposerBase) -> None:
        self.composer = composer

    def set_name(self, name: str) -> None:
        self.name = name

    def add_child(self, document: Document) -> Document:
        """Add another document as an extra sheet; returns it."""
        self.children.append(document)
        return document

    # -- modern API --------------------------------------------------------------------
    def add_sheet(self, data: Any, name: str | None = None, **kwargs: Any) -> Document:
        """Create a child sheet that inherits this document's options.

        ``kwargs`` are passed to ``Document`` (``order``, ``column_types`` or options).
        """
        if "config" not in kwargs:
            kwargs["config"] = self.config.copy()
            for key in ("title", "author", "description"):
                setattr(kwargs["config"], key, None)
        return self.add_child(Document(data, name=name, **kwargs))

    @property
    def sheets(self) -> list[Document]:
        """This document followed by every (nested) child, in write order."""
        out: list[Document] = [self]
        for child in self.children:
            out.extend(child.sheets)
        return out

    @property
    def columns(self) -> list[dict[str, Any]]:
        """``[{"name": ..., "type": ...}]`` for this sheet."""
        return [
            {"name": title, "type": header.type_name}
            for title, header in zip(self.data_model.field_titles, self.data_model.field_headers)
        ]

    @property
    def rows(self) -> list[list[Any]]:
        """Cell values (plain Python objects) for this sheet; formulas as ``"=..."`` text."""
        return [
            [cell.display() if isinstance(cell, FormulaFieldType) else cell.data for cell in row]
            for row in self.grid.grid_data
        ]

    def to_records(self) -> list[dict[Any, Any]]:
        """Rows as dicts keyed by column title."""
        titles = self.data_model.field_titles
        return [dict(zip(titles, row)) for row in self.rows]

    def to_markdown(self, max_rows: int | None = None) -> str:
        """Markdown tables for every sheet -- ideal for putting a sheet in an LLM prompt."""
        return self._render_text("markdown", max_rows)

    def to_html(self, max_rows: int | None = None) -> str:
        return self._render_text("html", max_rows)

    def to_csv(self) -> str:
        return str(self.writestr("csv"))

    def to_text(self, max_rows: int | None = None) -> str:
        return self._render_text("text", max_rows)

    def to_json(self) -> str:
        """JSON in the workbook-spec shape (round-trips through ``mm.from_spec``)."""
        return str(self.writestr("json"))

    def to_spec(self) -> dict[str, Any]:
        """The workbook spec as a dict (see ``mm.spec``)."""
        from .composers.text import ComposerJSON

        composer = ComposerJSON(self.data_model, self.grid, self)
        return composer.to_spec()

    def describe(self, sample_rows: int = 3) -> dict[str, Any]:
        """A compact summary (sheets, columns, types, row counts, sample rows) for LLMs."""
        sheets = []
        for index, doc in enumerate(self.sheets, start=1):
            spec = type(self).to_spec_sheet(doc, index)
            sheets.append(
                {
                    "name": spec["name"],
                    "row_count": len(doc.grid.grid_data),
                    "columns": spec["columns"],
                    "sample_rows": spec["rows"][:sample_rows],
                }
            )
        return {"sheet_count": len(sheets), "sheets": sheets}

    @staticmethod
    def to_spec_sheet(document: Document, index: int = 1) -> dict[str, Any]:
        from .composers.text import ComposerJSON

        return ComposerJSON.sheet_spec(document, index)

    def _render_text(self, fmt: str, max_rows: int | None) -> str:
        saved = [(doc, doc.config.max_rows) for doc in self.sheets]
        try:
            if max_rows is not None:
                for doc, _ in saved:
                    doc.config.max_rows = max_rows
            return str(self.writestr(fmt))
        finally:
            for doc, value in saved:
                doc.config.max_rows = value

    # -- constructors --------------------------------------------------------------------
    @classmethod
    def from_spec(cls, spec: Mapping[str, Any] | str, **kwargs: Any) -> Document:
        """Build a document from a workbook spec (dict or JSON string). See ``mm.spec``."""
        from .spec import from_spec

        return from_spec(spec, **kwargs)

    @classmethod
    def from_file(cls, source: Any, format: str | None = None, **kwargs: Any) -> Document:
        """Load ``.xlsx``/``.xls``/``.csv``/``.tsv``/``.json`` into a document (all sheets)."""
        from .reader import read_document

        return read_document(source, format=format, **kwargs)

    @classmethod
    def from_cursor(cls, cursor: Any, **kwargs: Any) -> Document:
        """Build from a DB-API cursor after ``execute()``."""
        return cls(cursor, **kwargs)

    def __repr__(self) -> str:
        return (
            f"<Document name={self.name!r} rows={len(self.grid.grid_data)} "
            f"columns={len(self.data_model.field_titles)} children={len(self.children)}>"
        )
