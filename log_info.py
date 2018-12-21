import re
import gzip
import hashlib
from pathlib import Path

import pandas as pd

from log_tools import process_df
from log_transformers import convert_to_datetime, validate_outer_request, get_resource, get_resource_group


DEFAULT_CONFIG = {
    'log_dir': '../nginx_t',
    'pickle_file': 'logs_df.pkl',
    'hashes_file': 'hashes.txt',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': 'access.log*',
    'log_arc_file_name_re_pattern': r'.+\.gz$',
    'log_entry_pattern': r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s(".+?")\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$',
    'log_entry_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                         'time', 'ref', 'app', '_2'],
    'log_dataframe_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                             'time', 'ref', 'app', '_2', 'outer_request', 'resource', 'resource_group'],
    'filter_match': [],
    'filter_not_match': [{'column': 'request', 'regexp': r'^"GET /.+md5 HTTP.+"$'}],
    'filter_in': [{'column': 'domain', 'values': ['files.deeppavlov.ai']}],
    'filter_not_in': [{'column': 'resource_group', 'values': ['', 'favicon.ico', 'robots.txt', 'sitemap.xml']}],
    'transform': [{'column': 'timestamp', 'transformer': convert_to_datetime},
                  {'column': 'outer_request', 'transformer': validate_outer_request},
                  {'column': 'resource', 'transformer': get_resource},
                  {'column': 'resource_group', 'transformer': get_resource_group}]
}

home_dir = Path(__file__).resolve().parent


# TODO: add logging
def update_log_df(config: dict) -> pd.DataFrame:
    log_dir = Path(home_dir, config['log_dir']).resolve()
    pickle_file = Path(home_dir, config['pickle_file']).resolve() if config['pickle_file'] else None
    hashes_file = Path(home_dir, config['hashes_file']).resolve() if config['hashes_file'] else None

    if not log_dir.is_dir():
        raise FileNotFoundError(f'No source log dir found {str(log_dir)}')

    if pickle_file and pickle_file.is_file():
        df_log = pd.read_pickle(str(pickle_file))
    else:
        df_log = pd.DataFrame(columns=config['log_dataframe_fields'])

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
            df_parsed = pd.DataFrame(data=parsed, columns=config['log_entry_fields'])
            df_append = process_df(df_parsed, config)

            df_log_columns = list(df_log.columns)
            df_append_columns = list(df_append.columns)

            if set(df_log_columns) != set(df_append_columns):
                raise ValueError(f'Processed data frame columns set {str(df_append_columns)} '
                                 f'is not similar to data frame columns set {str(df_log_columns)}')

            df_log = df_log.append(other=df_append, ignore_index=True)

            new_hashes.append(file_hash)

    df_log.drop_duplicates(inplace=True)

    # TODO: unreachable for maintenance
    if new_hashes and False:
        if pickle_file:
            df_log.to_pickle(str(pickle_file))

        if hashes_file:
            hashes.extend(new_hashes)
            with hashes_file.open('w') as f:
                f.write('\n'.join(hashes))

    return df_log
