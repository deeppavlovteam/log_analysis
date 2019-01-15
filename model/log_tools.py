import hashlib
from pathlib import Path
from datetime import date, timedelta
from typing import Union, Tuple

import requests
from maxminddb import open_database
from maxminddb.reader import Reader


GEOLITE_DB_ARC_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz'
GEOLITE_HASH_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.md5'
GEOLITE_ARC_PATH = './temp/GeoLite2-City.mmdb.gz'
GEOLITE_DB_PATH = './temp/GeoLite2-City.mmdb'


def get_file_md5_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()

    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)

    file_hash = hash_md5.hexdigest()

    return file_hash


"""
def _update_geolite_db():
    dp_arc_url = GEOLITE_DB_ARC_URL
    hash_url = GEOLITE_HASH_URL

    arc_path = Path(GEOLITE_ARC_PATH).resolve()
    db_path = Path(GEOLITE_DB_PATH).resolve()

    if db_path.is_file():
        last_mod_date = date.fromtimestamp(db_path.stat().st_mtime)
        if True: #date.today() > last_mod_date:
"""


class _GeoliteDb:
    def __init__(self) -> None:
        self._dp_arc_url = GEOLITE_DB_ARC_URL
        self._hash_url = GEOLITE_HASH_URL
        self._arc_path = Path(GEOLITE_ARC_PATH).resolve()
        self._db_path = Path(GEOLITE_DB_PATH).resolve()

        self._db_updated = date.fromtimestamp(0)
        self._db: Reader

        self._update_db()

    def _update_db(self) -> None:
        if True: #date.today() > self._db_updated:
            download_hash = requests.get(self._hash_url).text

            if not self._db_path.is_file() or download_hash != get_file_md5_hash(self._db_path):
                self._db_path.parent().mkdir(exist_ok=True, parents=True)
                dp_arc_request = requests.get(url=self._dp_arc_url)

                with self._db_path.open('wb') as f:
                    f.write(dp_arc_request)


if __name__ == '__main__':
    dt = date.today()
    tdt = timedelta(days=1)
    print(date.fromtimestamp(0))
    print(dt)
    print(dt + tdt)
    print(requests.get(GEOLITE_HASH_URL).text)
