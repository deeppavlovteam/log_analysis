import re
from datetime import datetime


def convert_to_datetime(row):
    result = datetime.strptime(row['timestamp'], '[%d/%b/%Y:%H:%M:%S %z]')
    return result


def validate_outer_request(row):
    result = False if re.fullmatch(r'^10\.11.+', row['ip_from']) else True
    return result


def get_resource(row):
    match = re.search(r'^"GET\s+(.+)\s+HTTP.+"$', row['request'])
    result = match.group(1) if match else None
    return result

