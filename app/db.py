from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app import config

# DB column -> DureVie column, so the ported report logic runs unchanged.
COLUMN_MAP = {
    "artist": "artiste",
    "project_type": "type_projet",
    "project": "projet",
    "activity": "activite",
    "category": "categorie_budgetaire",
    "comment": "commentaires",
    "forecast_artist": "prevision_artiste",
    "forecast_label": "prevision_ddv",
    "forecast_date": "prevision_date",
    "actual_artist": "reel_artiste",
    "actual_label": "reel_ddv",
    "actual_date": "reel_date",
}


def connect(**kwargs) -> psycopg.Connection:
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, **kwargs)


def init_schema() -> None:
    with connect() as conn:
        conn.execute((Path(__file__).parent / "schema.sql").read_text())
