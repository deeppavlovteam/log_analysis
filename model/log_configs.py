from model.log_transformers import convert_str_to_datetime, convert_datetime_to_date, validate_outer_request
from model.log_transformers import get_resource, get_resource_group, get_country_from_ip, get_city_from_ip


DEFAULT_CONFIG = {
    'log_dir': '/var/log/nginx',
    'pickle_file': 'logs_df.pkl',
    'hashes_file': 'hashes.txt',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': '*access.log*',
    'log_arc_file_name_re_pattern': r'.+\.gz$',
    'log_source_pattern': r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s(".+?")\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$',
    'log_source_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                          'bytes', 'ref', 'app', '_2'],
    'log_dataframe_columns': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                              'bytes', 'ref', 'app', '_2', 'date', 'outer_request', 'resource', 'resource_group'],

    'pre_filters': {
        'filter_match': [],
        'filter_not_match': [{'column': 'request', 'regexp': r'^"GET /.+md5 HTTP.+"$'}],
        'filter_in': [{'column': 'domain', 'values': ['files.deeppavlov.ai']}],
        'filter_not_in': [],
    },
    'transform': [{'column': 'timestamp', 'transformer': convert_str_to_datetime},
                  {'column': 'date', 'transformer': convert_datetime_to_date},
                  {'column': 'outer_request', 'transformer': validate_outer_request},
                  {'column': 'resource', 'transformer': get_resource},
                  {'column': 'resource_group', 'transformer': get_resource_group}],
    'post_filters': {
        'filter_match': [],
        'filter_not_match': [],
        'filter_in': [],
        'filter_not_in': [{'column': 'resource_group', 'values': ['', 'favicon.ico', 'robots.txt', 'sitemap.xml',
                                                                  'vemgmtss.html']}],
    }
}

RAW_FILES_LOG_CONFIG = {
    'log_dir': '/var/log/nginx',
    'pickle_file': '../raw_logs_df.pkl',
    'hashes_file': '../raw_hashes.txt',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': '*access.log*',
    'log_arc_file_name_re_pattern': r'.+\.gz$',
    'log_source_pattern': r'^(\S+?)\s(\S+?)\s(\S+?)\s(\[.+?\])\s(".+?")\s(.+?)\s(.+?)\s(".+?")\s(".+?")\s(".+?")$',
    'log_source_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                          'bytes', 'ref', 'app', '_2'],
    'log_dataframe_columns': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code',
                          'bytes', 'ref', 'app', '_2'],

    'pre_filters': {
        'filter_match': [],
        'filter_not_match': [],
        'filter_in': [{'column': 'domain', 'values': ['files.deeppavlov.ai']}],
        'filter_not_in': [],
    },
    'transform': [],
    'post_filters': {
        'filter_match': [],
        'filter_not_match': [],
        'filter_in': [],
        'filter_not_in': [],
    }
}

PROCESSED_FILES_LOG_CONFIG = {
    'log_dir': '',
    'pickle_file': '../logs_df.pkl',
    'hashes_file': '',
    'reports_dir': 'reports',
    'log_file_name_glob_pattern': '*access.log*',
    'log_arc_file_name_re_pattern': r'',
    'log_source_pattern': r'',
    'log_source_fields': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code', 'bytes',
                          'ref', 'app', '_2'],
    'log_dataframe_columns': ['ip_from', 'domain', '_1', 'timestamp', 'request', 'response_code', 'bytes',
                              'ref', 'app', '_2', 'date', 'outer_request', 'resource', 'resource_group',
                              'country_from', 'city_from'],

    'pre_filters': {
        'filter_match': [],
        'filter_not_match': [{'column': 'request', 'regexp': r'^"GET /.+md5 HTTP.+"$'}],
        'filter_in': [],
        'filter_not_in': [],
    },
    'transform': [{'column': 'timestamp', 'transformer': convert_str_to_datetime},
                  {'column': 'date', 'transformer': convert_datetime_to_date},
                  {'column': 'outer_request', 'transformer': validate_outer_request},
                  {'column': 'resource', 'transformer': get_resource},
                  {'column': 'resource_group', 'transformer': get_resource_group},
                  {'column': 'country_from', 'transformer': get_country_from_ip},
                  {'column': 'city_from', 'transformer': get_city_from_ip}],
    'post_filters': {
        'filter_match': [],
        'filter_not_match': [],
        'filter_in': [],
        'filter_not_in': [{'column': 'resource_group', 'values': ['', 'favicon.ico', 'robots.txt', 'sitemap.xml',
                                                                  'vemgmtss.html']}],
    }
}
