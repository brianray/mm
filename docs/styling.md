# Cell types, formats and styling

## Styles are CSS

Marmir styles are CSS-like strings, the same in Python, the workbook spec and every
output format (HTML output uses them directly):

```python
mm.Document(
    rows,
    header_style="color: white; background-color: #7030A0; font-weight: bold; text-align: center",
    row_styles=("background-color: #FFFFFF", "background-color: #F3E5F5"),   # banding
    column_styles={"Revenue": "font-family: Courier New"},
)
mm.Cell("Over budget", style="color: #C00000; font-weight: bold")
```

Supported properties:

| Property | Values |
| --- | --- |
| `color`, `background-color` (`background`) | `#RGB`, `#RRGGBB`, `rgb(r, g, b)`, CSS names |
| `font-family` | first family in the list is used |
| `font-size` | `11pt`, `14px`, `12` |
| `font-weight` | `bold`, `normal`, `100`-`900` |
| `font-style` | `italic`, `normal` (`bold` accepted for 0.x compatibility) |
| `text-decoration` | `underline`, `line-through` |
| `text-align` | `left`, `center`, `right`, `justify` |
| `vertical-align` | `top`, `middle`, `bottom` |
| `white-space` / `wrap` | `normal` wraps text, `nowrap` |
| `border` / `border-style` | `thin`, `medium`, `thick`, `dashed`, `dotted`, `double`, `1px solid #ccc` |
| `border-color` | color |
| `number-format` | an Excel number format |

Precedence: alternating row style, then column style, then the cell's own style. Set
`header_style=""` and `row_styles=()` for unstyled output.

In legacy `.xls` output colors snap to the nearest Excel 97 palette entry.

## Number formats

Excel format codes work everywhere (`"#,##0.00"`, `"0.0%"`, `'"$"#,##0'`,
`"yyyy-mm-dd"`). Set them per cell (`format=`), per column (`number_formats=` or the
spec's column `format`) or through types:

| Type | Default format |
| --- | --- |
| `mm.Percent(0.256, decimals=1)` | `0.0%` |
| `mm.Currency(9.5, symbol="€")` | `"€"#,##0.00` |
| dates / datetimes / times | `date_format`, `datetime_format`, `time_format` options |
| durations | `[h]:mm:ss` |

Date types also accept C `strftime` codes, translated to Excel: `mm.Date(d,
"%d %B %Y")` -> `dd mmmm yyyy`. Codes Excel cannot express (`%j`, `%U`, `%z`, ...) raise
`UnsupportedFormatCodeException`.

## Formulas

`mm.Formula("SUM(B2:B9)")` or any string beginning with `=`. Row 1 is the header, so the
first data row is row 2. Formulas are written for the spreadsheet application to
calculate; CSV keeps the formula text. To store text that begins with `=`, use
`infer_formulas=False` or a `string` column type -- Marmir then forces it to be text.

## Links and images

`mm.URL(url, "label")` becomes a clickable hyperlink (HTML output only links `http`,
`https` and `mailto` URLs). `mm.Image(path, width, height)` embeds an image (XLSX needs
`marmir[images]`; XLS accepts BMP, or any format with Pillow installed).

## Column widths

Columns are sized from real per-character font metrics (Arial, Times New Roman,
Verdana, Georgia, Courier New, ... including bold/italic and kerning), clamped by
`min_col_width`/`max_col_width`. Fix widths with `column_widths={"A": 30, "Notes": 50}`.
