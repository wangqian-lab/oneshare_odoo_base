# -*- coding: utf-8 -*-
from unittest import TestCase
from ..github import GithubProvider
from .. import CloudProvider

from odoo import api, exceptions, fields, models, _


class TestGithubProvider(TestCase):
    def setUp(self):
        self._app = CloudProvider(GithubProvider)
        self._app.open()

    def test_trigger_repo_dispatch_evt(self):
        ret = self._app.invoke_api('repo_dispatch', repo='onesphere')
        print(ret)
        self.assertTrue(ret)
