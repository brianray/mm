# Security model

Marmir is often driven by model output and, through the HTTP API and MCP server, by
remote callers. These are the guarantees the tool layer (`mm.ai.SpreadsheetTools`, the
MCP server and the HTTP API) provides:

- **Writes are confined to the output directory.** Callers choose a file *name* only;
  directories in `filename` are discarded and the name is sanitised.
- **Reads are confined to an allow-list.** `read_spreadsheet` resolves symlinks and `..`
  and refuses anything outside `read_dirs` (default: the working directory) and the
  output directory, and only opens spreadsheet extensions. The HTTP API only reads
  uploaded files.
- **Images are off by default** in tool contexts, because an image path from a model
  could point anywhere on disk (`allow_images=True` / `--allow-images` to enable).
- **Size limits.** Specs over `max_cells` (250,000 by default) are rejected; HTTP
  uploads are capped at 20 MB.
- **Formula/CSV injection.** Text cells that begin with `=` are forced to be text in
  XLSX when they are typed as strings or `infer_formulas` is off; CSV output prefixes
  text beginning with `=`, `+`, `-`, `@`, tab or CR with an apostrophe
  (`escape_formula_strings`). Note that `infer_formulas` is **on** by default, which is
  what you want when the model authors the sheet; turn it off when rendering untrusted
  third-party data.
- **HTML output** escapes all text and only links `http`, `https` and `mailto` URLs.
- **Errors, not exceptions.** Invalid input returns `{"ok": false, "errors": [...]}`
  rather than stack traces.
- **Authentication.** The HTTP API supports a bearer key (`MARMIR_API_KEY`, compared in
  constant time). The MCP HTTP transports have no built-in auth: keep them on
  localhost or behind an authenticating proxy.
- **No pickle.** Font metrics ship as JSON; nothing is unpickled at runtime.
