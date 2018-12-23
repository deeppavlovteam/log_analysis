from copy import deepcopy

import pandas as pd


def count_groupby(df: pd.DataFrame, group_by: list, report_by: list) -> pd.DataFrame:
    df_columns = deepcopy(group_by)
    df_columns.extend(report_by)
    df_grouped_count = df[df_columns].groupby(group_by).count()
    return df_grouped_count
