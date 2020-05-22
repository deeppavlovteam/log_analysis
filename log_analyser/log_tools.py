import hashlib
import gzip
from pathlib import Path
from datetime import date

import requests
from maxminddb import open_database
from maxminddb.reader import Reader


GEOLITE_DB_ARC_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz'
GEOLITE_HASH_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.md5'
GEOLITE_DB_PATH = '/home/ignatov/log_stuff/log_analysis/temp/GeoLite2-City.mmdb'
GEOLITE_HASH_PATH = '/home/ignatov/log_stuff/log_analysis/temp/GeoLite2-City.mmdb.md5'


def get_file_md5_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()

    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)

    file_hash = hash_md5.hexdigest()

    return file_hash


class GeoliteDbWrapper:
    def __init__(self) -> None:
        self._dp_arc_url = GEOLITE_DB_ARC_URL
        self._hash_url = GEOLITE_HASH_URL
        self._db_path = Path(GEOLITE_DB_PATH).resolve()
        self._hash_path = Path(GEOLITE_HASH_PATH).resolve()

        self._db_upd_check_date = date.fromtimestamp(0)
        self._db_reader: Reader = open_database(self._db_path)

    def _update_db(self) -> bool:
        return True
        updated = False

        if date.today() > self._db_upd_check_date:
            download_hash = requests.get(self._hash_url).text

            if self._hash_path.is_file():
                with self._hash_path.open('r') as f_hash:
                    current_hash = f_hash.read()
            else:
                current_hash = ''

            if not self._db_path.is_file() or download_hash != current_hash:
                self._db_path.parent.mkdir(exist_ok=True, parents=True)
                dp_arc_request = requests.get(url=self._dp_arc_url)

                with self._db_path.open('wb') as f_db:
                    f_db.write(gzip.decompress(dp_arc_request.content))

                with self._hash_path.open('w') as f_hash:
                    f_hash.write(download_hash)

                self._db_reader = open_database(self._db_path)
                updated = True

            self._db_upd_check_date = date.today()

        return updated

    def get_ip_info(self, ip_address: str):
        self._update_db()
        result = self._db_reader.get(ip_address)
        return result
