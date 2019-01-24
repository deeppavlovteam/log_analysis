import logging
from pathlib import Path

from log_analyser.log_dataframe import LogDataFrame
from log_analyser.log_configs import RAW_FILES_LOG_CONFIG


def update() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_file_path = Path('./log_update.log').resolve()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    file_handler = logging.FileHandler(filename=log_file_path, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info('Started updating raw logs Dataframe...')

    raw_ldf = LogDataFrame(RAW_FILES_LOG_CONFIG)
    df_upd = raw_ldf.update()
    df_upd_rows_count = 0 if df_upd is None else df_upd.shape[0]

    logger.info(f'Finished updating raw logs Dataframe with {df_upd_rows_count} rows')


if __name__ == '__main__':
    update()
