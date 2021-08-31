# -*- coding: utf-8 -*-

import sys
import os
from odoo import http, tools
from odoo.tools.func import lazy_property
from distutils.util import strtobool
from odoo.tools._vendor.sessions import SessionStore

if sys.version_info > (3,):
    import _pickle as cPickle

    unicode = str
else:
    import cPickle

SESSION_TIMEOUT = 60 * 60 * 24 * 7  # 1 weeks in seconds

hosts: str = tools.config.get('redis_host', None) or os.getenv('ENV_REDIS_HOST', 'localhost')
startup_nodes = hosts.split(',')

ports = int(tools.config.get('redis_port') or os.getenv('ENV_REDIS_PORT', '6379'))
db = int(tools.config.get('redis_dbindex') or os.getenv('ENV_REDIS_DB', '1'))
password = tools.config.get('redis_pass') or os.getenv('ENV_REDIS_PASSWORD', None)


def is_redis_session_store_activated():
    return tools.config.get('enable_redis') or strtobool(os.getenv('ENV_REDIS_ENABLE', 'False'))


try:
    import redis, rediscluster
except ImportError:
    if is_redis_session_store_activated():
        raise ImportError(
            'Please install package python3-redis: '
            'apt install python3-redis')


class RedisSessionStore(SessionStore):

    def __init__(self, *args, **kwargs):
        super(RedisSessionStore, self).__init__(*args, **kwargs)
        self.expire = kwargs.get('expire', SESSION_TIMEOUT)
        self.key_prefix = kwargs.get('key_prefix', '')
        if len(startup_nodes == 1):
            host = startup_nodes[0]
            self.redis = redis.Redis(
                health_check_interval=30,
                host=host,
                port=ports,
                db=db,
                password=password)
        else:
            self.redis = rediscluster.RedisCluster(
                startup_nodes=startup_nodes,
                health_check_interval=30,
                password=password)
        self._is_redis_server_running()

    def save(self, session):
        key = self._get_session_key(session.sid)
        data = cPickle.dumps(dict(session))
        self.redis.setex(name=key, value=data, time=self.expire)

    def delete(self, session):
        key = self._get_session_key(session.sid)
        self.redis.delete(key)

    def _get_session_key(self, sid):
        key = self.key_prefix + sid
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        return key

    def get(self, sid):
        key = self._get_session_key(sid)
        data = self.redis.get(key)
        if data:
            self.redis.setex(name=key, value=data, time=self.expire)
            data = cPickle.loads(data)
        else:
            data = {}
        return self.session_class(data, sid, False)

    def _is_redis_server_running(self):
        try:
            self.redis.ping()
        except redis.ConnectionError:
            raise redis.ConnectionError('Redis server is not responding')


if is_redis_session_store_activated():
    # Patch methods of openerp.http to use Redis instead of filesystem

    def session_gc(session_store):
        # Override to ignore file unlink
        # because sessions are not stored in files
        pass


    @lazy_property
    def session_store(self):
        # Override to use Redis instead of filestystem
        return RedisSessionStore(session_class=http.OpenERPSession)


    http.session_gc = session_gc
    http.Root.session_store = session_store
