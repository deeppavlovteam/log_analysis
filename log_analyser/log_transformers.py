import re
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network

from log_analyser.log_tools import GeoliteDbWrapper


#geolite_db_wrapper = GeoliteDbWrapper()


def convert_str_to_datetime(row):
    if isinstance(row['timestamp'], str):
        result = datetime.strptime(row['timestamp'], '[%d/%b/%Y:%H:%M:%S %z]')
    else:
        result = None

    return result


def convert_datetime_to_date(row):
    if isinstance(row['timestamp'], datetime):
        timestamp: datetime = row['timestamp']
        result = timestamp.date()
    else:
        result = None

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
    if isinstance(row['request'], str):
        match = re.search(r'^"GET\s+(.+)\s+HTTP.+"$', row['request'])
        result = match.group(1) if match else None
    else:
        result = None

    return result


def get_resource_group(row):
    if isinstance(row['resource'], str):
        result = row['resource'].strip('/').split('/')[0]
    else:
        result = None

    return result


def get_country_from_ip(row):
    try:
        ip_info = geolite_db_wrapper.get_ip_info(row['ip_from'])
        result = ip_info['country']['names']['en'] if isinstance(ip_info, dict) else None

    except (ValueError, KeyError):
        result = None

    return result


def get_city_from_ip(row):
    try:
        ip_info = geolite_db_wrapper.get_ip_info(row['ip_from'])
        result = ip_info['city']['names']['en'] if isinstance(ip_info, dict) else None

    except (ValueError, KeyError):
        result = None

    return result
