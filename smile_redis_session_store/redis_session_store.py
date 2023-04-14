# -*- coding: utf-8 -*-

import sys
from odoo import http, tools
from odoo.tools.func import lazy_property
from odoo.tools._vendor.sessions import SessionStore
from odoo.addons.smile_redis_session_store.constants import (
    is_redis_session_store_activated,
    SESSION_TIMEOUT,
    startup_nodes,
    redis_ports,
    redis_db,
    redis_password,
)

if sys.version_info > (3,):
    import _pickle as cPickle

    unicode = str
else:
    import cPickle

try:
    import redis
except ImportError:
    if is_redis_session_store_activated():
        raise ImportError(
            "Please install package python3-redis: " "apt install python3-redis"
        )

from redis.backoff import ExponentialBackoff
from redis.retry import Retry

class RedisSessionStore(SessionStore):
    def __init__(self, *args, **kwargs):
        super(RedisSessionStore, self).__init__(*args, **kwargs)
        self.expire = kwargs.get("expire", SESSION_TIMEOUT)
        self.key_prefix = kwargs.get("key_prefix", "")
        retry = Retry(ExponentialBackoff(), 3)
        host = startup_nodes[0]
        if len(startup_nodes) == 1:
            self.redis = redis.Redis(
                health_check_interval=30,
                host=host,
                port=redis_ports,
                db=redis_db,
                password=redis_password,
                retry=retry,
            )
        else:
            self.redis = redis.cluster.RedisCluster(
                host=host,
                port=redis_ports,
                retry=retry,
                health_check_interval=30,
                password=redis_password,
            )
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
            key = key.encode("utf-8")
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
            raise redis.ConnectionError("Redis server is not responding")


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
