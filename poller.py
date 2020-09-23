import re
from datetime import datetime
from pathlib import Path

from log_analyser.log_dataframe import LogDataFrame
from stats.models import Record
from log_analyser.log_transformers import validate_outer_request


def foo(path_to_gz: Path):
    ldf = LogDataFrame({'log_dataframe_columns':['a'], 'log_dir': '', 'pickle_file': '', 'hashes_file': ''})
    lines = ldf._read_file(path_to_gz)
    template = r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s"GET\s(.+?)"\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$'
    parsed = re.findall(template, lines, flags=re.MULTILINE)
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
                   outer_request=validate_outer_request({'ip_from': ip_from}))
        r.save()


def boo():
    access = [p for p in Path('/home/ignatov/log_stuff/data/nginx/').resolve().glob('files-access.log*.gz')]
    for a in access:
        foo(a)