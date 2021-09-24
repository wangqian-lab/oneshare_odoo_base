# -*- encoding: utf-8 -*-

from baidu_aip_sdk.nlp import AipNlp
from distutils.util import strtobool

try:
    from .http import http_request
except ImportError:
    from odoo.addons.oneshare_utils.http import http_request
import os

ENV_GITHUB_ACCESS_TOKEN = os.getenv('ENV_GITHUB_ACCESS_TOKEN', '')
ENV_GITHUB_OWNER = os.getenv('ENV_GITHUB_OWNER', '')


class GithubProvider(object):
    def __init__(self, token=ENV_GITHUB_ACCESS_TOKEN, owner=ENV_GITHUB_OWNER):
        self._access_token = token
        self._owner = owner
        self._repo_event_url_tmpl = f'https://api.github.com/repos/{self._owner}/%s/dispatches'

    def open(self):
        return True

    def invoke_api(self, evt: str = '', *args, **kwargs):
        if evt == 'repo_dispatch':
            repo = kwargs.get('repo', '')
            return self.trigger_repo_dispatch_evt(repo)

    def trigger_repo_dispatch_evt(self, repo=''):
        if not repo:
            return
        url = self._repo_event_url_tmpl % (repo,)
        headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {self._access_token}'}
        resp = self._do_trigger_repo_dispatch_evt(url=url, headers=headers)
        return resp

    @http_request()
    def _do_trigger_repo_dispatch_evt(self, *args, **kwargs):
        data = {"event_type": kwargs.get("event_type", "event_type")}
        return data
