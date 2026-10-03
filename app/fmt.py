import datetime as dt

import pandas as pd


def amount(v) -> str:
    if v is None or v == "" or (isinstance(v, float) and pd.isna(v)):
        return ""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{n:,.2f}".replace(",", " ").replace(".", ",")


def is_negative(v) -> bool:
    try:
        return float(v) < 0
    except (TypeError, ValueError):
        return False


def cell(v) -> str:
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return ""
    if isinstance(v, (pd.Timestamp, dt.date)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return amount(v)
    return str(v)


def month_label(col: str, cutoff: str) -> str:
    # DureVie buckets the whole previous year into Dec and the whole next year into Jan.
    year = int(cutoff[:4])
    if col == f"{year - 1}-12":
        return f"≤ {year - 1}"
    if col == f"{year + 1}-01":
        return f"≥ {year + 1}"
    return col
