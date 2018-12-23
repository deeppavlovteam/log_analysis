from copy import deepcopy
from collections import defaultdict

import pandas as pd


def filter_df(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    applied_filters = defaultdict(list)

    # further '== True/False' instead of 'is True/False' is for pandas dark magic

    # filter_match
    for df_filter in config['filter_match']:
        column = df_filter['column']
        regexp = df_filter['regexp']
        if column in df.columns:
            df = df[df[column].str.match(regexp) == True]
            applied_filters['filter_match'].append(df_filter)

    # filter_not_match
    for df_filter in config['filter_not_match']:
        column = df_filter['column']
        regexp = df_filter['regexp']
        if column in df.columns:
            df = df[df[column].str.match(regexp) == False]
            applied_filters['filter_not_match'].append(df_filter)

    # filter_in
    for df_filter in config['filter_in']:
        column = df_filter['column']
        values = df_filter['values']
        if column in df.columns:
            df = df[df[column].isin(values) == True]
            applied_filters['filter_in'].append(df_filter)

    # filter_not_in
    for df_filter in config['filter_not_in']:
        column = df_filter['column']
        values = df_filter['values']
        if column in df.columns:
            df = df[df[column].isin(values) == False]
            applied_filters['filter_not_in'].append(df_filter)

    for filter_type, df_filers in applied_filters.items():
        for df_filter in df_filers:
            config[filter_type].remove(df_filter)

    return df


# TODO: add column names passing to transformer via decorator
def apply_to_df(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    for df_transformer in config['transform']:
        column = df_transformer['column']
        transformer = df_transformer['transformer']
        df.loc[:, column] = df.apply(transformer, axis=1)

    return df


def process_df(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    config = deepcopy(config)

    df = filter_df(df, config)
    df = apply_to_df(df, config)
    df = filter_df(df, config)

    return df
