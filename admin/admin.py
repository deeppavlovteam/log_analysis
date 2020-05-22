import json
from collections import defaultdict

import requests
from flask import Flask, Response, redirect, flash
from flask_admin import Admin
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from flask_admin.model.filters import BaseBooleanFilter
from flask_basicauth import BasicAuth
from jinja2 import Markup
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.strategy_options import joinedload
from sqlalchemy.sql import func, text
from werkzeug.exceptions import HTTPException
from sqlalchemy.orm.exc import NoResultFound

from db.db import get_session
from db.models.record import Record
from db.models.config import Config


app = Flask(__name__)
#basic_auth = BasicAuth(app)

#class AuthException(HTTPException):
#    def __init__(self, message):
#        super().__init__(message, Response(
#            message, 401,
#            {'WWW-Authenticate': 'Basic realm="Login Required"'}
#        ))


class SafeModelView(ModelView):
    can_delete = False
    can_create = False
    can_edit = False

#    def is_accessible(self):
#        if not basic_auth.authenticate():
#            raise AuthException('Not authenticated. Refresh the page.')
#        else:
#            return True

#    def inaccessible_callback(self, name, **kwargs):
#        return redirect(basic_auth.challenge())


class ConfigModelView(SafeModelView):
    page_size=300


class FilterBySuccess(BaseSQLAFilter, BaseBooleanFilter):
    def apply(self, query, value, alias=None):
        if value == '1':
            return query.filter(Record.response_code == 200)
        else:
            print(query)
            return query.filter(Record.response_code != 200)

    def operation(self):
        return u'true'

class FilterOuter(BaseSQLAFilter, BaseBooleanFilter):
    def apply(self, query, value, alias=None):
        if value == '1':
            return query.filter(Record.outer_request == True)  # noqa: E711
        else:
            return query.filter(Record.outer_request == False)  # noqa: E711

    def operation(self):
        return u'outer'


class RecordModelView(SafeModelView):
    column_list = ('file', 'ip_from', 'outer_request', 'country')
    column_filters = (
        FilterBySuccess(column=None, name='response OK'),
        FilterOuter(column=None, name='Request type')
    )


if __name__ == '__main__':
    session = get_session('nginx', 'nginx', '192.168.10.78:5432', 'nginx_logs')
    admin = Admin(app, name='microblog', template_mode='bootstrap3')
    admin.add_view(ConfigModelView(Config, session))
    admin.add_view(RecordModelView(Record, session))
    app.run(host='0.0.0.0', port=5000)