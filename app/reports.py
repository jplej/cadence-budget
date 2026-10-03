import pandas as pd

from app import db, logic, schema

SOURCE_COLS = ["source_file_name", "source_sheet", "source_row"]


def load_cleaned(cutoff: str) -> pd.DataFrame | None:
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(list(db.COLUMN_MAP) + SOURCE_COLS)} FROM budget_line_raw ORDER BY id"
        ).fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows).rename(columns=db.COLUMN_MAP)
    for col in [schema.PREVISION_ARTISTE, schema.PREVISION_DDV, schema.REEL_ARTISTE, schema.REEL_DDV]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
    return logic.clean_budget_data(df, cutoff)


def _sort_by_cashflow_sign(df: pd.DataFrame) -> pd.DataFrame:
    # Ported from DureVie presentation_layer: revenues first, then expenses, per artist/type.
    if df.empty:
        return df
    df = df.copy()
    date_columns = [c for c in df.columns if c not in schema.PIVOT_INDEX]
    df["total_amount"] = df[date_columns].apply(pd.to_numeric, errors="coerce").sum(axis=1, skipna=True)
    df["sort_key"] = df["total_amount"].apply(lambda x: 0 if pd.isna(x) or x == 0 else (1 if x < 0 else 0))
    df = df.sort_values([schema.ARTISTE, schema.TYPE_PROJET, "sort_key", "total_amount"], ascending=[True, True, True, False])
    return df.drop(columns=["total_amount", "sort_key"])


def display_name(artist: str) -> str:
    return artist.removesuffix("_BUDGETS").replace("-", " ").strip("_").title()


def _num(v) -> float:
    return 0.0 if v == "" or v is None or pd.isna(v) else float(v)


def _artist_cards(cleaned: pd.DataFrame, cutoff: str) -> list[dict]:
    summary = logic.artist_project_summary(cleaned, cutoff)
    projects = cleaned[cleaned[schema.TYPE_PROJET] != schema.TYPE_FIXE]
    types = projects.groupby(schema.ARTISTE)[schema.TYPE_PROJET].unique()
    cards = []
    for row in summary.to_dict("records"):
        if row["artiste"] == "TOTAL":
            continue
        cards.append({
            "artist": row["artiste"],
            "name": display_name(row["artiste"]),
            "types": ", ".join(sorted(types.get(row["artiste"], []))),
            "revenus": _num(row["total_revenus"]),
            "depenses": -_num(row["total_depenses"]),
            "net": _num(row["total_net"]),
        })
    return sorted(cards, key=lambda c: c["net"], reverse=True)


def home(cutoff: str) -> dict | None:
    cleaned = load_cleaned(cutoff)
    if cleaned is None:
        return None
    return {"grand_total": logic.grand_total_report(cleaned), "cards": _artist_cards(cleaned, cutoff)}


def cashflow(cutoff: str) -> dict | None:
    cleaned = load_cleaned(cutoff)
    if cleaned is None:
        return None
    return logic.cashflow_report(cleaned)


def artist(cutoff: str, name: str) -> dict | None:
    cleaned = load_cleaned(cutoff)
    if cleaned is None:
        return None
    card = next((c for c in _artist_cards(cleaned, cutoff) if c["artist"] == name), None)
    lines = cleaned[cleaned[schema.ARTISTE] == name]
    projects = sorted(lines[lines[schema.TYPE_PROJET] != schema.TYPE_FIXE][schema.PROJET].dropna().astype(str).unique())
    artist_amounts = pd.concat([lines[schema.PREVISION_ARTISTE], lines[schema.REEL_ARTISTE]]).fillna(0)
    return {
        "card": card,
        "projects": projects,
        "has_artist_share": bool((artist_amounts != 0).any()),
        **_pivot(cleaned, cutoff, fixe=False, artist=name),
    }


def budget_pivot(cutoff: str, fixe: bool, artist: str | None = None) -> dict | None:
    cleaned = load_cleaned(cutoff)
    if cleaned is None:
        return None
    return _pivot(cleaned, cutoff, fixe, artist)


def _pivot(cleaned: pd.DataFrame, cutoff: str, fixe: bool, artist: str | None = None) -> dict:
    main = logic.main_budget_report(cleaned, cutoff).reset_index()
    is_fixe = main[schema.TYPE_PROJET] == schema.TYPE_FIXE
    main = _sort_by_cashflow_sign(main[is_fixe] if fixe else main[~is_fixe])
    artists = sorted(main[schema.ARTISTE].dropna().unique())
    if artist:
        main = main[main[schema.ARTISTE] == artist]
    months = [c for c in main.columns if c not in schema.PIVOT_INDEX]
    status = {}
    if not fixe:
        st = logic.status_budget_report(cleaned, cutoff, schema.DATA_TYPE_PROJECT)
        status = {(*idx, m): v for idx, row in st.iterrows() for m, v in row.items() if isinstance(v, str)}
    sections = [(f"{display_name(a)} · {t}", g) for (a, t), g in main.groupby([schema.ARTISTE, schema.TYPE_PROJET], sort=False)]
    return {"pivot": main, "months": months, "status": status, "sections": sections, "artists": artists}


def lines(cutoff: str, artist: str | None = None, project_type: str | None = None) -> dict | None:
    cleaned = load_cleaned(cutoff)
    if cleaned is None:
        return None
    artists = sorted(cleaned[schema.ARTISTE].dropna().unique())
    if artist:
        cleaned = cleaned[cleaned[schema.ARTISTE] == artist]
    if project_type:
        cleaned = cleaned[cleaned[schema.TYPE_PROJET] == project_type]
    cols = [schema.ARTISTE, schema.TYPE_PROJET, schema.PROJET, schema.CATEGORIE, schema.COMMENTAIRES,
            schema.PREVISION_DDV, schema.PREVISION_DATE, schema.REEL_DDV, schema.REEL_DATE,
            schema.AMOUNT, schema.STATUT] + SOURCE_COLS
    return {"lines": cleaned[cols], "artists": artists}
