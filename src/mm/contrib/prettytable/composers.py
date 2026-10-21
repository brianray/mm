"""``ComposerPrettyTable``: render a document as a ``prettytable.PrettyTable``."""

from __future__ import annotations

from typing import Any

from mm.composers.base import ComposerBase
from mm.errors import MissingDependencyError

try:
    import prettytable

    pretty_table = True
except ImportError:  # pragma: no cover - depends on environment
    prettytable = None  # type: ignore[assignment, unused-ignore]
    pretty_table = False

__all__ = ["ComposerPrettyTable", "pretty_table"]


class ComposerPrettyTable(ComposerBase):
    """Returns a ``PrettyTable`` (``str()`` it for text). Child sheets are returned as a
    list of tables when present."""

    format_name = "prettytable"

    def write_header(self) -> None:
        self.pt.field_names = [str(t) for t in self.data_model.field_titles]

    def row(self, row: list[Any]) -> None:
        self.pt.add_row([cell.display() for cell in row])

    def run(self, child: Any = None) -> Any:
        if not pretty_table:
            raise MissingDependencyError("prettytable", "prettytable", "PrettyTable output")
        self.pt = prettytable.PrettyTable()
        if self.document.config.headers:
            self.write_header()
        else:
            self.pt.field_names = [str(t) for t in self.data_model.field_titles]
            self.pt.header = False
        self.iterate_grid()
        if not self.document.children:
            return self.pt
        tables = [self.pt]
        for doc in self.document.children:
            tables.append(ComposerPrettyTable(doc.data_model, doc.grid, doc).run())
        return tables
