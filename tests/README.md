# Tests

Automated checks for the parts of this repo that have real logic: the
`docforge.py` template engine, the `tools/new-client.py` generator, and basic
integrity checks on the static site in `docs/`.

No package manager or extra dependencies are required — everything runs on
the Python standard library (`unittest`).

## Run everything

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Or, if `pytest` is installed (optional, same tests, nicer output):

```bash
pytest
```

## What's covered
- `test_docforge.py` — money/date filters, field substitution, conditional
  blocks, and safe filename generation.
- `test_new_client.py` — the client generator stamps the expected files,
  fills in the handoff page and client guide correctly, and the client access
  hub (`docs/clients/index.html`) regenerates from each client's `config.json`.
- `test_static_site.py` — every manifest/config JSON file parses, internal
  page links resolve to real files, and every folder under `docs/clients/`
  has a `config.json`.

These tests never modify tracked files — they use temporary directories for
anything the generator writes.
