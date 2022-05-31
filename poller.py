import json
import re
from datetime import datetime
from pathlib import Path
from shutil import rmtree

from deeppavlov.download import get_config_downloads
from django.db.models import Count
from git import Repo
from packaging import version
from tqdm import tqdm

from log_analyser.log_dataframe import LogDataFrame
from log_analyser.log_tools import GeoliteDbWrapper, ColabWrapper
from log_analyser.log_tools import get_file_md5_hash
from log_analyser.log_transformers import validate_outer_request
from stats.models import Record, Hash, File, Config, ConfigName, IP

file_buffer = {}
config_buffer = {}
ip_buffer = {}

geolite_db_wrapper = GeoliteDbWrapper(db_path='/data/legacy/GeoLite2-City.mmdb',
                                      hash_path='/data/legacy/GeoLite2-City.mmdb.md5')
colab_wrapper = ColabWrapper('/data/legacy/cloud.json')


def get_location(ip_from: str):
    ip_info = geolite_db_wrapper.get_ip_info(ip_from)
    country, city, company = None, None, None
    if isinstance(ip_info, dict):
        try:
            country = ip_info['country']['names']['en']
        except KeyError:
            pass
        try:
            city = ip_info['city']['names']['en']
        except KeyError:
            pass
    if colab_wrapper(ip_from):
        company = 'Google Colab'
    return country, city, company


def add_gz_to_db(path_to_gz: Path):
    hash = get_file_md5_hash(path_to_gz)
    ldf = LogDataFrame({'log_dataframe_columns':['a'], 'log_dir': '', 'pickle_file': '', 'hashes_file': ''})
    lines = ldf._read_file(path_to_gz)
    template = r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s"GET\s(.+?)"\s(.+?)\s(.+?)\s(".*?")\s(".*?")\s(".+?")(.*?)$'
    parsed = re.findall(template, lines, flags=re.MULTILINE)
    creating = []
    for ip_from, domain, _1, timestamp, request, response_code, bytes, ref, app, _2, stat_data in parsed:
        # from 2 april 2021 logs contain token, from april-may 2021 (see releases) logs also contain download
        # session id, file id in download session (countdown) and library version

        token, session_id, file_id, dp_version = [val if val != '-' else None for val in (stat_data.split() + ['-'] * 4)[:4]]
        file_templ = r'^(.+?)[\s\?]'
        config_templ = r'.+?[\?\&]config=(.+?)[\s\&]'
        file_match = re.search(file_templ, request)
        # Assuming that file_match is not None. If it is, we need to get error and look at data
        file_name = file_match.group(1)
        try:
            file = file_buffer[file_name]
        except KeyError:
            try:
                file = File.objects.get(name=file_name)
            except File.DoesNotExist:
                file = File(name=file_name, md5=file_name.endswith('.md5'))
                file.save()
            file_buffer[file_name] = file
        config_match = re.search(config_templ, request)
        config = None
        if config_match is not None:
            config_name = config_match.group(1)
            try:
                config = config_buffer[config_name]
            except KeyError:
                try:
                    config = ConfigName.objects.get(name=config_name)
                except ConfigName.DoesNotExist:
                    config = ConfigName(name=config_name)
                    config.save()
                config_buffer[config_name] = config
        try:
            ip = ip_buffer[ip_from]
        except KeyError:
            try:
                ip = IP.objects.get(ip=ip_from)
            except IP.DoesNotExist:
                contry, city, company = get_location(ip_from)
                ip = IP(ip=ip_from,
                        outer_request=validate_outer_request({'ip_from': ip_from}),
                        country=contry,
                        city=city,
                        company=company)
                ip.save()
                ip_buffer[ip_from] = ip
        try:
            r = Record(ip=ip,
                       time=datetime.strptime(timestamp, '[%d/%b/%Y:%H:%M:%S %z]'),
                       file=file,
                       config=config,
                       response_code=int(response_code),
                       bytes=int(bytes),
                       ref=ref,
                       app=app,
                       forwarded_for=_2,
                       gz_hash=hash,
                       token=token,
                       session_token=session_id,
                       file_number=file_id,
                       dp_version=dp_version)
        except ValueError as e:
            print(ip_from, domain, _1, timestamp, request, response_code, bytes, ref, app, _2)
            raise e
        creating.append(r)
    Record.objects.bulk_create(creating)
    h = Hash(filename=path_to_gz.name, hash=hash)
    h.save()


def update_files():
    File.objects.all().delete()
    stat = Record.objects.filter(response_code=200).values('file').annotate(total=Count('file')) #.order_by('total')
    new_files = [File(name=s['file'], downloads_number=s['total']) for s in stat]
    File.objects.bulk_create(new_files)


def update_configs(conf_path: str, dp_version: str):
    conf_path = Path(conf_path).resolve()
    def get_files(path: Path, conf_type=None):
        if path.is_dir():
            for file in path.iterdir():
                get_files(file, conf_type or file.name)
        if path.suffix == '.json':
            with open(str(path), 'r') as file:
                data = json.loads(file.read())
                try:
                    files = [item[0].replace('http://files.deeppavlov.ai', '') for item in get_config_downloads(data)]
                except FileNotFoundError as e:
                    print(f'{dp_version}\t{path}\n{e}')
                    return
                if not files:
                    return
                name = path.name.replace('.json', '').replace('-', '_')
                if ConfigName.objects.filter(name=name).exists():
                    conf_name = ConfigName.objects.get(name=name)
                else:
                    conf_name = ConfigName(name=name)
                    conf_name.save()
                if Config.objects.filter(name=conf_name).exists():
                    for config in Config.objects.filter(name=conf_name):
                        if version.parse(config.dp_version) < version.parse(dp_version):
                            if set(config.files.values_list('name', flat=True)) == set(files):
                                config.dp_version = dp_version
                                config.type = conf_type
                                config.save()
                            else:
                                for cof in Config.objects.filter(name=conf_name):
                                    if set(cof.files.values_list('name', flat=True)) == set(files):
                                        break
                                else:
                                    new_conf = Config(type=conf_type,
                                                      name=conf_name,
                                                      dp_version=dp_version)
                                    new_conf.save()
                                    for file in files:
                                        try:
                                            fil = File.objects.get(name=file)
                                        except File.DoesNotExist:
                                            fil = File(name=file, md5=file.endswith('.md5'))
                                            fil.save()
                                        new_conf.files.add(fil)
                else:
                    new_conf = Config(type=conf_type,
                                      name=conf_name,
                                      dp_version=dp_version)
                    new_conf.save()
                    for file in files:
                        try:
                            fil = File.objects.get(name=file)
                        except File.DoesNotExist:
                            fil = File(name=file, md5=file.endswith('.md5'))
                            fil.save()
                        new_conf.files.add(fil)

    get_files(conf_path)


def upd_deeppavlov():
    repo_dir = '/tmp/DeepPavlov'
    repo = Repo.clone_from('https://github.com/deepmipt/DeepPavlov', repo_dir, branch='master')
    tags = sorted([t.name for t in repo.tags if version.parse(t.name) >= version.parse('0.2.0')], key=version.parse)
    for t in tqdm(tags):
        repo.git.checkout(t)
        update_configs(conf_path=f'{repo_dir}/deeppavlov/configs', dp_version=t)
    rmtree(repo_dir)


def boo():
    from time import time
    start = time()
    access = sorted([p for p in Path('/data/share/').resolve().glob('files-access.log*.gz')])
    for a in tqdm(access):
        hash = get_file_md5_hash(a)
        if Hash.objects.filter(hash=hash).exists():
            print('skipping file')
            continue
        Record.objects.filter(gz_hash=hash).delete()
        print(a.name)
        add_gz_to_db(a)
    print(time()-start)
    #upd_deeppavlov()
