import re
from datetime import datetime
from pathlib import Path

from log_analyser.log_dataframe import LogDataFrame
from stats.models import Record, Hash, File
from log_analyser.log_transformers import validate_outer_request
from log_analyser.log_tools import get_file_md5_hash
from django.db.models import Count


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
        config_match = re.search(config_templ, request)
        config = ''
        if config_match is not None:
            config = config_match.group(1)
        try:
            r = Record(ip=ip_from,
                       time=datetime.strptime(timestamp, '[%d/%b/%Y:%H:%M:%S %z]'),
                       file=file,
                       md5=file.endswith('.md5'),
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
    update_files()