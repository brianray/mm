# Migrating from Marmir 0.x

Marmir 2.0 targets Python 3.10+ (0.x was Python 2). The import name is still `mm` and
the core API is unchanged:

```python
import mm
mm.Document(data, order=..., column_types=..., config_dict=...).write("out.xlsx")
mm.Date, mm.URL, mm.Image, mm.Formula, mm.Config
doc.set_name(...); doc.add_child(...); doc.set_composer_class(...); doc.writestr()
```

Legacy modules are kept as aliases: `mm.model_base`, `mm.config_base`,
`mm.document_base`, `mm.document_writers`, `mm.composer_base`, `mm.composer_xls`,
`mm.grid_base`, `mm.serializer_base`, `mm.style_base`, `mm.color_converter`,
`mm.contrib.django.data_model`, `mm.contrib.django.grid`,
`mm.contrib.prettytable.composers`.

## Behaviour changes

| 0.x | 2.0 | To keep the old behaviour |
| --- | --- | --- |
| `writestr()` returned XLS bytes | returns **XLSX** bytes | `writestr("xls")` (`pip install "marmir[xls]"`) |
| `write("x.xls")` ignored the extension | the extension picks the format | -- |
| column types came from the first row only | all rows are scanned, blanks skipped | `infer_rows=1` |
| a later row with extra keys raised | extra keys add columns | `strict_columns=True` |
| missing values were written as `''` | written as blank cells | -- |
| empty data raised | allowed when `order` is given | -- |
| default styles: grey/white rows, red border | white/light-grey banding, navy header | pass the old `header_style`/`row_styles` |
| `write_gdata()` (ClientLogin) | deprecated; forwards to `write_gsheet()` (gspread) | -- |
| vendored xlwt 0.7.2 | `xlwt`/`xlrd` from PyPI (optional) | -- |
| `INGORE_DATA_MISMATCH` | `ignore_data_mismatch` (old name still works) | -- |
| font metrics pickle | JSON | -- |
| `ComposerPrettyTable` only text output | built-in `text`, `markdown`, `html`, `csv`, `json` | PrettyTable composer still available |

## New things worth adopting

- `doc.add_sheet(rows, name=...)` (inherits options), keyword options
  (`mm.Document(rows, autofilter=True)`).
- `mm.Percent`, `mm.Currency`, `mm.Duration`, `mm.Cell(value, style=..., format=...)`.
- DataFrames, DB-API cursors, dataclasses and Pydantic models as input.
- `mm.read()` / `Document.from_file()` to read spreadsheets.
- The [workbook spec](workbook-spec.md) and the [GenAI integrations](integrations/anthropic.md).
