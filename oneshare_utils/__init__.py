# -*- encoding: utf-8 -*-

from . import baidu
from . import http
from . import constants


class CloudProvider(object):
    def __init__(self, subclass=None, *args, **kwargs):
        self._subclass = subclass
        self._app = {}
        if subclass:
            self._app = self._subclass(*args, **kwargs)

    def address_recognition(self, text):
        raise NotImplementedError()

    def open(self):
        method = getattr(self._app, 'open', None)
        if not method:
            return False
        return method()

    def recognition(self, type, *args, **kargs):
        return self._app.recognition(type, *args, **kargs)
