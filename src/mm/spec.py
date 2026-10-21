"""The workbook spec: a JSON format for describing spreadsheets.

This is the contract between language models and Marmir. A model (or any program)
produces a JSON document like::

    {
      "title": "Q3 Sales",
      "sheets": [
        {
          "name": "Sales",
          "columns": [
            {"name": "Region", "type": "string"},
            {"name": "Revenue", "type": "currency"},
            {"name": "Growth", "type": "percent"},
            {"name": "Closed", "type": "date", "format": "%Y-%m-%d"}
          ],
          "rows": [
            ["North", 125000, 0.12, "2024-09-30"],
            ["South", 98000, -0.03, "2024-09-28"],
            [{"value": "Total", "style": "font-weight: bold"},
             {"formula": "SUM(B2:B3)"}, null, null]
          ],
          "options": {"autofilter": true}
        }
      ]
    }

``validate_spec`` returns precise, path-prefixed error messages an LLM can act on, and
``from_spec`` turns a valid spec into a ``Document``. ``Document.to_spec`` (or the JSON
output format) produces the same shape, so specs round-trip.

Cell values are JSON scalars or objects:

* ``{"formula": "SUM(B2:B5)"}`` -- a formula (leading ``=`` optional)
* ``{"url": "https://...", "text": "label"}`` -- a hyperlink
* ``{"image": "path/to/file.png", "width": 120, "height": 80}`` -- an image (local use only)
* ``{"value": ..., "type": "date", "format": "...", "style": "..."}`` -- a typed/styled value

Strings that start with ``=`` are formulas unless ``options.infer_formulas`` is false.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import DEFAULTS, Config
from .errors import SpecValidationError
from .types import (
    BaseFieldType,
    CurrencyFieldType,
    FormulaFieldType,
    ImageFieldType,
    PercentFieldType,
    URLFieldType,
    field_type_for_name,
)

__all__ = [
    "CELL_TYPES",
    "WORKBOOK_SPEC_SCHEMA",
    "from_spec",
    "normalize_spec",
    "validate_spec",
]

#: Type names a spec may use for columns and cells.
CELL_TYPES = [
    "string",
    "integer",
    "number",
    "decimal",
    "percent",
    "currency",
    "boolean",
    "date",
    "datetime",
    "time",
    "duration",
    "url",
    "formula",
    "image",
]

_OPTION_KEYS = set(DEFAULTS) | {"html_fragment", "csv_bom"}
_DOC_KEYS = {"title", "author", "description"}
_CELL_KEYS = {
    "value",
    "type",
    "format",
    "style",
    "formula",
    "url",
    "text",
    "image",
    "width",
    "height",
    "decimals",
    "symbol",
}
_COLUMN_KEYS = {"name", "type", "format", "width", "style", "description"}

_STYLE_DESC = (
    "CSS-like style, e.g. 'font-weight: bold; color: #FFFFFF; background-color: #1F4E79; "
    "text-align: center'. Properties: color, background-color, font-family, font-size, "
    "font-weight, font-style, text-decoration, text-align, vertical-align, white-space, "
    "border, border-color, number-format."
)

_CELL_SCHEMA: dict[str, Any] = {
    "description": (
        'A cell: a string, number, boolean or null; or an object. Use {"formula": '
        '"SUM(B2:B5)"} for formulas (A1 references; row 1 is the header row), '
        '{"url": "https://...", "text": "label"} for links, or {"value": ..., '
        '"type": ..., "format": ..., "style": ...} for a typed or styled value.'
    ),
    "anyOf": [
        {"type": "string"},
        {"type": "number"},
        {"type": "boolean"},
        {"type": "null"},
        {
            "type": "object",
            "properties": {
                "value": {"description": "The cell value."},
                "formula": {"type": "string", "description": "Formula, e.g. 'SUM(B2:B5)'."},
                "url": {"type": "string", "description": "Hyperlink target."},
                "text": {"type": "string", "description": "Hyperlink label."},
                "type": {"type": "string", "enum": CELL_TYPES},
                "format": {
                    "type": "string",
                    "description": "Excel number format ('#,##0.00', '0.0%') or strftime "
                    "codes for dates ('%Y-%m-%d').",
                },
                "style": {"type": "string", "description": _STYLE_DESC},
                "decimals": {"type": "integer", "description": "Decimals for percent/currency."},
                "symbol": {"type": "string", "description": "Currency symbol (default '$')."},
            },
            "additionalProperties": False,
        },
    ],
}

_OPTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": "Sheet options.",
    "properties": {
        "headers": {"type": "boolean", "description": "Write a header row (default true)."},
        "freeze_row": {"type": "integer", "description": "Rows frozen at the top (default 1)."},
        "freeze_col": {"type": "integer", "description": "Columns frozen at the left (default 0)."},
        "autofilter": {"type": "boolean", "description": "Add filter dropdowns to the header."},
        "header_style": {"type": "string", "description": _STYLE_DESC},
        "row_styles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Styles that alternate down the rows (banding). [] for none.",
        },
        "date_format": {"type": "string"},
        "datetime_format": {"type": "string"},
        "time_format": {"type": "string"},
        "infer_formulas": {
            "type": "boolean",
            "description": "Treat strings starting with '=' as formulas (default true).",
        },
        "adjust_all_col_width": {"type": "boolean", "description": "Auto-size columns."},
    },
    "additionalProperties": True,
}

_COLUMN_SCHEMA: dict[str, Any] = {
    "anyOf": [
        {"type": "string", "description": "Column title."},
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Column title (header text)."},
                "type": {"type": "string", "enum": CELL_TYPES, "description": "Column type."},
                "format": {"type": "string", "description": "Number/date format for the column."},
                "width": {"type": "number", "description": "Width in characters."},
                "style": {"type": "string", "description": _STYLE_DESC},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    ]
}

_SHEET_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Sheet (tab) name, max 31 characters."},
        "columns": {
            "type": "array",
            "items": _COLUMN_SCHEMA,
            "description": "Columns in order. Required when rows are arrays.",
        },
        "rows": {
            "type": "array",
            "description": "Data rows (not including the header). Each row is an array of "
            "cells in column order, or an object keyed by column name.",
            "items": {
                "anyOf": [
                    {"type": "array", "items": _CELL_SCHEMA},
                    {"type": "object", "additionalProperties": _CELL_SCHEMA},
                ]
            },
        },
        "options": _OPTIONS_SCHEMA,
    },
    "required": ["rows"],
    "additionalProperties": False,
}

#: JSON Schema (draft 2020-12 compatible) for a workbook spec.
WORKBOOK_SPEC_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Marmir workbook spec",
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Document title (file properties)."},
        "author": {"type": "string"},
        "description": {"type": "string"},
        "sheets": {"type": "array", "items": _SHEET_SCHEMA, "minItems": 1},
        "options": _OPTIONS_SCHEMA,
    },
    "required": ["sheets"],
    "additionalProperties": False,
}


def normalize_spec(spec: Any) -> dict[str, Any]:
    """Accept shorthand forms and return ``{"sheets": [...], ...}``.

    Shorthands: a JSON string; a single sheet (``{"rows": ..., "columns": ...}``);
    a bare list of row objects.
    """
    if isinstance(spec, (str, bytes)):
        try:
            spec = json.loads(spec)
        except json.JSONDecodeError as exc:
            raise SpecValidationError(
                [f"$: not valid JSON ({exc.msg} at line {exc.lineno})"]
            ) from exc
    if isinstance(spec, list):
        return {"sheets": [{"rows": spec}]}
    if not isinstance(spec, Mapping):
        raise SpecValidationError([f"$: expected an object, got {type(spec).__name__}"])
    spec = dict(spec)
    if "sheets" not in spec and "rows" in spec:
        sheet = {k: spec.pop(k) for k in ("name", "columns", "rows") if k in spec}
        if "options" in spec:
            sheet["options"] = spec.pop("options")
        spec["sheets"] = [sheet]
    return spec


def validate_spec(
    spec: Any,
    *,
    allow_images: bool = True,
    max_cells: int | None = None,
) -> list[str]:
    """Return a list of problems (empty when the spec is valid).

    Each message starts with a JSON path, e.g. ``sheets[0].rows[2][1]: ...``.
    """
    try:
        spec = normalize_spec(spec)
    except SpecValidationError as exc:
        return exc.errors
    errors: list[str] = []
    for key in spec:
        if key not in ("sheets", "options") and key not in _DOC_KEYS:
            errors.append(
                f"$.{key}: unknown property (allowed: title, author, description, sheets, options)"
            )
    _check_options(spec.get("options"), "$.options", errors)
    sheets = spec.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        errors.append("$.sheets: must be a non-empty array of sheets")
        return errors
    total_cells = 0
    for s_index, sheet in enumerate(sheets):
        path = f"sheets[{s_index}]"
        if not isinstance(sheet, Mapping):
            errors.append(f"{path}: expected an object with 'rows'")
            continue
        for key in sheet:
            if key not in ("name", "columns", "rows", "options"):
                errors.append(
                    f"{path}.{key}: unknown property (allowed: name, columns, rows, options)"
                )
        if "name" in sheet and not isinstance(sheet["name"], str):
            errors.append(f"{path}.name: must be a string")
        _check_options(sheet.get("options"), f"{path}.options", errors)
        columns = _check_columns(sheet.get("columns"), f"{path}.columns", errors)
        rows = sheet.get("rows")
        if not isinstance(rows, list):
            errors.append(f"{path}.rows: must be an array of rows")
            continue
        names = [c["name"] for c in columns] if columns is not None else None
        types = {c["name"]: c.get("type") for c in columns} if columns is not None else {}
        infer_formulas = _infer_formulas(spec, sheet)
        for r_index, row in enumerate(rows):
            rpath = f"{path}.rows[{r_index}]"
            if isinstance(row, list):
                if names is None:
                    errors.append(f"{rpath}: array rows need 'columns' on the sheet")
                    continue
                if len(row) > len(names):
                    errors.append(
                        f"{rpath}: has {len(row)} cells but there are {len(names)} columns"
                    )
                items = [
                    (names[i] if i < len(names) else None, i, cell) for i, cell in enumerate(row)
                ]
                total_cells += len(row)
            elif isinstance(row, Mapping):
                if names is not None:
                    unknown = [k for k in row if k not in names]
                    if unknown:
                        errors.append(f"{rpath}: unknown column(s) {unknown}; columns are {names}")
                items = [(k, k, cell) for k, cell in row.items()]
                total_cells += len(row)
            else:
                errors.append(f"{rpath}: a row must be an array or an object")
                continue
            for column, key, cell in items:
                cpath = f"{rpath}[{key!r}]" if isinstance(key, str) else f"{rpath}[{key}]"
                _check_cell(
                    cell,
                    types.get(column) if column is not None else None,
                    cpath,
                    errors,
                    allow_images,
                    infer_formulas,
                )
    if max_cells is not None and total_cells > max_cells:
        errors.append(f"$: {total_cells} cells exceeds the limit of {max_cells}")
    return errors


def _infer_formulas(spec: Mapping[str, Any], sheet: Mapping[str, Any]) -> bool:
    for options in (sheet.get("options"), spec.get("options")):
        if isinstance(options, Mapping) and "infer_formulas" in options:
            return bool(options["infer_formulas"])
    return True


def _check_options(options: Any, path: str, errors: list[str]) -> None:
    if options is None:
        return
    if not isinstance(options, Mapping):
        errors.append(f"{path}: must be an object")
        return
    for key, value in options.items():
        if key not in _OPTION_KEYS:
            errors.append(f"{path}.{key}: unknown option")
            continue
        default = DEFAULTS.get(key)
        if isinstance(default, bool) and not isinstance(value, bool):
            errors.append(f"{path}.{key}: must be true or false")
        elif (
            isinstance(default, int)
            and not isinstance(default, bool)
            and (not isinstance(value, int) or isinstance(value, bool) or value < 0)
        ):
            errors.append(f"{path}.{key}: must be a non-negative integer")
        elif key == "row_styles" and not (
            isinstance(value, str)
            or (isinstance(value, list) and all(isinstance(v, str) for v in value))
        ):
            errors.append(f"{path}.{key}: must be an array of style strings")


def _check_columns(columns: Any, path: str, errors: list[str]) -> list[dict[str, Any]] | None:
    if columns is None:
        return None
    if not isinstance(columns, list):
        errors.append(f"{path}: must be an array")
        return None
    out: list[dict[str, Any]] = []
    for index, column in enumerate(columns):
        cpath = f"{path}[{index}]"
        if isinstance(column, str):
            out.append({"name": column})
            continue
        if not isinstance(column, Mapping) or not isinstance(column.get("name"), str):
            errors.append(f"{cpath}: a column is a string or an object with a string 'name'")
            out.append({"name": f"Column {index + 1}"})
            continue
        for key in column:
            if key not in _COLUMN_KEYS:
                errors.append(f"{cpath}.{key}: unknown column property")
        if "type" in column:
            try:
                field_type_for_name(str(column["type"]))
            except ValueError as exc:
                errors.append(f"{cpath}.type: {exc}")
        if "width" in column and not isinstance(column["width"], (int, float)):
            errors.append(f"{cpath}.width: must be a number")
        out.append(dict(column))
    names = [c["name"] for c in out]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        errors.append(f"{path}: duplicate column names {dupes}")
    return out


def _check_cell(
    cell: Any,
    column_type: str | None,
    path: str,
    errors: list[str],
    allow_images: bool,
    infer_formulas: bool,
) -> None:
    if cell is None or isinstance(cell, (bool, int, float)):
        value: Any = cell
        type_name = column_type
    elif isinstance(cell, str):
        if infer_formulas and cell.startswith("="):
            _check_formula(cell, path, errors)
            return
        value, type_name = cell, column_type
    elif isinstance(cell, Mapping):
        unknown = [k for k in cell if k not in _CELL_KEYS]
        if unknown:
            errors.append(f"{path}: unknown cell properties {unknown}")
        kinds = [k for k in ("value", "formula", "url", "image") if k in cell]
        if len(kinds) != 1:
            errors.append(f"{path}: a cell object needs exactly one of value, formula, url, image")
            return
        if "formula" in cell:
            _check_formula(cell["formula"], path, errors)
            return
        if "url" in cell:
            if not isinstance(cell["url"], str) or not cell["url"]:
                errors.append(f"{path}.url: must be a non-empty string")
            return
        if "image" in cell:
            if not allow_images:
                errors.append(f"{path}.image: images are not allowed here")
            elif not isinstance(cell["image"], str):
                errors.append(f"{path}.image: must be a file path")
            return
        value = cell["value"]
        type_name = cell.get("type", column_type)
    else:
        errors.append(f"{path}: unsupported cell value of type {type(cell).__name__}")
        return
    if value is None or type_name is None:
        return
    try:
        field_type = field_type_for_name(str(type_name))
    except ValueError as exc:
        errors.append(f"{path}.type: {exc}")
        return
    if field_type is ImageFieldType and not allow_images:
        errors.append(f"{path}: images are not allowed here")
        return
    try:
        field_type.coerce(value)
    except (TypeError, ValueError) as exc:
        errors.append(f"{path}: {value!r} is not a valid {field_type.type_name} ({exc})")


def _check_formula(formula: Any, path: str, errors: list[str]) -> None:
    if not isinstance(formula, str) or not formula.strip().lstrip("="):
        errors.append(f"{path}.formula: must be a non-empty string")
        return
    depth = 0
    in_string = False
    for char in formula:
        if char == '"':
            in_string = not in_string
        elif not in_string and char == "(":
            depth += 1
        elif not in_string and char == ")":
            depth -= 1
            if depth < 0:
                break
    if in_string:
        errors.append(f"{path}.formula: unbalanced double quotes in {formula!r}")
    elif depth != 0:
        errors.append(f"{path}.formula: unbalanced parentheses in {formula!r}")


def from_spec(
    spec: Any,
    *,
    allow_images: bool = True,
    base_dir: str | Path | None = None,
    max_cells: int | None = None,
    validate: bool = True,
) -> Any:
    """Build a ``Document`` (first sheet; the rest are children) from a workbook spec.

    Raises ``SpecValidationError`` listing every problem when the spec is invalid.
    ``base_dir`` resolves relative image paths.
    """
    from .document import Document

    spec = normalize_spec(spec)
    if validate:
        errors = validate_spec(spec, allow_images=allow_images, max_cells=max_cells)
        if errors:
            raise SpecValidationError(errors)

    root: Document | None = None
    global_options = dict(spec.get("options") or {})
    for index, sheet in enumerate(spec["sheets"], start=1):
        options = {**global_options, **dict(sheet.get("options") or {})}
        config = Config(options)
        if index == 1:
            for key in _DOC_KEYS:
                if spec.get(key):
                    setattr(config, key, spec[key])
        columns, rows = _sheet_rows(sheet)
        column_types: dict[Any, Any] = {}
        for column in columns:
            name = column["name"]
            if column.get("type"):
                column_types[name] = field_type_for_name(column["type"])
            if column.get("format"):
                config.number_formats = {**config.number_formats, name: column["format"]}
            if column.get("width") is not None:
                config.column_widths = {**config.column_widths, name: column["width"]}
            if column.get("style"):
                config.column_styles = {**config.column_styles, name: column["style"]}
        types_by_name = {c["name"]: c.get("type") for c in columns}
        names = [c["name"] for c in columns]
        built = [
            [
                _build_cell(cell, types_by_name.get(names[i]), base_dir, config)
                for i, cell in enumerate(row)
            ]
            for row in rows
        ]
        document = Document(
            built,
            order=names,
            column_types=column_types or None,
            config=config,
            name=sheet.get("name") or f"Sheet {index}",
        )
        if root is None:
            root = document
        else:
            root.add_child(document)
    assert root is not None
    return root


def _sheet_rows(sheet: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[list[Any]]]:
    raw_columns = sheet.get("columns")
    rows = sheet.get("rows") or []
    if raw_columns is not None:
        columns = [{"name": c} if isinstance(c, str) else dict(c) for c in raw_columns]
    else:
        seen: dict[str, None] = {}
        for row in rows:
            if isinstance(row, Mapping):
                for key in row:
                    seen.setdefault(key, None)
        columns = [{"name": k} for k in seen]
    names = [c["name"] for c in columns]
    out: list[list[Any]] = []
    for row in rows:
        if isinstance(row, Mapping):
            out.append([row.get(name) for name in names])
        else:
            out.append(list(row) + [None] * (len(names) - len(row)))
    return columns, out


def _build_cell(
    cell: Any, column_type: str | None, base_dir: str | Path | None, config: Config
) -> Any:
    if not isinstance(cell, Mapping):
        return cell
    extras = {k: cell[k] for k in ("style", "format") if cell.get(k) is not None}
    if "formula" in cell:
        return FormulaFieldType(str(cell["formula"]), **extras)
    if "url" in cell:
        return URLFieldType(str(cell["url"]), cell.get("text"), **extras)
    if "image" in cell:
        path = Path(str(cell["image"]))
        if base_dir is not None and not path.is_absolute():
            path = Path(base_dir) / path
        return ImageFieldType(str(path), cell.get("width"), cell.get("height"), **extras)
    value = cell.get("value")
    type_name = cell.get("type") or column_type
    if value is None:
        return None
    if type_name is None:
        from .model import figure_out_type

        field_type: type[BaseFieldType] = figure_out_type(value, bool(config.infer_formulas))
    else:
        field_type = field_type_for_name(type_name)
    data = field_type.coerce(value)
    if field_type is PercentFieldType:
        return PercentFieldType(data, decimals=int(cell.get("decimals", 0)), **extras)
    if field_type is CurrencyFieldType:
        return CurrencyFieldType(
            data,
            symbol=str(cell.get("symbol", "$")),
            decimals=int(cell.get("decimals", 2)),
            **extras,
        )
    return field_type(data, **extras)
