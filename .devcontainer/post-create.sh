#!/usr/bin/env bash
set -euo pipefail

# .venv and .tox are named volumes. Give them to user instead of roo
sudo chown vscode:vscode .venv .tox

# The system site-packages directory is root-owned, so install fusesoc into the
# user site
pip install --user -e .

# Build the pre-commit hook environments (black, ruff, mypy, ty, ...)
pre-commit install-hooks

# Only write the git hook file if the checkout doesn't already have one.
if [ ! -e .git/hooks/pre-commit ]; then
    pre-commit install
fi

# Some tests need an initialized FuseSoC library to be present (see tox.ini).
fusesoc library add --global fusesoc_cores https://github.com/fusesoc/fusesoc-cores
