import json
import re
from datetime import datetime
from logging import getLogger
from pathlib import Path

from deeppavlov.download import get_config_downloads
from packaging import version
from pandas import DataFrame, read_pickle
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from db.models import Base, Record, Hash, Config

log = getLogger(__name__)


def get_session(user: str, password: str, host: str, dbname: str) -> Session:
    db_uri = f'postgresql://{user}:{password}@{host}/{dbname}'
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    return session_maker()


class DBManager:
    def __init__(self, session: Session):
        self._session = session

    def load_pkl(self, path_to_pkl: str, path_to_hashes: str) -> None:
        '''Loads pkl file with old db (before 05.19)'''
        with open(path_to_hashes, 'r') as file:
            new_hashes = file.read().split()
            old_hashes = set(h for h, in self._session.query(Hash.hash))
            if not new_hashes:
                log.error(f'There is no hashes in {path_to_hashes}.')
                return
            elif len(new_hashes) != len(set(new_hashes)):
                log.error(f'There is some duplicated hashes in {path_to_hashes}.')
                return
            elif set(new_hashes) & old_hashes:
                log.error(f'There is some hashes that already in database')
                return
        records_added = 0
        df: DataFrame = read_pickle(path_to_pkl)
        pattern = re.compile('"GET (.*) HTTP.*')
        conf_pat = re.compile('(.*)\?config=(.*)')
        some_pat = re.compile('(.*)\?(.*)')
        for _, row in df.iterrows():
            req = pattern.findall(row['request'])
            if not req:
                continue
            elif len(req) != 1:
                log.error(f'Wrong request! {row["request"]}')
                raise ValueError(row['request'])
            else:
                req = req[0]
            config = None
            parts = conf_pat.findall(req)
            if parts:
                if len(parts) > 1:
                    log.error(f'Wrong parts {parts}')
                    raise ValueError('Wrong parts')
                req = parts[0][0]
                config = parts[0][1]
            else:
                parts = some_pat.findall(req)
                if parts:
                    if len(parts) > 1:
                        log.error(f'Wrong parts {parts}')
                        raise ValueError('Wrong parts')
                    req = parts[0][0]
                    if parts[0][1].find('=') == -1:
                        config = parts[0][1]
            if req.endswith('.md5'):
                continue
            rec = Record(
                ip_from=row['ip_from'],
                timestamp=row['timestamp'],
                file=req,
                config=config,
                response_code=row['response_code'],
                bytes=row['bytes'],
                ref=row['ref'],
                app=row['app'],
                forwarded_for=row['_2'],
                outer_request=row['outer_request'],
                country=row['country_from'],
                city=row['city_from']
            )
            self._session.add(rec)
            records_added += 1
        for hash in new_hashes:
            hash_db = Hash(hash=hash)
            self._session.add(hash_db)
        self._session.commit()
        log.info(f'Successfully added {records_added} records and {len(new_hashes)} hashes')

    def update_configs(self, conf_path: str, dp_version: str):
        conf_path = Path(conf_path).resolve()

        def get_files(path: Path, conf_type=None):
            if path.is_dir():
                for file in path.iterdir():
                    get_files(file, conf_type or file.name)
            if path.suffix == '.json':
                with open(str(path), 'r') as file:
                    data = json.loads(file.read())
                    files = [item[0].replace('http://files.deeppavlov.ai', '') for item in get_config_downloads(data)]
                    if not files:
                        return
                    candidate = Config(
                        name=path.name.replace('.json', '').replace('-', '_'),
                        type=conf_type,
                        dp_version=dp_version,
                        files=files
                    )
                    add = True
                    for config in self._session.query(Config).filter_by(name=candidate.name).all():
                        if set(config.files) == set(candidate.files):
                            if version.parse(config.dp_version) < version.parse(candidate.dp_version):
                                config.dp_version = candidate.dp_version
                                if config.type != candidate.type:
                                    config.type = candidate.type
                                    log.info(f'Updated {config.name} type')
                                self._session.add(config)
                                log.info(f'Updated {config.name} version to {config.dp_version}')
                            add = False
                    if add:
                        self._session.add(candidate)

        get_files(conf_path)
        self._session.commit()

    @staticmethod
    def _parse_time(time_str: str):
        try:
            time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        return time


if __name__ == '__main__':
    sess = get_session('nginx', 'nginx', '0.0.0.0:5432', 'nginx_logs')
    manager = DBManager(sess)
#    manager.load_pkl('/home/ignatov/log_stuff/log_analysis/logs_df_processed.pkl', '/home/ignatov/log_stuff/log_analysis/raw_hashes.txt')
#    manager.update_configs('/home/ignatov/dev/DeepPavlov/deeppavlov/configs', '0.1.6')
