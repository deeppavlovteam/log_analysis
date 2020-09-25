import json
import re
from datetime import datetime
from pathlib import Path

from deeppavlov.download import get_config_downloads
from django.db.models import Count
from git import Repo
from packaging import version

from log_analyser.log_dataframe import LogDataFrame
from log_analyser.log_tools import get_file_md5_hash
from log_analyser.log_transformers import validate_outer_request
from stats.models import Record, Hash, File, Config, ConfigName


def add_gz_to_db(path_to_gz: Path):
    hash = get_file_md5_hash(path_to_gz)
    ldf = LogDataFrame({'log_dataframe_columns':['a'], 'log_dir': '', 'pickle_file': '', 'hashes_file': ''})
    lines = ldf._read_file(path_to_gz)
    template = r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s"GET\s(.+?)"\s(.+?)\s(.+?)\s(".*?")\s(".*?")\s(".+?")$'
    parsed = re.findall(template, lines, flags=re.MULTILINE)
    creating = []
    for ip_from, domain, _1, timestamp, request, response_code, bytes, ref, app, _2 in parsed:
        file_templ = r'^(.+?)[\s\?]'
        config_templ = r'.+?[\?\&]config=(.+?)[\s\&]'
        file_match = re.search(file_templ, request)
        file = ''
        if file_match is not None:
            file = file_match.group(1)
        if File.objects.filter(name=file).exists():
            file = File.objects.get(name=file)
        else:
            file = File(name=file, md5=file.endswith('.md5'))
            file.save()
        config_match = re.search(config_templ, request)
        config = ''
        if config_match is not None:
            config = config_match.group(1)
        if ConfigName.objects.filter(name=config).exists():
            config = ConfigName.objects.get(name=config)
        else:
            config = ConfigName(name=config)
            config.save()
        try:
            r = Record(ip=ip_from,
                       time=datetime.strptime(timestamp, '[%d/%b/%Y:%H:%M:%S %z]'),
                       file=file,
                       config=config,
                       response_code=int(response_code),
                       bytes=int(bytes),
                       ref=ref,
                       app=app,
                       forwarded_for=_2,
                       outer_request=validate_outer_request({'ip_from': ip_from}),
                       gz_hash=hash)
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
                        if set(json.loads(config.files)) == set(files):
                            if version.parse(config.dp_version) < version.parse(dp_version):
                                config.dp_version = dp_version
                                if config.type != conf_type:
                                    config.type = conf_type
                                config.save()
                else:
                    new_conf = Config(type=conf_type,
                                      name=conf_name,
                                      dp_version=dp_version,
                                      files=json.dumps(files))
                    new_conf.save()

    get_files(conf_path)


def upd_deeppavlov():
#    repo = Repo.clone_from('https://github.com/deepmipt/DeepPavlov', './DeepPavlov', branch='master')
    repo = Repo('DeepPavlov')
    tags = sorted([t.name for t in repo.tags if version.parse(t.name) >= version.parse('0.2.0')], key=version.parse)
    for t in tags:
        repo.git.checkout(t)
        update_configs(conf_path='DeepPavlov/deeppavlov/configs', dp_version=t)


def boo():
    access = [p for p in Path('/home/ignatov/log_stuff/data/nginx/').resolve().glob('files-access.log*.gz')]
    for a in access:
        hash = get_file_md5_hash(a)
        if Hash.objects.filter(hash=hash).exists():
            print('skipping file')
            continue
        Record.objects.filter(gz_hash=hash).delete()
        print(a.name)
        add_gz_to_db(a)
#    update_files()