# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Copyright headers

Every source file starts with the GPL header (copy it from an existing file, e.g.
`fades/main.py`), whose first line is:

    # Copyright YYYY(1)-YYYY(2) Facundo Batista, Nicolás Demarchi

- `YYYY(1)` is the year the file was **created**. Never change it: keep whatever the file
  already has (e.g. `tests/test_main.py` starts in 2015, not 2014). Don't copy it from
  another file when creating a new one.
- `YYYY(2)` is the year of the **last change** to the file. When modifying a file, update
  it to the current year.
- If both years are the same (e.g. a file created this year), use a single year:
  `# Copyright 2026 Facundo Batista, Nicolás Demarchi`.
- New files (test fixtures in `tests/test_files/` included) get the **full** header, not
  just the copyright line.
