import io

import pandas as pd

from app import schema
from app.adapters.base import SourceFile
from app.config import SHEET_NAMES
from app.logic import normalise

ROW = "_source_row"
SHEET = "_source_sheet"


def file_kinds(name: str) -> list[str]:
    # Same case-sensitive keyword matching as DureVie; a file matching none is skipped.
    return [kind for kw, kind in (("Spectacle", "spectacle"), ("Album", "album"), ("Fixe", "fixe")) if kw in name]


def _read(content: bytes, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(content), sheet_name=sheet, engine="openpyxl")
    df = df.dropna(how="all")
    df[ROW] = df.index + 2
    df[SHEET] = sheet
    return df


def _spectacle(content: bytes, file: SourceFile) -> pd.DataFrame:
    df = _read(content, SHEET_NAMES["spectacle"])
    df[schema.ARTISTE] = file.folder_name
    df = normalise(df).copy()
    df[schema.TYPE_PROJET] = schema.TYPE_SPECTACLE
    df[schema.PROJET] = df["nom_du_spectacle"]
    return df


def _album(content: bytes, file: SourceFile, sheet: str) -> pd.DataFrame:
    album = file.name.split("-")[1].split(".xl")[0].strip()
    df = _read(content, sheet)
    df[schema.ARTISTE] = file.folder_name
    df[schema.PROJET] = album
    df = normalise(df).copy()
    df = df.rename(columns={"categorie_depense": schema.CATEGORIE, "sous_caterogie_depense": "classification_artiste"})
    if sheet == SHEET_NAMES["album_expenses"]:
        # DureVie concatenates all files first, so a file without this column loses all its rows.
        df = df.dropna(subset=["classification_artiste"]) if "classification_artiste" in df else df.iloc[0:0]
    df[schema.TYPE_PROJET] = schema.TYPE_ALBUM
    return df


def _parse_fixe_data(df: pd.DataFrame) -> pd.DataFrame:
    date_columns, other_columns = [], []
    for col in df.columns:
        if col in (ROW, SHEET):
            continue
        col_str = str(col).strip()
        if col_str.lower() in ["passé", "passe", "futur"]:
            continue
        try:
            pd.to_datetime(col_str)
            (date_columns if col_str.count("-") >= 2 else other_columns).append(col)
        except Exception:
            other_columns.append(col)
    if not date_columns:
        return pd.DataFrame()
    melted = df.melt(id_vars=other_columns, value_vars=date_columns, var_name="date_column", value_name="amount")
    melted = melted.dropna(subset=["amount"])
    melted = melted[melted["amount"] != 0]
    result = pd.DataFrame()
    if other_columns:
        result[schema.CATEGORIE] = melted[other_columns[0]]
    result[schema.COMMENTAIRES] = melted[other_columns[1]] if len(other_columns) > 1 else ""
    result[schema.PREVISION_DDV] = melted["amount"]
    result[schema.PREVISION_DATE] = pd.to_datetime(melted["date_column"])
    result[schema.REEL_DDV] = melted["amount"]
    result[schema.REEL_DATE] = pd.to_datetime(melted["date_column"])
    result[schema.PREVISION_ARTISTE] = None
    result[schema.REEL_ARTISTE] = None
    result[schema.ACTIVITE] = "operations"
    result[schema.PROJET] = "operations"
    return result


def _fixe(content: bytes, file: SourceFile) -> pd.DataFrame:
    df = _read(content, SHEET_NAMES["fixe"])
    parsed = _parse_fixe_data(df)
    parsed[SHEET] = SHEET_NAMES["fixe"]
    parsed[schema.ARTISTE] = file.folder_name
    df = normalise(parsed).copy()
    df[schema.TYPE_PROJET] = schema.TYPE_FIXE
    return df


def parse_file(content: bytes, file: SourceFile) -> pd.DataFrame:
    frames = []
    for kind in file_kinds(file.name):
        if kind == "spectacle":
            frames.append(_spectacle(content, file))
        elif kind == "album":
            frames.append(_album(content, file, SHEET_NAMES["album_expenses"]))
            frames.append(_album(content, file, SHEET_NAMES["album_revenues"]))
        else:
            frames.append(_fixe(content, file))
    cols = schema.STANDARD_COLUMNS + [ROW, SHEET]
    frames = [f.reindex(columns=cols).astype(object) for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)
