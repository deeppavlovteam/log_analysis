import re
import gzip
import hashlib
from copy import deepcopy
from pathlib import Path
from multiprocessing import Process, Queue

import pandas as pd



DEFAULT_CONFIG = {
    'log_dir': '../nginx',
    'pickle_file': 'logs_df.pkl',
    'hashes_file': 'hashes.txt',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': 'access.log*',
    'log_arc_file_name_re_pattern': r'.+\.gz$',
    'log_source_pattern': r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s(".+?")\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$',
    'log_source_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                          'bytes', 'ref', 'app', '_2'],
    'log_dataframe_columns': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                              'bytes', 'ref', 'app', '_2', 'date', 'outer_request', 'resource', 'resource_group'],
    'filter_match': [],
    'filter_not_match': [{'column': 'request', 'regexp': r'^"GET /.+md5 HTTP.+"$'}],
    'filter_in': [{'column': 'domain', 'values': ['files.deeppavlov.ai']}],
    'filter_not_in': [{'column': 'resource_group', 'values': ['', 'favicon.ico', 'robots.txt', 'sitemap.xml',
                                                              'vemgmtss.html']}],
    'transform': [{'column': 'timestamp', 'transformer': convert_str_to_datetime},
                  {'column': 'date', 'transformer': convert_datetime_to_date},
                  {'column': 'outer_request', 'transformer': validate_outer_request},
                  {'column': 'resource', 'transformer': get_resource},
                  {'column': 'resource_group', 'transformer': get_resource_group}]
}


# TODO: add logging
class LogDataFrame:
    def __init__(self, config: dict, df: pd.DataFrame = None) -> None:
        self._config = deepcopy(config)
        self._df: pd.DataFrame
        self._hashes: list

        config_df_columns: list = self._config['log_dataframe_columns']
        home_dir = Path(__file__).resolve().parent
        pickle_file = Path(home_dir, config['pickle_file']).resolve() if config['pickle_file'] else None
        hashes_file = Path(home_dir, config['hashes_file']).resolve() if config['hashes_file'] else None

        if df:
            df_columns = list(df.columns)
            if set(df_columns) == set(config_df_columns):
                self._df = df
            else:
                raise ValueError(f'Unmatching data frame columns sets\n'
                                 f'\tdata frame columns: {str(df_columns)}\n'
                                 f'\tconfig columns: {str(config_df_columns)}')
        elif pickle_file and pickle_file.is_file():
            self._df = pd.read_pickle(str(pickle_file))
        else:
            print('Created new data frame')
            self._df = pd.DataFrame(columns=config_df_columns)

        if hashes_file and hashes_file.is_file():
            with hashes_file.open('r') as f:
                f_read = f.read()
                self._hashes = f_read.split('\n') if f_read else []
        else:
            self._hashes = []

    @staticmethod
    def _read_file(log_file: Path) -> str:
        if re.fullmatch(r'.+\.gz$', log_file.name):
            with gzip.open(log_file, 'rb') as f:
                log_bytes: bytes = f.read()
                log_str = log_bytes.decode()
        else:
            with log_file.open('r') as f:
                log_str = f.read()

        return log_str

    # TODO: add column names passing to transformer via decorator
    @staticmethod
    def _apply_to_df(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        for df_transformer in config['transform']:
            column = df_transformer['column']
            transformer = df_transformer['transformer']
            df.loc[:, column] = df.apply(transformer, axis=1)

        return df

    @staticmethod
    def _filter_df(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        # further '== True/False' instead of 'is True/False' is for pandas dark magic

        # filter_match
        for df_filter in config['filter_match']:
            column = df_filter['column']
            regexp = df_filter['regexp']
            if column in df.columns:
                df = df[df[column].str.match(regexp) == True]

        # filter_not_match
        for df_filter in config['filter_not_match']:
            column = df_filter['column']
            regexp = df_filter['regexp']
            if column in df.columns:
                df = df[df[column].str.match(regexp) == False]

        # filter_in
        for df_filter in config['filter_in']:
            column = df_filter['column']
            values = df_filter['values']
            if column in df.columns:
                df = df[df[column].isin(values) == True]

        # filter_not_in
        for df_filter in config['filter_not_in']:
            column = df_filter['column']
            values = df_filter['values']
            if column in df.columns:
                df = df[df[column].isin(values) == False]

        return df

    @staticmethod
    def _process_df(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        df = LogDataFrame._apply_to_df(df, config)
        df = LogDataFrame._filter_df(df, config)
        return df

    # log data frame processing is isolated to separate process because of Pandas memory leaks
    def _wrap_process_df(self, df: pd.DataFrame) -> pd.DataFrame:
        def wrap_with_queue(in_queue: Queue, out_queue: Queue) -> None:
            df_in, config_in = in_queue.get()
            df_out = self._process_df(df_in, config_in)
            out_queue.put(df_out)

        q_in = Queue()
        q_out = Queue()

        p = Process(target=wrap_with_queue, args=(q_in, q_out))
        p.start()

        q_in.put((df, self._config))
        processed_df = q_out.get()

        return processed_df

    def _update_from_files(self, log_dir: Path):
        update_files = []

        for log_file in log_dir.glob(self._config['log_file_name_glob_pattern']):
            hash_md5 = hashlib.md5()

            with log_file.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)

            file_hash = hash_md5.hexdigest()

            if file_hash not in self._hashes:
                update_files.append((log_file, file_hash))

        for log_file, file_hash in update_files:
            print(f'Processing file {str(log_file)}')
            log_str = self._read_file(log_file)
            parsed = re.findall(self._config['log_entry_pattern'], log_str, flags=re.MULTILINE)
            if parsed:
                df_parsed = pd.DataFrame(data=parsed, columns=self._config['log_source_fields'])
                df_processed = self._wrap_process_df(df_parsed)

                df_columns = list(self._df.columns)
                df_processed_columns = list(df_processed.columns)

                if set(df_columns) != set(df_processed_columns):
                    raise ValueError(f'Processed data frame columns set {str(df_append_columns)} '
                                     f'is not similar to data frame columns set {str(df_log_columns)}')

                df_log = df_log.append(other=df_append, ignore_index=True)

                new_hashes.append(file_hash)
