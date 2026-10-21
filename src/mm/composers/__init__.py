"""Output formats ("composers") and the registry that maps names/extensions to them."""

from __future__ import annotations

import importlib
import os
from typing import Any

from ..errors import UnsupportedFormatError
from .base import ComposerBase

__all__ = [
    "ComposerBase",
    "available_formats",
    "format_for_path",
    "get_composer_class",
    "register_composer",
]

# name -> "module:Class" (imported lazily so optional dependencies stay optional)
_REGISTRY: dict[str, Any] = {
    "xlsx": "mm.composers.xlsx:ComposerXLSX",
    "xls": "mm.composers.xls:ComposerXLS",
    "csv": "mm.composers.text:ComposerCSV",
    "tsv": "mm.composers.text:ComposerTSV",
    "json": "mm.composers.text:ComposerJSON",
    "markdown": "mm.composers.text:ComposerMarkdown",
    "html": "mm.composers.text:ComposerHTML",
    "text": "mm.composers.text:ComposerText",
}

_ALIASES: dict[str, str] = {
    "excel": "xlsx",
    "md": "markdown",
    "htm": "html",
    "txt": "text",
    "ascii": "text",
}

_EXTENSIONS: dict[str, str] = {
    ".xlsx": "xlsx",
    ".xlsm": "xlsx",
    ".xls": "xls",
    ".csv": "csv",
    ".tsv": "tsv",
    ".tab": "tsv",
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".txt": "text",
}


def register_composer(
    name: str, composer: type[ComposerBase] | str, extensions: tuple[str, ...] = ()
) -> None:
    """Register a custom output format.

    >>> class MyComposer(ComposerBase): ...
    >>> register_composer("mine", MyComposer, extensions=(".mine",))
    """
    key = name.lower()
    _REGISTRY[key] = composer
    for ext in extensions:
        _EXTENSIONS[ext if ext.startswith(".") else "." + ext] = key


def available_formats() -> list[str]:
    """Names of every registered format."""
    return sorted(_REGISTRY)


def normalise_format(name: str) -> str:
    key = name.lower().lstrip(".")
    key = _ALIASES.get(key, key)
    if key not in _REGISTRY:
        raise UnsupportedFormatError(
            f"unknown format {name!r}; available: {', '.join(available_formats())}"
        )
    return key


def get_composer_class(name: str) -> type[ComposerBase]:
    """Return the composer class for a format name such as ``"xlsx"`` or ``"md"``."""
    key = normalise_format(name)
    target = _REGISTRY[key]
    if isinstance(target, str):
        module_name, _, attr = target.partition(":")
        target = getattr(importlib.import_module(module_name), attr)
        _REGISTRY[key] = target
    return target


def format_for_path(path: str | os.PathLike[str]) -> str | None:
    """Guess the format from a file name, or ``None`` if the extension is unknown."""
    ext = os.path.splitext(os.fspath(path))[1].lower()
    return _EXTENSIONS.get(ext)
