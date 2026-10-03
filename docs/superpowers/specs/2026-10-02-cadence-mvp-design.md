# Cadence MVP — Design

Date: 2026-10-02
Status: draft, awaiting review

## Goal

Rebuild Cadence as a small local web app that shows the DureVie label's budget reports, fed from the same Excel files on Google Drive that the DureVie ETL reads today.

**Done when:** on the dev machine, at the same cutoff date, the Cadence dashboard's grand total and per-artist totals match the current `Budget DureVie - A JOUR.xlsx` report (checked by hand).

## Scope

In:
- Scheduled + on-demand sync of DureVie's `.xlsx` files from a Drive folder into Postgres.
- Four read-only pages mirroring the current Excel report tabs.
- Cutoff date selectable in the UI.

Out (explicitly, for now):
- Deployment, auth, multi-tenancy, sign-up.
- Editing data in the app — spreadsheets stay the source of truth.
- Waterfall payouts, partner splits, charts.
- Excel export — the existing DureVie Render cron keeps producing the `.xlsx` untouched.
- Automated tests.
- The Django `saas-starter/` code — left in place, not used, deleted later.

## Stack

- Python 3.13, `uv`.
- FastAPI + Jinja2 templates + HTMX (from CDN), one small CSS file. No JS build.
- APScheduler (in-process) for the schedule.
- PostgreSQL 16 via `docker compose` (the only container). Plain SQL with `psycopg` 3, no ORM, no migrations tool.
- pandas + openpyxl for Excel parsing; `google-api-python-client` for Drive.

Run locally: `docker compose up -d` then `uv run uvicorn app.web:app --reload`.

## Configuration (`.env`, gitignored)

- `DATABASE_URL`
- `SOURCE` — `drive` or `local`
- `DRIVE_FOLDER_ID` — root folder containing the `*_BUDGETS` artist folders
- `GOOGLE_CREDENTIALS_PATH` — service-account JSON, kept outside the repo
- `LOCAL_SOURCE_DIR` — for the `local` adapter
- `SYNC_INTERVAL_HOURS` — default 12

## Code layout

```
app/
  adapters/
    base.py      # SourceFile dataclass + Source protocol: list_files(), download(file) -> bytes
    drive.py     # Google Drive implementation
    local.py     # local folder implementation, same folder/file conventions
  parsing.py     # ported DureVie parsing: bytes + file metadata -> normalized rows
  sync.py        # sync(): lock, parse, replace rows, record sync_run
  db.py          # connection pool, schema bootstrap, small query helpers
  schema.sql     # tables + lines_at() function
  reports.py     # report queries + monthly pivot (pandas)
  web.py         # FastAPI app, routes, scheduler startup
  templates/     # base.html + one template per page + HTMX partials
  static/style.css
docker-compose.yml   # Postgres only
pyproject.toml
.env.example
```

## Data model

### `sync_run`

| column | type | notes |
|---|---|---|
| id | serial PK | |
| started_at | timestamptz | |
| finished_at | timestamptz | null while running |
| trigger | text | `schedule` or `manual` |
| status | text | `running`, `ok`, `partial`, `failed` |
| files_ok | int | |
| files_failed | int | |
| errors | jsonb | list of `{file, message}`; run-level error uses `file = null` |

### `budget_line_raw`

The normalized fact table: DureVie's 12 standard columns, translated, plus source traceability.

| column | type | DureVie origin |
|---|---|---|
| id | bigserial PK | |
| artist | text | `artiste` (artist folder name) |
| project_type | text | `type_projet`: `spectacle`, `album`, `fixe` |
| project | text | `projet` |
| activity | text | `activite` |
| category | text | `categorie_budgetaire` |
| comment | text | `commentaires` |
| forecast_artist | numeric(12,2) | `prevision_artiste` |
| forecast_label | numeric(12,2) | `prevision_ddv` |
| forecast_date | date | `prevision_date` |
| actual_artist | numeric(12,2) | `reel_artiste` |
| actual_label | numeric(12,2) | `reel_ddv` |
| actual_date | date | `reel_date` |
| source_file_id | text | Drive file ID (or relative path for `local`) |
| source_file_name | text | |
| source_sheet | text | |
| source_row | int | row number in the sheet |
| synced_at | timestamptz | |

Index on `source_file_id`. Sign convention: positive = revenue, negative = expense. Non-numeric amounts become 0, as in DureVie.

### `lines_at(cutoff date)`

SQL function returning every `budget_line_raw` row plus:
- `amount` — `actual_label` if `actual_date` is not null and `<= cutoff`, else `forecast_label`.
- `date` — `actual_date` under the same condition, else `forecast_date`.
- `status` — `forecast` if there's no actual on or before the cutoff (or `actual_label = 0`); `paid` if `forecast_label = 0` or `|actual_label| >= |forecast_label|`; otherwise `partial`.

Only the label amounts (`*_label`) feed reports, matching DureVie. Artist amounts are stored for later use.

## Sync flow

`sync(trigger)` in `app/sync.py`, called by APScheduler every `SYNC_INTERVAL_HOURS` and by `POST /sync`:

1. Take `pg_try_advisory_lock`. If held, return "already running".
2. Insert a `sync_run` row with status `running`.
3. `source.list_files()`, using DureVie's conventions (see `DureVieBudget/STRUCTURE_DRIVE.md`): artist = folder name; type from the `Spectacle` / `Album` / `Fixe` keyword in the file name; album name = text after the first `-`; files without a keyword are skipped; no subfolder recursion. If listing fails, mark the run `failed` and stop — no data is touched.
4. For each file: download, parse, then in one transaction delete that file's rows and insert the new ones. A parse/download error is recorded in `errors` and the file's previous rows are kept.
5. Delete rows whose `source_file_id` is not in the listing (files removed from Drive).
6. Close the run: `ok` if no errors, `partial` if some files failed, `failed` on a run-level error. Release the lock.

Parsing ports DureVie's `data_acquisition.py` logic unchanged in behavior: sheet names `RevenuDepenses`, `Depenses ` and `Revenus ` (trailing spaces), `fixe`; the client template column mapping for album expenses; wide-to-long melt for `fixe`; show name read from the `nom_du_spectacle` column. The parser works on bytes + file metadata and has no Drive dependency.

## Reports

`app/reports.py` runs SQL against `lines_at(:cutoff)` and pivots by month in pandas.

**Month bucketing** (ported as-is from DureVie `utils.create_date_month`, for parity): dates in the cutoff year get one column per month; any date in the previous year goes into one bucket (shown as "≤ Dec <year-1>"); any date in the next year goes into one bucket ("≥ Jan <year+1>"); dates in other years keep their raw date as the bucket — a DureVie quirk that's kept for now and documented on the raw data page.

Report functions, mirroring `DureVieBudget/src/business_logic.py`:
- `grand_total(cutoff)` — revenues (sum of positive amounts), expenses (sum of negative), net; all lines including `fixe`.
- `artist_summary(cutoff)` — per-artist / per-project KPIs as in `artist_project_summary`.
- `cashflow(cutoff)` — net per month by artist and by project type, each with `TOTAL` and `CUMULATIF` rows.
- `project_budget(cutoff, artist=None)` — non-`fixe` lines pivoted by (artist, project type, category) × month, with an aggregated status per cell: all paid → paid, all forecast → forecast, otherwise partial.
- `fixed_budget(cutoff)` — `fixe` lines by category × month.
- `lines(cutoff, filters)` — raw lines with computed amount/status and source columns.

## Pages

A shared layout with a top bar: sync status ("Last sync 14:02 — 23 files OK, 1 failed", linking to the error list), a cutoff date input (default today) and a Refresh button. Changing the cutoff swaps the main table via HTMX (`hx-get` with the cutoff as a query param; URLs stay shareable).

| route | content |
|---|---|
| `GET /` | Dashboard: grand total, artist summary, the two cashflow tables |
| `GET /projects` | Project budget pivot with status colors (yellow forecast, orange partial, green paid) + legend, artist filter |
| `GET /fixed` | Fixed costs pivot |
| `GET /lines` | Raw lines, filter by artist / type, source file + sheet + row per line |
| `GET /sync` | Last runs with per-file errors |
| `POST /sync` | Start a manual sync in a background task; returns the status fragment |

Amounts are formatted French-style (`1 234,56 €`), negatives in red. Labels in the UI are in French (Prévision, Réel, Payé…); code and DB are in English.

## Error handling

- Per-file failures never abort the sync, never delete that file's previous data, and are shown in the UI with file name and reason.
- Drive listing/auth failure: run marked `failed`, all data kept, banner shown in red.
- A stale sync (`running` with no `finished_at` after 1 hour) is shown as failed in the UI; the advisory lock is released automatically when its connection closes.
- Pages render from whatever data is present; an empty DB shows "No data yet — run a sync".

## Acceptance check (manual)

1. Run a sync against the real Drive folder; expect `ok` or `partial` with explained errors.
2. Pick a cutoff date and run the DureVie ETL locally with `--cutoff-date` set to the same date.
3. Compare grand total (revenues, expenses, net) and per-artist totals between the Cadence dashboard and the Excel "Tableau de Bord" tab. They must match to the cent.
