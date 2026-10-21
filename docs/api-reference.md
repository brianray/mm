# API reference

Everything below is importable from `mm` unless a module is named.

## Building and writing

- `Document(data, data_model_class=None, grid_class=None, serializer_class=None, config=None, config_dict=None, order=None, column_types=None, name=None, **options)`
  - `.write(target, format=None)`, `.writestr(format=None)`, `.to_bytes(format="xlsx")`
  - `.to_markdown(max_rows=None)`, `.to_html(max_rows=None)`, `.to_text(max_rows=None)`, `.to_csv()`, `.to_json()`, `.to_spec()`, `.describe(sample_rows=3)`
  - `.rows`, `.columns`, `.to_records()`, `.sheets`, `.children`, `.name`, `.config`, `.data_model`, `.grid`
  - `.add_sheet(data, name=None, **kwargs)`, `.add_child(document)`, `.set_name(name)`
  - `.set_composer_class(cls_or_name)`, `.set_composer(composer)`, `.get_composer(format=None)`
  - `.write_gsheet(title, **kwargs)`, `.write_gdata(...)` (deprecated)
  - `Document.from_spec(spec)`, `Document.from_file(source, format=None)`, `Document.from_cursor(cursor)`
- `write(data, target, format=None, **kwargs)` -- one-liner.
- `Config(config_dict=None, **options)` (alias `ConfigBase`): `.get(key, default)`, `.set_dict(d)`, `.to_dict()`, `.changed()`, `.copy()`; `mm.config.DEFAULTS`.

## Cells

`Cell(value, style=None, format=None)`; aliases `Date`, `DateTime`, `Time`, `Duration`,
`URL`, `Image`, `Formula`, `Number`, `Integer`, `Text`, `Bool`, `Percent`, `Currency`,
`Empty` for the `*FieldType` classes in `mm.types`. Every field type has `type_name`,
`coerce(value)`, `from_value(value, **kw)`, `to_json()`, `display()`, `data`, `style`,
`format`. `mm.types.field_type_for_name(name)`.

## Reading

- `read(source, format=None, *, header=True, sheet=None, max_rows=None, formulas=True) -> list[Sheet]`
- `Sheet(name, columns, rows)`, `.records()`
- `read_document(source, format=None, **kwargs) -> Document`

## Spec

- `WORKBOOK_SPEC_SCHEMA`
- `validate_spec(spec, *, allow_images=True, max_cells=None) -> list[str]`
- `from_spec(spec, *, allow_images=True, base_dir=None, max_cells=None, validate=True) -> Document`
- `mm.spec.normalize_spec(spec)`

## Extending

- `DataModel(data, order=None, column_types=None, config=None)`: `.field_titles`, `.field_headers`, `.table`, `.columns()`; `mm.model.normalize_data`, `mm.model.figure_out_type`
- `GridBase`: `.populate(indata, config)`, `.make_cell(...)`, `.grid_data`; `Serializer`
- `ComposerBase`, `register_composer(name, cls, extensions=())`, `available_formats()`; helpers `mm.composers.base.cell_style`, `number_format`, `header_style`
- `mm.style.parse_style`, `merge_styles`, `Style`; `mm.colors.parse_color`; `mm.formats.to_excel_from_C_codes`; `mm.fonts.get_string_width`

## GenAI (`mm.ai`)

- `SpreadsheetTools(output_dir=None, read_dirs=None, allow_images=False, max_cells=250000, include_base64=False, enable_read=True, preview_rows=5)`
  - `.anthropic_tools()`, `.openai_tools(api="responses"|"chat")`, `.definitions()`
  - `.call(name, arguments)`, `.call_json(name, arguments)`
  - `.handle_anthropic_tool_use(block)`, `.handle_openai_tool_call(call)`
  - `.create_spreadsheet(...)`, `.preview_spreadsheet(...)`, `.read_spreadsheet(...)`
- `anthropic_tools()`, `openai_tools(api)`, `handle_tool_call(name, args)`, `SYSTEM_PROMPT`
- `mm.ai.mcp_server.build_server(tools=None)`, `main(argv)`
- `mm.server.create_app(tools=None, api_key=None, public_url=None)`

## Errors

`MarmirError` > `EmptyDataError`, `DataMismatchError`, `UnsupportedFormatError`,
`SpecValidationError` (`.errors`), `MissingDependencyError`,
`mm.errors.UnsupportedFormatCodeException`.
