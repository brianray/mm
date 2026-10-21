"""Exceptions raised by Marmir."""

from __future__ import annotations


class MarmirError(Exception):
    """Base class for every error Marmir raises on purpose."""


class EmptyDataError(MarmirError, ValueError):
    """Raised when there is no data and no column order to build a sheet from."""


class DataMismatchError(MarmirError, ValueError):
    """Raised when rows do not line up with the columns (see ``Config.strict_columns``)."""


class UnsupportedFormatError(MarmirError, ValueError):
    """Raised when an output or input format is unknown."""


class UnsupportedFormatCodeException(MarmirError, ValueError):
    """Raised when a C ``strftime`` code has no Excel number-format equivalent."""


class SpecValidationError(MarmirError, ValueError):
    """Raised when a workbook spec (the JSON format used by GenAI tools) is invalid.

    ``errors`` holds one human/LLM readable message per problem, each prefixed with a
    JSON path such as ``sheets[0].rows[3]``.
    """

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        summary = "; ".join(self.errors[:10])
        if len(self.errors) > 10:
            summary += f"; ... and {len(self.errors) - 10} more"
        super().__init__(f"Invalid workbook spec: {summary}")


class MissingDependencyError(MarmirError, ImportError):
    """Raised when an optional dependency (extra) is needed but not installed."""

    def __init__(self, package: str, extra: str, feature: str):
        self.package = package
        self.extra = extra
        super().__init__(
            f"{feature} requires the '{package}' package. "
            f"Install it with: pip install 'marmir[{extra}]'"
        )
