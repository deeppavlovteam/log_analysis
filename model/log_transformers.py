import re
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network


def convert_str_to_datetime(row):
    result = datetime.strptime(row['timestamp'], '[%d/%b/%Y:%H:%M:%S %z]')
    return result


def convert_datetime_to_date(row):
    timestamp: datetime = row['timestamp']
    result = timestamp.date()
    return result


def validate_outer_request(row):
    try:
        ip_from = IPv4Address(row['ip_from'])
    except ValueError:
        return False

    net_10 = IPv4Network('10.0.0.0/8')
    net_172 = IPv4Network('172.16.0.0/12')
    net_192 = IPv4Network('192.168.0.0/16')

    result = not (ip_from in net_10 or ip_from in net_172 or ip_from in net_192)

    return result


def get_resource(row):
    match = re.search(r'^"GET\s+(.+)\s+HTTP.+"$', row['request'])
    result = match.group(1) if match else None
    return result


def get_resource_group(row):
    result = row['resource'].strip('/').split('/')[0]
    return result
