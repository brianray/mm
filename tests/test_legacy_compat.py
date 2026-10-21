"""The Marmir 0.x API keeps working."""

from __future__ import annotations

import datetime as dt

import mm
from mm import color_converter, model_base
from mm.composer_base import ComposerBase
from mm.config_base import ConfigBase
from mm.document_base import Document
from mm.document_writers import DocumentWriter
from mm.grid_base import GridBase
from mm.serializer_base import Serializer
from mm.style_base import StyleBase

from .helpers import sheet_values


def test_legacy_modules():
    assert model_base.IntFieldType in model_base.get_members_list()
    assert model_base.is_custom_mm_type(mm.Date(dt.date.today()))
    assert not model_base.is_custom_mm_type(1)
    assert color_converter.get_closest_rgb_match("#ffffff") == 0x09
    assert Document is mm.Document
    assert issubclass(Document, DocumentWriter)
    assert ComposerBase and GridBase and Serializer and StyleBase and ConfigBase


def test_readme_examples(tmp_path):
    now = dt.datetime.now().replace(microsecond=0)
    my_data = [
        {"msg": "My first Row", "id": 1, "when": now},
        {"msg": "My second Row", "id": 2, "when": now},
    ]
    mm.Document(my_data).write(tmp_path / "example.xls")
    assert (tmp_path / "example.xls").read_bytes()[:4] == b"\xd0\xcf\x11\xe0"

    fancy = [
        {
            "msg": "My first Row",
            "id": 1,
            "when": mm.Date(now, "%Y-%m-%dT%H:%M:%S"),
            "homepage": mm.URL("https://github.com/brianray"),
        },
        {
            "msg": "My second Row",
            "id": 2,
            "when": now,
            "homepage": mm.URL("http://twitter.com/brianray", "Tweet Me"),
        },
    ]
    mm.Document(fancy).write(tmp_path / "fancy.xlsx")
    assert sheet_values((tmp_path / "fancy.xlsx").read_bytes())[2][3] == "Tweet Me"


def test_config_object_and_dict(records):
    config = mm.Config()
    config.headers = False
    doc = mm.Document(records, config=config, config_dict={"freeze_row": 0})
    assert doc.config is config and doc.config.freeze_row == 0


def test_dup_keys(tmp_path):
    data = [{"id dup": 2, "id": 1}, {"id dup": 4, "id": 3}]
    assert sheet_values(mm.Document(data).writestr()) == [["id dup", "id"], [2, 1], [4, 3]]


def test_custom_data_model_without_config_kwarg(records):
    class MyModel(mm.DataModel):
        def __init__(self, data, order=None, column_types=None):
            super().__init__(data, order=["id"], column_types=column_types)

    doc = mm.Document(records, data_model_class=MyModel)
    assert doc.data_model.field_titles == ["id"]


def test_custom_grid_class(records):
    class UpperGrid(mm.GridBase):
        def make_cell(self, model, row_id, col_id, value, ignore):
            cell = super().make_cell(model, row_id, col_id, value, ignore)
            if isinstance(cell.data, str):
                cell.data = cell.data.upper()
            return cell

    assert mm.Document(records, grid_class=UpperGrid).rows[0][0] == "MY FIRST CELL"


def test_grid_requires_attributes():
    import pytest

    with pytest.raises(AttributeError):
        GridBase().populate([], None)


def test_grid_without_model_normalises(records):
    grid = GridBase()
    grid.row_count, grid.col_count, grid.headers, grid.titles = (
        2,
        1,
        [model_base.StringFieldType],
        ["msg"],
    )
    grid.populate(records, mm.Config())
    assert grid.grid_data[1][0].data == "My second Cell"
