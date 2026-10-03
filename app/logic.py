# DureVie's report logic, ported unchanged from DureVieBudget/src (docstrings stripped).


import logging
import unicodedata
from typing import Any, List

import pandas as pd

from app import schema


class DataValidationError(Exception):
    pass


def norm_text(text: Any) -> Any:
    if not isinstance(text, str):
        return text
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def normalise(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [norm_text(col) for col in df.columns]
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(norm_text)
    return df

def generate_complete_dates(input_date: str) -> List[pd.Timestamp]:
    input_date = pd.to_datetime(input_date)
    complete_dates = []
    complete_dates.append(pd.Timestamp(year=input_date.year - 1, month=12, day=31))
    for month in range(1, 13):
        complete_dates.append(pd.Timestamp(year=input_date.year, month=month, day=1))
    complete_dates.append(pd.Timestamp(year=input_date.year + 1, month=1, day=1))
    return complete_dates

def create_date_month(date: pd.Timestamp, input_date: pd.Timestamp) -> pd.Timestamp:
    if date.year == input_date.year:
        return pd.Timestamp(year=input_date.year, month=date.month, day=1)
    elif date.year == input_date.year - 1:
        return pd.Timestamp(year=input_date.year - 1, month=12, day=31)
    elif date.year == input_date.year + 1:
        return pd.Timestamp(year=input_date.year + 1, month=1, day=1)
    else:
        return date


def pivot_by_month(df: pd.DataFrame, value_col: str, input_date: str, group_agg, pivot_aggfunc: str='first', fill_value=None) -> pd.DataFrame:
    df = df.copy()
    df[schema.DATE_MONTH] = pd.to_datetime(df[schema.DATE_MONTH]).dt.strftime('%Y-%m')
    grouped = df.groupby(schema.GROUP_KEYS)[value_col].agg(group_agg).reset_index()
    complete_dates = [pd.to_datetime(date).strftime('%Y-%m') for date in generate_complete_dates(input_date)]
    pivoted = grouped.pivot_table(index=schema.PIVOT_INDEX, columns=schema.DATE_MONTH, values=value_col, aggfunc=pivot_aggfunc)
    return pivoted.reindex(columns=complete_dates, fill_value=fill_value)


logger = logging.getLogger('durevie_budget')

def clean_budget_data(df: pd.DataFrame, input_date: str) -> pd.DataFrame:
    required_cols = [schema.PREVISION_DATE, schema.REEL_DATE, schema.PREVISION_DDV, schema.REEL_DDV]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f'Missing required columns: {missing_cols}')
    df = df.copy()
    df[schema.PREVISION_DATE] = pd.to_datetime(df[schema.PREVISION_DATE])
    df[schema.REEL_DATE] = pd.to_datetime(df[schema.REEL_DATE])
    input_date_dt = pd.to_datetime(input_date)
    df[schema.REEL_DDV] = pd.to_numeric(df[schema.REEL_DDV], errors='coerce').fillna(0)
    df[schema.PREVISION_DDV] = pd.to_numeric(df[schema.PREVISION_DDV], errors='coerce').fillna(0)
    df[schema.AMOUNT] = df.apply(lambda row: row[schema.REEL_DDV] if pd.notna(row[schema.REEL_DATE]) and row[schema.REEL_DATE] <= input_date_dt else row[schema.PREVISION_DDV], axis=1)
    df[schema.DATE] = df.apply(lambda row: row[schema.REEL_DATE] if pd.notna(row[schema.REEL_DATE]) and row[schema.REEL_DATE] <= input_date_dt else row[schema.PREVISION_DATE], axis=1)
    df[schema.DATE_MONTH] = df[schema.DATE].apply(lambda x: create_date_month(x, input_date_dt) if pd.notna(x) else None)
    df[schema.STATUT] = df.apply(lambda row: _classify_status(row, input_date_dt), axis=1)
    return df

def _classify_status(row, cutoff) -> str:
    p = row.get(schema.PREVISION_DDV, 0) or 0
    r = row.get(schema.REEL_DDV, 0) or 0
    rd = row.get(schema.REEL_DATE)
    has_actual = pd.notna(rd) and rd <= cutoff and (r != 0)
    if not has_actual:
        return schema.STATUS_FORECAST
    if p == 0 or abs(r) >= abs(p) - 1e-09:
        return schema.STATUS_PAID
    return schema.STATUS_PARTIAL

def _agg_status(series):
    vals = [v for v in series if v]
    if not vals:
        return None
    if all((v == schema.STATUS_PAID for v in vals)):
        return schema.STATUS_PAID
    if all((v == schema.STATUS_FORECAST for v in vals)):
        return schema.STATUS_FORECAST
    return schema.STATUS_PARTIAL

def _filter_by_data_type(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    if data_type == schema.DATA_TYPE_FIXE:
        return df[df[schema.TYPE_PROJET] == schema.TYPE_FIXE].copy()
    if data_type == schema.DATA_TYPE_PROJECT:
        return df[df[schema.TYPE_PROJET] != schema.TYPE_FIXE].copy()
    if data_type == schema.DATA_TYPE_ALL:
        return df.copy()
    raise DataValidationError(f"Invalid data_type: {data_type}. Must be '{schema.DATA_TYPE_ALL}', '{schema.DATA_TYPE_FIXE}', or '{schema.DATA_TYPE_PROJECT}'")

def grand_total_report(cleaned_df: pd.DataFrame) -> dict:
    amount = pd.to_numeric(cleaned_df[schema.AMOUNT], errors='coerce').fillna(0)
    return {'revenus': float(amount[amount > 0].sum()), 'depenses': float(amount[amount < 0].sum()), 'net': float(amount.sum())}

def status_budget_report(cleaned_df: pd.DataFrame, input_date: str, data_type: str='project') -> pd.DataFrame:
    required_cols = schema.GROUP_KEYS + [schema.STATUT]
    missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
    if missing_cols:
        raise DataValidationError(f'Missing required columns: {missing_cols}')
    df = _filter_by_data_type(cleaned_df, data_type)
    return pivot_by_month(df, schema.STATUT, input_date, group_agg=_agg_status)

def main_budget_report(cleaned_df: pd.DataFrame, input_date: str) -> pd.DataFrame:
    required_cols = schema.GROUP_KEYS + [schema.AMOUNT]
    missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
    if missing_cols:
        raise DataValidationError(f'Missing required columns: {missing_cols}')
    pivoted = pivot_by_month(cleaned_df, schema.AMOUNT, input_date, group_agg='sum', pivot_aggfunc='sum')
    return pivoted.replace(0, None)

def comment_budget_report(cleaned_df: pd.DataFrame, input_date: str, data_type: str='all') -> pd.DataFrame:
    required_cols = schema.GROUP_KEYS + [schema.COMMENTAIRES]
    missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
    if missing_cols:
        raise DataValidationError(f'Missing required columns: {missing_cols}')
    df = _filter_by_data_type(cleaned_df, data_type)

    def join_comments(x):
        return '\n'.join([str(c) for c in x.dropna().unique() if str(c).strip()])
    return pivot_by_month(df, schema.COMMENTAIRES, input_date, group_agg=join_comments)

def artist_project_summary(cleaned_df: pd.DataFrame, input_date: str) -> pd.DataFrame:
    required_cols = ['artiste', 'type_projet', 'amount', 'date']
    missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
    if missing_cols:
        raise DataValidationError(f'Missing required columns: {missing_cols}')
    df = cleaned_df.copy()
    input_date_dt = pd.to_datetime(input_date)
    current_year = input_date_dt.year
    df = df[df['date'].dt.year == current_year]
    df = df[df['type_projet'] != 'fixe']
    df['revenus'] = df['amount'].apply(lambda x: x if x > 0 else 0)
    df['depenses'] = df['amount'].apply(lambda x: abs(x) if x < 0 else 0)
    project_types = sorted(df['type_projet'].unique())
    artists = sorted(df['artiste'].unique())
    result = pd.DataFrame({'artiste': artists})
    revenus_data = {}
    depenses_data = {}
    net_data = {}
    ratio_data = {}
    for project_type in project_types:
        project_data = df[df['type_projet'] == project_type]
        revenus_agg = project_data.groupby('artiste')['revenus'].sum().reindex(artists, fill_value=0)
        depenses_agg = project_data.groupby('artiste')['depenses'].sum().reindex(artists, fill_value=0)
        net_agg = revenus_agg - depenses_agg
        ratio_agg = revenus_agg / depenses_agg.replace(0, float('inf'))
        ratio_agg = ratio_agg.replace([float('inf'), -float('inf')], 0)
        revenus_data[f'revenus_{project_type}'] = revenus_agg.values
        depenses_data[f'depenses_{project_type}'] = depenses_agg.values
        net_data[f'net_{project_type}'] = net_agg.values
        ratio_data[f'ratio_{project_type}'] = ratio_agg.values
    for col_name, values in revenus_data.items():
        result[col_name] = values
    revenus_cols = list(revenus_data.keys())
    result['total_revenus'] = result[revenus_cols].sum(axis=1)
    for col_name, values in depenses_data.items():
        result[col_name] = values
    depenses_cols = list(depenses_data.keys())
    result['total_depenses'] = result[depenses_cols].sum(axis=1)
    for col_name, values in net_data.items():
        result[col_name] = values
    net_cols = list(net_data.keys())
    result['total_net'] = result[net_cols].sum(axis=1)
    for col_name, values in ratio_data.items():
        result[col_name] = values
    result['total_ratio'] = result['total_revenus'] / result['total_depenses'].replace(0, float('inf'))
    result['total_ratio'] = result['total_ratio'].replace([float('inf'), -float('inf')], 0)
    for col in result.columns:
        if col != 'artiste' and (not col.startswith('ratio_')) and (col != 'total_ratio'):
            result[col] = result[col].replace(0, '')
    total_row = pd.DataFrame({'artiste': ['TOTAL']})
    for col in result.columns:
        if col != 'artiste':
            if col.startswith('ratio_') or col == 'total_ratio':
                total_revenus_sum = result[col.replace('ratio_', 'revenus_').replace('total_ratio', 'total_revenus')].replace('', 0).sum()
                total_depenses_sum = result[col.replace('ratio_', 'depenses_').replace('total_ratio', 'total_depenses')].replace('', 0).sum()
                if total_depenses_sum != 0:
                    total_row[col] = total_revenus_sum / total_depenses_sum
                else:
                    total_row[col] = ''
            else:
                total_sum = result[col].replace('', 0).sum()
                total_row[col] = total_sum if total_sum != 0 else ''
    result = pd.concat([result, total_row], ignore_index=True)
    return result

def cashflow_report(cleaned_df: pd.DataFrame) -> dict:
    required_cols = ['date_month', 'amount', 'artiste', 'type_projet']
    missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
    if missing_cols:
        raise DataValidationError(f'Missing required columns: {missing_cols}')
    df = cleaned_df.copy()
    df['date_month'] = pd.to_datetime(df['date_month']).dt.strftime('%Y-%m')
    all_months = sorted([month for month in df['date_month'].unique() if pd.notna(month)])
    df = df[pd.notna(df['date_month'])]
    artist_pivot = df.pivot_table(index='artiste', columns='date_month', values='amount', aggfunc='sum', fill_value=0)
    artist_pivot = artist_pivot.reindex(columns=all_months, fill_value=0)
    artist_total = artist_pivot.sum()
    artist_pivot.loc['TOTAL'] = artist_total
    artist_cumulative = artist_total.cumsum()
    artist_pivot.loc['CUMULATIF'] = artist_cumulative
    project_pivot = df.pivot_table(index='type_projet', columns='date_month', values='amount', aggfunc='sum', fill_value=0)
    project_pivot = project_pivot.reindex(columns=all_months, fill_value=0)
    project_total = project_pivot.sum()
    project_pivot.loc['TOTAL'] = project_total
    project_cumulative = project_total.cumsum()
    project_pivot.loc['CUMULATIF'] = project_cumulative
    for df_table in [artist_pivot, project_pivot]:
        df_table.replace(0, '', inplace=True)
    return {'artist_cashflow': artist_pivot, 'project_cashflow': project_pivot}
