# daylio-obsidian-parser (compatibility shim)

This package exists only for backward compatibility.

- Canonical package: `obsidian-daylio-parser`
- Canonical CLI: `obsidian-daylio-parser`
- Legacy CLI kept by this shim: `daylio_to_md`

The shim forwards execution to `obsidian_daylio_parser.__main__.main` and emits a deprecation warning.

## Publish flow

1. Publish the canonical package from the repository root.
2. Publish this shim package from `shim/daylio-obsidian-parser/`.

```bash
cd shim/daylio-obsidian-parser
python -m build
python -m twine upload dist/*
```

