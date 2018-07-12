# -*- coding: utf-8 -*-
#

import os

from . import utils
from .exception import LoadAccessKeyError


class AccessKeyAuth:
    def __init__(self, access_key):
        self.access_key = access_key

    def sign_request(self, req):
        date = utils.http_date()
        req.headers['Date'] = date
        #signature = utils.make_signature(self.access_key.secret, date=date)
        req.headers['Authorization'] = self.access_key.secret
        return req

    def __bool__(self):
        return bool(self.access_key)


class TokenAuth:
    def __init__(self, token):
        self.token = token

    def sign_request(self, req):
        req.headers['Authorization'] = 'Bearer {0}'.format(self.token)
        return req

    def __bool__(self):
        return self.token != ""


class SessionAuth:
    def __init__(self, session_id, csrf_token):
        self.session_id = session_id
        self.csrf_token = csrf_token

    def sign_request(self, req):
        cookie = [v for v in req.headers.get('Cookie', '').split(';')
                  if v.strip()]
        cookie.extend(['sessionid='+self.session_id,
                       'csrftoken='+self.csrf_token])
        req.headers['Cookie'] = ';'.join(cookie)
        req.headers['X-CSRFTOKEN'] = self.csrf_token
        return req

    def __bool__(self):
        return self.session_id != ""


class PrivateTokenAuth:

    def __init__(self, token):
        self.token = token

    def sign_request(self, req):
        req.headers['Authorization'] = 'Token {0}'.format(self.token)
        return req

    def __bool__(self):
        return self.token != ""


class AccessKey(object):
    def __init__(self, id=None, secret=None):
        self.id = id
        self.secret = secret

    @staticmethod
    def clean(value, sep=':', silent=False):
        try:
            id, secret = value.split(sep)
        except (AttributeError, ValueError) as e:
            if not silent:
                raise LoadAccessKeyError(e)
            return '', ''
        else:
            return id, secret

    def load_from_val(self, val, **kwargs):
        self.id, self.secret = self.clean(val, **kwargs)

    def load_from_env(self, env, **kwargs):
        value = os.environ.get(env)
        self.id, self.secret = self.clean(value, **kwargs)

    def load_from_f(self, f, **kwargs):
        value = ''
        if isinstance(f, str) and os.path.isfile(f):
            f = open(f)
        if hasattr(f, 'read'):
            for line in f:
                if line and not line.strip().startswith('#'):
                    value = line.strip()
                    break
            f.close()
        self.id, self.secret = self.clean(value, **kwargs)

    def save_to_f(self, f, silent=False):
        if isinstance(f, str):
            f = open(f, 'wt')
        try:
            f.write('{0}:{1}'.format(self.id, self.secret))
        except IOError:
            if not silent:
                raise
        finally:
            f.close()

    def __bool__(self):
        return bool(self.id) and bool(self.secret)

    def __eq__(self, other):
        return self.id == other.id and self.secret == other.secret

    def __str__(self):
        return '{0}'.format(self.id)

    def __repr__(self):
        return '{0}'.format(self.id)


class AppAccessKey(AccessKey):
    """使用Access key来认证"""

    def __init__(self, app, id=None, secret=None):
        super().__init__(id=id, secret=secret)
        self.app = app

    @property
    def _key_env(self):
        return self.app.config['ACCESS_KEY_ENV']

    @property
    def _key_val(self):
        return self.app.config['ACCESS_KEY']

    @property
    def _key_file(self):
        return self.app.config['ACCESS_KEY_FILE']

    def load_from_conf_env(self, sep=':', silent=False):
        super().load_from_env(self._key_env, sep=sep, silent=silent)

    def load_from_conf_val(self, sep=':', silent=False):
        super().load_from_val(self._key_val, sep=sep, silent=silent)

    def load_from_conf_file(self, sep=':', silent=False):
        super().load_from_f(self._key_file, sep=sep, silent=silent)

    def load(self, **kwargs):
        """Should return access_key_id, access_key_secret"""
        for method in [self.load_from_conf_env,
                       self.load_from_conf_val,
                       self.load_from_conf_file]:
            try:
                return method(**kwargs)
            except LoadAccessKeyError:
                continue
        return None

    def save_to_file(self):
        return super().save_to_f(self._key_file)
