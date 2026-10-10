# Contributing

Use `main` as the stable branch and open pull requests against `main`. Development
work lives on `dev` or a focused feature branch. Do not commit directly to `main`.

## Set up

Install Python 3.13+ and uv for contributor checks. On Ubuntu install tmux and rsync
so terminal/transfer integration tests run rather than skip:

```bash
sudo apt-get install tmux rsync
uv sync --frozen
```

Docker users can run `docker compose build` and `docker compose run --rm ssh-cred tui`.
Optional command shortcuts are installed only with `./setup.sh` (Docker) or
`./setup.sh --local` after a native installation. Docker runtime does not require
host Python; Python/uv above are for development checks.

To exercise demo servers, copy `.env.example` to `.env`, set `ENV=development`,
and run `docker compose run --rm ssh-cred demo-seed`. Unit tests use temporary
storage and explicit environment fixtures. Never add private keys, passwords,
credential exports, or your `.env` to Git.

## Before committing

```bash
./scripts/check.sh
```

This installs the locked developer dependencies, runs Ruff correctness linting,
validates shell syntax, runs the complete functional suite, and checks whitespace
in staged and unstaged changes. Keep tests independent of actual servers and your
personal credentials. Add regression coverage for changed behavior.

Enable the optional Git hook once per clone to run these checks before every commit:

```bash
git config core.hooksPath .githooks
```

The hook validates working-tree code; stage the intended changes before committing.
CI validates the actual PR commit, so it remains authoritative. Hooks are optional
local helpers; branch protection is the merge enforcement mechanism.

For dependency changes use `uv add` (or `uv add --dev`) and commit both
`pyproject.toml` and `uv.lock`. A stale lockfile fails frozen installation.

## Prepare a pull request

Commit your work, then rebase on current main before opening the PR:

```bash
git fetch origin
git rebase origin/main
./scripts/check.sh
git push -u origin dev
```

After rebasing an already-published personal branch, use `--force-with-lease` only
when needed and coordinate with anyone sharing it. Do not force-push `main`.
Describe the problem, resulting behavior, and tests. Complete the PR template.

## Required CI

Pull requests to `main` run:

- Ruff and functional tests on Python 3.13 and 3.14, including credential CRUD,
  encryption, import/export, CLI behavior, dashboard navigation, keys, themes,
  development gating, rsync, and tmux overflow isolation.
- Shell syntax and an installed-wheel smoke test outside the source checkout.
- Docker build, the full suite inside Docker, and fresh-volume startup/persistence
  smoke checks. Temporary smoke-test volumes are cleaned automatically.

The required **PR stability gate** passes only when every validation job succeeds.
Failed, cancelled, or skipped jobs block merging. Review the Actions logs before
retrying; fix failing tests instead of skipping checks. Run `python3
scripts/docker_smoke.py` after building to reproduce Docker smoke checks locally.
