# Output formats and reading files

| Format | Extensions | `writestr()` returns | Sheets | Notes |
| --- | --- | --- | --- | --- |
| `xlsx` (default) | `.xlsx`, `.xlsm` | bytes | all | full styling, formulas, links, images, freeze panes, autofilter |
| `xls` | `.xls` | bytes | all | `marmir[xls]`; 65,536 rows x 256 columns; Excel 97 palette |
| `csv` | `.csv` | str | first | ISO dates, formula-injection guard |
| `tsv` | `.tsv`, `.tab` | str | first | |
| `json` | `.json` | str | all | the [workbook spec](workbook-spec.md) shape, round-trips |
| `markdown` (`md`) | `.md`, `.markdown` | str | all | GitHub tables, `## Sheet` headings, numbers right-aligned |
| `html` | `.html`, `.htm` | str | all | styled `<table>`s; `html_fragment=True` for embedding |
| `text` (`txt`) | `.txt` | str | all | psql-style ASCII tables |

`max_rows=N` truncates the text formats with a "N more rows" note -- useful when a
sheet is going into a prompt: `doc.to_markdown(max_rows=50)`.

The legacy PrettyTable output is still available:

```python
from mm.contrib.prettytable import ComposerPrettyTable
doc.set_composer_class(ComposerPrettyTable)
print(doc.writestr())
```

## Reading

```python
sheets = mm.read("book.xlsx")                    # list[mm.Sheet]
sheets = mm.read(data_bytes, format="csv")
sheets = mm.read("book.xlsx", sheet="Summary", max_rows=100)
sheets = mm.read("book.xlsx", formulas=False)    # cached values instead of formula text
sheet.name, sheet.columns, sheet.rows, sheet.records()

doc = mm.read_document("book.xlsx")              # a Document (extra sheets = children)
```

| Input | Notes |
| --- | --- |
| `.xlsx`/`.xlsm` | date-only cells come back as `date`, formulas as `"=..."` text |
| `.xls` | `marmir[xls]` (xlrd) |
| `.csv`/`.tsv` | delimiter sniffed; numbers parsed; `'=` escapes undone |
| `.json` | workbook specs or lists of records |

Format detection uses the extension, then the content (`PK` zip -> xlsx, OLE -> xls,
`{`/`[` -> JSON, otherwise CSV).
