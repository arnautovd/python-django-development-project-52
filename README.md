### Hexlet tests and linter status:
[![Actions Status](https://github.com/arnautovd/python-django-development-project-52/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/arnautovd/python-django-development-project-52/actions)

## Development

Install dependencies and create the local database:

```bash
uv sync
uv run python manage.py migrate
```

Start the development server:

```bash
uv run python manage.py runserver
```

Run project checks:

```bash
uv run python manage.py check
uv run ruff check .
```

Local development uses SQLite. Set `DATABASE_URL` in `.env` to use PostgreSQL.

## Render

The `render.yaml` blueprint creates a free web service and PostgreSQL database.
The web service uses Gunicorn and runs migrations and `collectstatic` during the
build.
