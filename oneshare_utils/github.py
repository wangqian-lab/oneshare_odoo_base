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
    def __init__(self, token=ENV_GITHUB_ACCESS_TOKEN):
        self._access_token = token
        self._repo_event_url_tmpl = f'https://api.github.com/repos/%s/%s/dispatches'

    def open(self):
        return True

    def invoke_api(self, evt: str = '', *args, **kwargs):
        if evt == 'repo_dispatch':
            repo = kwargs.get('repo', '')
            owner = kwargs.get('owner', '')
            client_payload = kwargs.get('client_payload', '')
            return self.trigger_repo_dispatch_evt(owner, repo, client_payload)

    def trigger_repo_dispatch_evt(self, owner='', repo='', client_payload: dict = {}):
        if not repo or not owner:
            return
        url = self._repo_event_url_tmpl % (owner, repo,)
        headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {self._access_token}'}
        resp = self._do_trigger_repo_dispatch_evt(url=url, headers=headers, client_payload=client_payload)
        return resp

    @http_request()
    def _do_trigger_repo_dispatch_evt(self, *args, **kwargs):
        data = {"event_type": kwargs.get("event_type", "event_type"),
                "client_payload": kwargs.get('client_payload', {})}
        return data
