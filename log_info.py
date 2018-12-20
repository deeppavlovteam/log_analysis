import re
import gzip
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict

import pandas as pd

DEFAULT_CONFIG = {
    'log_dir': '../nginx_t',
    'pickle_file': 'logs_df.pkl',
    'hashes_file': 'hashes.txt',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': 'access.log*',
    'log_arc_file_name_re_pattern': r'.+\.gz$',
    'log_entry_pattern': r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s(".+?")\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$',
    'log_entry_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request',
                         'response_code', 'time', 'ref', 'app', '_2'],
    'log_dataframe_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request',
                             'response_code', 'time', 'ref', 'app', '_2', 'internal_request', 'resource'],
    'filter_match': [],
    'filter_not_match': [],
    'filter_in': [{'column': 'ip_from', 'values': ['files.deeppavlov.ai']}],
    'filter_not_in': []
}

home_dir = Path(__file__).resolve().parent


def filter_df(in_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    filters_applied = defaultdict(list)

    out_df = in_df

    # isin
    for df_filter in config['filter_in']:
        column = df_filter['column']
        values = df_filter['values']

        if column in out_df.columns:
            out_df = out_df[out_df[column].isin(values)]
            filters_applied['filter_in'].append(df_filter)

    for filter_type, df_filers in filters_applied.items():
        for df_filter in df_filers:
            config[filter_type].remove(df_filter)

    return out_df


def process_df(in_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    out_df = in_df

    out_df = filter_df(out_df, config)

    return out_df


def update_log_df(config: dict) -> pd.DataFrame:
    log_dir = Path(home_dir, config['log_dir']).resolve()
    pickle_file = Path(home_dir, config['pickle_file']).resolve() if config['pickle_file'] else None
    hashes_file = Path(home_dir, config['hashes_file']).resolve() if config['hashes_file'] else None

    if not log_dir.is_dir():
        raise FileNotFoundError(f'No source log dir found {str(log_dir)}')

    if pickle_file and pickle_file.is_file():
        log_df = pd.read_pickle(str(pickle_file))
    else:
        log_df = pd.DataFrame(columns=config['log_dataframe_fields'])

    if hashes_file and hashes_file.is_file():
        with hashes_file.open('r') as f:
            f_read = f.read()
            hashes = f_read.split('\n') if f_read else []
    else:
        hashes = []

    new_hashes = []

    for log_file in log_dir.glob(config['log_file_name_glob_pattern']):
        hash_md5 = hashlib.md5()

        with log_file.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)

        file_hash = hash_md5.hexdigest()

        if file_hash not in hashes:
            if re.fullmatch(config['log_arc_file_name_re_pattern'], log_file.name):
                with gzip.open(log_file, 'rb') as f:
                    log_bytes: bytes = f.read()
                    log_str = log_bytes.decode()
            else:
                with log_file.open('r') as f:
                    log_str = f.read()

            parsed = re.findall(config['log_entry_pattern'], log_str, flags=re.MULTILINE)
            append_df = pd.DataFrame(data=parsed, columns=config['log_entry_fields'])

            #log_df = process_df(append_df, config)
            log_df = log_df.append(other=append_df, ignore_index=True)

            new_hashes.append(file_hash)

    if new_hashes and False:
        if pickle_file:
            log_df.to_pickle(str(pickle_file))

        if hashes_file:
            hashes.extend(new_hashes)
            with hashes_file.open('w') as f:
                f.write('\n'.join(hashes))

    return log_df
