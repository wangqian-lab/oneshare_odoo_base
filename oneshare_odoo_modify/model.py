# -*- coding: utf-8 -*-

from odoo import models, api
import odoo
from odoo.tools.sql import _schema, table_exists
from distutils.util import strtobool
import os
import logging

_logger = logging.getLogger(__name__)

ENV_TIMESCALE_ENABLE = strtobool(os.getenv('ENV_TIMESCALE_ENABLE', 'false'))


class OneshareHyperModel(models.AbstractModel):
    _hyper = True
    _log_access = False
    _hyper_field = 'time'
    _dimensions = []
    _auto = True  # automatically create database backend
    _register = False  # not visible in ORM registry, meant to be python-inherited only
    _abstract = False  # not abstract
    _transient = False  # not transient
    _description = 'Hyper Model'

    @classmethod
    def _build_model_attributes(cls, pool):
        cls._hyper_interval = getattr(cls, '_hyper_interval', '1 month')
        cls._hyper_field = getattr(cls, '_hyper_field', 'time')
        super(OneshareHyperModel, cls)._build_model_attributes(pool)

    @api.model
    def _add_magic_fields(self):
        # cyclic import
        from odoo import fields
        # this field 'id' must override any other column or field
        self._add_field('id', fields.Id(automatic=True))

        if self._hyper_field not in self._fields:
            self._add_field(self._hyper_field, fields.Date(default=fields.Date.today, required=True))

    def _execute_sql(self):
        super(OneshareHyperModel, self)._execute_sql()
        if ENV_TIMESCALE_ENABLE:
            self._execute_hyper_sql()

    def _execute_hyper_sql(self):
        self._cr.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
        cmd = '''ALTER TABLE %s DROP CONSTRAINT IF EXISTS %s_pkey''' % (self._table, self._table)
        self._cr.execute(cmd)
        self._cr.commit()
        cmd = '''SELECT create_hypertable('%s', '%s',if_not_exists => TRUE,chunk_time_interval => interval '%s')''' % (
            self._table, self._hyper_field, self._hyper_interval,)
        self._cr.execute(cmd)
        _logger.info("HypterTable '%s': created", self._table)

    def _add_dimensions(self):
        """

        Modify this model's database table constraints so they match the one in
        _dimensions.

        """
        cr = self._cr

        def add(par_num, definition):
            query = '''SELECT add_dimension('%s', '%s', number_partitions => %d, if_not_exists => true)''' % (
                self._table, definition, par_num)
            try:
                cr.execute(query)
                cr.commit()
                _logger.info("Table '%s': added dimesion '%s' ",
                             self._table, definition)
            except Exception as e:
                _logger.warning("Table '%s': unable to add constraint '%s'!\n"
                                "If you want to have it, you should update the records and execute manually:\n%s",
                                self._table, definition, query)
                cr.rollback()

        par_num = 2 ** (len(self._dimensions) + 1)
        for definition in self._dimensions:
            add(par_num, definition)

    def _add_sql_constraints(self):
        # must_create_table = not table_exists(self._cr, self._table)
        super(OneshareHyperModel, self)._add_sql_constraints()
        self._cr.commit()
        if ENV_TIMESCALE_ENABLE:
            self._execute_hyper_sql()  # 先执行sql保证其变为hyper table
            self._add_dimensions()


odoo.models.OneshareHyperModel = OneshareHyperModel
