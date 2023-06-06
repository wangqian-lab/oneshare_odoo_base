# -*- coding: utf-8 -*-
import os
from distutils.util import strtobool

from odoo import models, api

ENV_TIMESCALE_ENABLE = strtobool(os.getenv("ENV_TIMESCALE_ENABLE", "false"))


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def search_count(self, args):
        return super(Base, self).search_count(args)
        # TODO: 关于select count(1)慢
        # self._flush_search(args)
        #
        # query = self._where_calc(args)
        # self._apply_ir_rules(query, 'read')
        # query.subselect()
        # query_str, params = query.ad(f"* FROM approximate_row_count('{self._table}')")
        # self._cr.execute(query_str, params)
        # res = self._cr.fetchone()
        # return res[0]
