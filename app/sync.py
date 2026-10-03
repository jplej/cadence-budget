import logging

import pandas as pd
from psycopg.types.json import Jsonb

from app import db
from app.adapters.base import SourceFile, get_source
from app.parsing import ROW, SHEET, file_kinds, parse_file

log = logging.getLogger("cadence.sync")

LOCK_ID = 7_250_001
TEXT_COLS = ["artist", "project_type", "project", "activity", "category", "comment"]
AMOUNT_COLS = ["forecast_artist", "forecast_label", "actual_artist", "actual_label"]
DATE_COLS = ["forecast_date", "actual_date"]


def _to_records(df: pd.DataFrame, file: SourceFile) -> list[tuple]:
    df = df.rename(columns={v: k for k, v in db.COLUMN_MAP.items()})
    for col in AMOUNT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    for col in TEXT_COLS:
        df[col] = df[col].map(lambda v: None if pd.isna(v) else str(v))
    df[ROW] = pd.to_numeric(df[ROW], errors="coerce")
    df = df.astype(object).where(df.notna(), None)
    return [
        (*(r[c] for c in TEXT_COLS), r["forecast_artist"], r["forecast_label"], r["forecast_date"],
         r["actual_artist"], r["actual_label"], r["actual_date"],
         file.id, file.name, r[SHEET], None if r[ROW] is None else int(r[ROW]))
        for r in df.to_dict("records")
    ]


INSERT = """
INSERT INTO budget_line_raw (artist, project_type, project, activity, category, comment,
    forecast_artist, forecast_label, forecast_date, actual_artist, actual_label, actual_date,
    source_file_id, source_file_name, source_sheet, source_row)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def sync(trigger: str = "manual") -> str:
    with db.connect(autocommit=True) as lock_conn:
        if not lock_conn.execute("SELECT pg_try_advisory_lock(%s) AS ok", (LOCK_ID,)).fetchone()["ok"]:
            return "already running"
        run_id = lock_conn.execute(
            "INSERT INTO sync_run (trigger) VALUES (%s) RETURNING id", (trigger,)
        ).fetchone()["id"]
        errors, ok = [], 0
        try:
            source = get_source()
            files = [f for f in source.list_files() if file_kinds(f.name)]
        except Exception as e:
            log.exception("listing failed")
            errors.append({"file": None, "message": f"{type(e).__name__}: {e}"})
            _finish(lock_conn, run_id, "failed", 0, errors)
            return "failed"

        for file in files:
            try:
                records = _to_records(parse_file(source.download(file), file), file)
                with db.connect() as conn, conn.transaction():
                    conn.execute("DELETE FROM budget_line_raw WHERE source_file_id = %s", (file.id,))
                    with conn.cursor() as cur:
                        cur.executemany(INSERT, records)
                ok += 1
            except Exception as e:
                log.exception("file failed: %s", file.name)
                errors.append({"file": f"{file.folder_name}/{file.name}", "message": f"{type(e).__name__}: {e}"})

        lock_conn.execute(
            "DELETE FROM budget_line_raw WHERE NOT (source_file_id = ANY(%s))", ([f.id for f in files],)
        )
        status = "ok" if not errors else "partial"
        _finish(lock_conn, run_id, status, ok, errors)
        return status


def _finish(conn, run_id: int, status: str, ok: int, errors: list) -> None:
    conn.execute(
        "UPDATE sync_run SET finished_at = now(), status = %s, files_ok = %s, files_failed = %s, errors = %s WHERE id = %s",
        (status, ok, len(errors), Jsonb(errors), run_id),
    )
    conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
