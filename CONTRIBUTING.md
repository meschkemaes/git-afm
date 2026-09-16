# Contributing

Thanks for considering a contribution to **git-afm**.

[English](README.md) · [Português](README.pt.md)

## Setup

You need a Mac with Apple Silicon, Git, Python 3.10+, and Apple Intelligence enabled.

```bash
git clone https://github.com/meschkemaes/git-afm.git
cd git-afm
python3 -m pip install -e ".[dev,mcp]"
```

## Tests

```bash
# Unit tests (no Apple Intelligence required for most of these)
python3 -m pytest tests/ -v -m "not integration"

# On-device integration tests (Apple Intelligence must be available)
python3 -m pytest tests/ -v -m integration
```

Integration tests talk to the real Apple Foundation Models runtime. They skip automatically when the model is unavailable.

## Pull requests

1. Keep the change focused.
2. Add or update tests when behaviour changes.
3. Use [Conventional Commits](https://www.conventionalcommits.org/) for the PR title and commits (`feat:`, `fix:`, `docs:`, …).
4. Run the unit tests before opening the PR.

## Scope

`git-afm` is intentionally small: staged diffs in, structured commits / PR markdown / explanations out, all on-device. Features that require a cloud API or a non-Apple runtime are out of scope.
