# 7. Extending Marmir

**Goal:** make Marmir fit your organisation: a reusable house style, custom cell
behaviour, new output formats, and Django models.

```python
import datetime as dt

import mm

orders = [
    {"customer": "Blue Door Cafe", "bags": 40, "margin": 0.31},
    {"customer": "Harbor Bakery", "bags": 12, "margin": -0.04},
    {"customer": "Union Diner", "bags": 75, "margin": 0.27},
]
```

## A house style

Every Acme report should look the same. Subclass `mm.Config` and set defaults as class
attributes; pass an instance to any document:

```python
class AcmeStyle(mm.Config):
    header_style = "color: white; background-color: #6F4E37; font-weight: bold; text-align: center"
    row_styles = ("background-color: #FFFFFF", "background-color: #F5EFE6")
    autofilter = True
    author = "Acme Coffee Finance"
    number_formats = {"margin": "0.0%"}


doc = mm.Document(orders, config=AcmeStyle(), name="Margins")
print(doc.config.autofilter, doc.config.author)
```

Output:

```text
True Acme Coffee Finance
```

Options passed to `Document` still override the house style
(`mm.Document(rows, config=AcmeStyle(), autofilter=False)`).

## Custom cell behaviour: a grid

The grid turns each raw value into a typed cell. Override `make_cell` to apply rules to
every cell -- here, negative margins turn red:

```python
class HighlightNegatives(mm.GridBase):
    def make_cell(self, model, row_id, col_id, value, ignore):
        cell = super().make_cell(model, row_id, col_id, value, ignore)
        if isinstance(cell.data, (int, float)) and not isinstance(cell.data, bool) and cell.data < 0:
            cell.style = "color: #C00000; font-weight: bold"
        return cell


doc = mm.Document(orders, config=AcmeStyle(), grid_class=HighlightNegatives, name="Margins")
print([cell.style for cell in doc.grid.grid_data[1]])
doc.write("margins.xlsx")
```

Output:

```text
[None, None, 'color: #C00000; font-weight: bold']
```

## A new output format: a composer

A composer renders a document. This one writes JSON Lines, one object per row --
a common format for data pipelines and LLM fine-tuning sets:

```python
import json


class ComposerJSONL(mm.ComposerBase):
    format_name = "jsonl"
    media_type = "application/jsonl"

    def run(self, child=None):
        titles = [str(t) for t in self.data_model.field_titles]
        lines = [
            json.dumps(dict(zip(titles, (cell.to_json() for cell in row))))
            for row in self.grid.grid_data
        ]
        return "\n".join(lines) + "\n"


mm.register_composer("jsonl", ComposerJSONL, extensions=(".jsonl",))
doc.write("margins.jsonl")
print(open("margins.jsonl").read())
```

Output:

```text
{"customer": "Blue Door Cafe", "bags": 40, "margin": 0.31}
{"customer": "Harbor Bakery", "bags": 12, "margin": -0.04}
{"customer": "Union Diner", "bags": 75, "margin": 0.27}
```

Registered formats work everywhere: `doc.write("x.jsonl")`, `doc.writestr("jsonl")`,
`marmir convert in.xlsx out.jsonl`.

Cell-by-cell composers can use the classic hooks instead of `run`'s loop:
`write_header()`, `iterate_grid()` (which calls `start_new_row`, `write_cell` and
`end_row`) and `finish()`. Use `mm.composers.base.cell_style(document, row, col, cell)`
and `number_format(...)` to get the same styling decisions as the built-in formats.

## Friendlier headers: a data model

The data model decides the columns. Subclass `mm.DataModel` to change them -- here,
turning `snake_case` keys into readable titles for every report:

```python
from mm.model import MISSING


class TitleCaseModel(mm.DataModel):
    def __init__(self, data, order=None, column_types=None, config=None):
        super().__init__(data, order=order, column_types=column_types, config=config)
        self.keys = list(self.field_titles)                      # what the rows use
        self.field_titles = [str(k).replace("_", " ").title() for k in self.keys]  # what people see

    def value_at(self, row, index):
        # also called during type inference, before self.keys exists
        keys = getattr(self, "keys", self.field_titles)
        return row.get(keys[index], MISSING)


report = mm.Document([{"customer_name": "Union Diner", "bags_ordered": 75}], data_model_class=TitleCaseModel)
print(report.data_model.field_titles, report.rows)
```

Output:

```text
['Customer Name', 'Bags Ordered'] [['Union Diner', 75]]
```

(For a one-off, renaming keys before building the document is simpler; a model class
pays off when many reports share the rule.)

## Django

`pip install "marmir[django]"`. Build sheets from QuerySets using the model's field
definitions:

<!-- skip -->
```python
from mm.contrib.django import DjangoDataModel, DjangoGrid

from shop.models import Order

doc = mm.Document(
    Order.objects.select_related("customer").filter(placed__year=2024),
    data_model_class=DjangoDataModel,
    grid_class=DjangoGrid,
    order=["id", "customer", "placed", "bags", "price"],
    name="2024 orders",
)
doc.write("orders_2024.xlsx")
```

Types come from the field classes (`DateField` -> date, `DecimalField` -> decimal, ...),
foreign keys are written with `str(related)`, and `DjangoDataModel(...,
verbose_names=True)` uses each field's `verbose_name` as the header. In a view, return
`HttpResponse(doc.to_bytes(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`.

## Google Sheets

`pip install "marmir[gsheets]"` and create a Google Cloud service account with the
Sheets and Drive APIs enabled:

<!-- skip -->
```python
sheet = doc.write_gsheet("Acme margins", credentials_file="service-account.json", share_with="ops@acme.example")
print(sheet.url)
```

## Where to go next

- [Concepts](../concepts.md) -- how documents, models, grids and composers fit together.
- [API reference](../api-reference.md).
- [Cookbook](../cookbook.md) -- short recipes for common tasks.
- [Contributing](../../CONTRIBUTING.md) -- add a composer or an integration to Marmir itself.
