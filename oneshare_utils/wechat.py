# -*- encoding: utf-8 -*-

import os
from wechatpy.client import WeChatClient
from wechatpy.client.api import WeChatWxa
import logging
from odoo.tools import ustr

_logger = logging.getLogger(__name__)

ENV_WECHAT_APP_ID = os.getenv('ENV_WECHAT_APP_ID', '')
ENV_WECHAT_SECRET_KEY = os.getenv('ENV_WECHAT_SECRET_KEY', '')


class WechatProvider(object):
    def __init__(self, app_id=ENV_WECHAT_APP_ID, secret_key=ENV_WECHAT_SECRET_KEY):
        self._app_id = app_id
        self._secret_key = secret_key
        self._client = WeChatClient(appid=self._app_id, secret=self._secret_key, timeout=60)
        self._session = None

    def auth(self, code: str = ''):
        if not self._client:
            return
        if not code:
            return
        ret = {}
        try:
            c = WeChatWxa(self._client)
            ret = c.code_to_session(code)
        except Exception as e:
            _logger.error(ustr(e))
        finally:
            return ret
