import gzip
import hashlib
import json
from datetime import date
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path

import requests
from maxminddb import open_database
from maxminddb.reader import Reader

GEOLITE_DB_ARC_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz'
GEOLITE_HASH_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.md5'
GEOLITE_DB_PATH = '../temp/GeoLite2-City.mmdb'
GEOLITE_HASH_PATH = '../temp/GeoLite2-City.mmdb.md5'


def get_file_md5_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()

    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)

    file_hash = hash_md5.hexdigest()

    return file_hash


class GeoliteDbWrapper:
    def __init__(self, dp_arc_url: str = GEOLITE_DB_ARC_URL,
                 hash_url: str = GEOLITE_HASH_URL,
                 db_path: str = GEOLITE_DB_PATH,
                 hash_path: str = GEOLITE_HASH_PATH) -> None:
        self._dp_arc_url = dp_arc_url
        self._hash_url = hash_url
        self._db_path = Path(db_path).resolve()
        self._hash_path = Path(hash_path).resolve()

        self._db_upd_check_date = date.fromtimestamp(0)
        self._db_reader: Reader = open_database(self._db_path)

    def _update_db(self) -> bool:
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
        result = self._db_reader.get(ip_address)
        return result


class ColabWrapper:
    def __init__(self, cloud_path):
        with open(cloud_path) as fin:
            cloud = json.loads(fin.read())
        self.networks = []
        for net_item in cloud['prefixes']:
            if 'ipv4Prefix' not in net_item:
                continue
            net = IPv4Network(net_item['ipv4Prefix'])
            self.networks.append(net)

    def __call__(self, ip):
        '''Returns true if ip is in any cloud networks, false otherwise.'''
        ip = IPv4Address(ip)
        for net in self.networks:
            if ip in net:
                return True
        return False
