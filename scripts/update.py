import logging
from pathlib import Path
from datetime import date

from log_analyser.log_dataframe import LogDataFrame
from log_analyser.log_configs import RAW_FILES_LOG_CONFIG, PROCESSED_FILES_LOG_CONFIG


REPORT_BEGIN_DATE = date(year=2017, month=1, day=1)
REPORT_END_DATE = date(year=2020, month=12, day=31)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

log_file_path = Path('./log_update.log').resolve()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

file_handler = logging.FileHandler(filename=log_file_path, mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def make_report() -> None:
    log_ldf = LogDataFrame(PROCESSED_FILES_LOG_CONFIG)
    df_log = log_ldf.df()

    df_log_filtered = df_log[(df_log['date'] >= REPORT_BEGIN_DATE) &
                             (df_log['date'] <= REPORT_END_DATE) &
                             (df_log['response_code'] == '200')]

    report_columns = ['date', 'resource_group', 'resource', 'outer_request', 'country_from', 'city_from', 'request']
    groupby_columns = ['date', 'resource_group', 'resource', 'outer_request', 'country_from', 'city_from']
    df_log_groupby = df_log_filtered[report_columns].groupby(groupby_columns)

    report_path = Path('./reports/resources_download.csv').resolve()
    report_path.parent.mkdir(exist_ok=True)
    df_log_groupby.count().to_csv(report_path, header=True)

    logger.info(f'Done generating reports for period {str(REPORT_BEGIN_DATE)} to {str(REPORT_END_DATE)}')


def update() -> None:
    logger.info('Started updating logs dataframes...')

    raw_ldf = LogDataFrame(RAW_FILES_LOG_CONFIG)
    raw_ldf_upd = raw_ldf.update()
    raw_ldf_upd_rows_count = 0 if raw_ldf_upd is None else raw_ldf_upd.shape[0]

    log_ldf = LogDataFrame(PROCESSED_FILES_LOG_CONFIG)
    log_ldf_upd = log_ldf.update(raw_ldf.df())
    log_ldf_upd_rows_count = 0 if log_ldf_upd is None else log_ldf_upd.shape[0]

    logger.info(f'Finished updating raw logs dataframe with {raw_ldf_upd_rows_count} rows '
                f'and log dataframe with {log_ldf_upd_rows_count} rows')


if __name__ == '__main__':
    update()
    make_report()
