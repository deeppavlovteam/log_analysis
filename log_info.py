import re
import gzip
import hashlib
from copy import deepcopy
from pathlib import Path
from multiprocessing import Process, Queue

import pandas as pd

from log_tools import process_df
from log_transformers import convert_str_to_datetime, convert_datetime_to_date
from log_transformers import validate_outer_request, get_resource, get_resource_group
from log_reporters import count_groupby


DEFAULT_CONFIG = {
    'log_dir': '../nginx',
    'pickle_file': 'logs_df.pkl',
    'hashes_file': 'hashes.txt',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': 'access.log*',
    'log_arc_file_name_re_pattern': r'.+\.gz$',
    'log_entry_pattern': r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s(".+?")\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$',
    'log_entry_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                         'time', 'ref', 'app', '_2'],
    'log_dataframe_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                             'time', 'ref', 'app', '_2', 'date', 'outer_request', 'resource', 'resource_group'],
    'filter_match': [],
    'filter_not_match': [{'column': 'request', 'regexp': r'^"GET /.+md5 HTTP.+"$'}],
    'filter_in': [{'column': 'domain', 'values': ['files.deeppavlov.ai']}],
    'filter_not_in': [{'column': 'resource_group', 'values': ['', 'favicon.ico', 'robots.txt', 'sitemap.xml']}],
    'transform': [{'column': 'timestamp', 'transformer': convert_str_to_datetime},
                  {'column': 'date', 'transformer': convert_datetime_to_date},
                  {'column': 'outer_request', 'transformer': validate_outer_request},
                  {'column': 'resource', 'transformer': get_resource},
                  {'column': 'resource_group', 'transformer': get_resource_group}],
    'reports': [{'name': 'resources_download',
                 'group_by': ['date', 'resource_group', 'resource', 'outer_request'],
                 'report_by': ['request'],
                 'rename': {'request': 'requests_number'},
                 'reporter': count_groupby}]
}

home_dir = Path(__file__).resolve().parent
default_config = deepcopy(DEFAULT_CONFIG)


# log data frame update is isolated to separate process because of Pandas memory leaks
def call_update_log_df(config: dict = default_config) -> pd.DataFrame:
    def wrap_with_queue(in_queue: Queue, out_queue: Queue) -> None:
        config_in: dict = in_queue.get()
        out_log_df = update_log_df(config_in)
        out_queue.put(out_log_df)

    q_in = Queue()
    q_out = Queue()

    p = Process(target=wrap_with_queue, args=(q_in, q_out))
    p.start()

    q_in.put(config)
    log_df = q_out.get()

    return log_df


# TODO: add logging
def update_log_df(config: dict) -> pd.DataFrame:
    config = deepcopy(config)

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
            print(f'Processing file {str(log_file)}')
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

    if new_hashes:
        if pickle_file:
            df_log.to_pickle(str(pickle_file))

        if hashes_file:
            hashes.extend(new_hashes)
            with hashes_file.open('w') as f:
                f.write('\n'.join(hashes))

    return df_log


def make_reports(df: pd.DataFrame, config: dict = default_config) -> None:
    reports_dir = Path(home_dir, config['reports_dir']).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    for report_config in config['reports']:
        report_name = report_config['name']
        group_by = report_config['group_by']
        report_by = report_config['report_by']
        rename: dict = report_config['rename']
        reporter = report_config['reporter']

        df_report: pd.DataFrame = reporter(df, group_by, report_by)

        if rename:
            df_report.rename(index=str, columns=rename, inplace=True)

        report_file = reports_dir / f'{report_name}.csv'
        df_report.to_csv(str(report_file))

        print(f'Generated report {report_file}')
