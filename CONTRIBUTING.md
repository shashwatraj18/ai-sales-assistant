# Contributing

Thanks for considering a contribution to the AI Sales Analytics Dashboard.

## Setup

```bash
git clone <your-fork-url>
cd ai-sales-analytics-dashboard
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python etl/generate_data.py
python etl/load.py
```

## Workflow

1. Open an issue describing the change before starting significant work.
2. Create a branch off `main`: `git checkout -b feature/short-description`.
3. Keep functions small and typed; run the checks below before opening a PR.
4. Write or update tests for any behavior change.
5. Open a pull request with a clear description of what changed and why.

## Checks

```bash
ruff check .
mypy .
pytest
```

## Code style

- Type hints and docstrings on every public function.
- No function much over 50 lines - extract a helper instead.
- New business logic goes in `analytics/`, `forecasting/`, or `ai/`, not in
  `streamlit_app.py` - that file should only orchestrate.

## Reporting bugs / requesting features

Please use the issue templates under `.github/ISSUE_TEMPLATE/`.
