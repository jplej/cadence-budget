CREATE TABLE IF NOT EXISTS sync_run (
    id serial PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    trigger text NOT NULL,
    status text NOT NULL DEFAULT 'running',
    files_ok int NOT NULL DEFAULT 0,
    files_failed int NOT NULL DEFAULT 0,
    errors jsonb NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS budget_line_raw (
    id bigserial PRIMARY KEY,
    artist text,
    project_type text,
    project text,
    activity text,
    category text,
    comment text,
    forecast_artist numeric(12,2),
    forecast_label numeric(12,2),
    forecast_date date,
    actual_artist numeric(12,2),
    actual_label numeric(12,2),
    actual_date date,
    source_file_id text NOT NULL,
    source_file_name text NOT NULL,
    source_sheet text,
    source_row int,
    synced_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS budget_line_raw_source_file_id ON budget_line_raw (source_file_id);
