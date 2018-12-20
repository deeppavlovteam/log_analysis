from datetime import datetime


def convert_to_datetime(row):
    result = datetime.strptime(row['timestamp'], '[%d/%b/%Y:%H:%M:%S %z]')
    return result
