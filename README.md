# Cadence

> ⚠️ Early alpha — not production ready.

Cadence is an open-source budgeting app for partnership project structures where cashflow is multiyear and traditional accounting doesn't apply. Built for artistic communities, co-productions, and anyone managing shared finances across multiple partners and projects.

## The problem

Standard accounting tools assume a single entity with a clean fiscal year. They break down when:
- Costs and revenues are shared between several partners with negotiated splits
- A project spans multiple years with forecast and realized amounts that evolve over time
- You need to predict cashflow problems months in advance, not just report on what already happened
- Profit distribution follows a waterfall — recoupment before split, variable rules per deal

## What Cadence does

- Track budget lines (forecast vs realized, per partner, per category) across all your projects
- Model cost-sharing splits at the project level with per-line overrides
- Define profit distribution waterfalls per project (recoupment, residual splits)
- Aggregate cashflow across the full portfolio to spot problems before they happen
- Multi-tenant — each organization gets its own isolated workspace

## Stack

- **Backend** — Python 3.13, Django 5.1, Django Ninja (REST API)
- **Database** — PostgreSQL 16 (uses `ltree` for hierarchical project tags)
- **Auth** — Django session auth
- **Deployment** — Docker, Docker Compose

## Development

```bash
git clone https://github.com/your-org/cadence
cd cadence/saas-starter
cp .env.example .env  # fill in DB credentials and SECRET_KEY
docker compose up -d  # starts PostgreSQL
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

API docs at `http://localhost:8000/api/docs`.

## License

MIT
