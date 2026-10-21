"""``DjangoGrid``: reads attribute values from model instances."""

from __future__ import annotations

import logging
from typing import Any

from mm.grid import GridBase
from mm.types import BaseFieldType, NoneFieldType, StringFieldType

log = logging.getLogger(__name__)

__all__ = ["DjangoGrid"]


class DjangoGrid(GridBase):
    def populate(self, indata: Any, config: Any = None) -> None:
        names = getattr(self.data_model, "field_names", self.titles)
        self.grid_data = []
        for instance in indata.iterator() if hasattr(indata, "iterator") else indata:
            row: list[BaseFieldType] = []
            for col_id, name in enumerate(names):
                value = getattr(instance, name)
                if value is None:
                    row.append(NoneFieldType())
                    continue
                field_type = self.headers[col_id]
                if hasattr(value, "_meta"):  # related object
                    value = str(value)
                try:
                    row.append(field_type.from_value(value))
                except (TypeError, ValueError):
                    row.append(StringFieldType.from_value(value))
            self.grid_data.append(row)
        self.row_count = len(self.grid_data)
        log.debug("populated grid %sx%s", self.row_count, self.col_count)
