# -*- coding: utf-8 -*-

import logging
import os
import sys
from distutils.util import strtobool

from psycopg2.extras import execute_values

import odoo
from odoo import models, api
from odoo.tools import index_exists, ustr
from odoo.tools.sql import _schema

_logger = logging.getLogger(__name__)

ENV_TIMESCALE_ENABLE = strtobool(os.getenv("ENV_TIMESCALE_ENABLE", "false"))


# def add_constraint(cr, tablename, constraintname, definition):
#     """ Add a constraint on the given table. """
#     query1 = 'ALTER TABLE "{}" ADD CONSTRAINT "{}" {}'.format(tablename, constraintname, definition)
#     query2 = 'COMMENT ON CONSTRAINT "{}" ON "{}" IS %s'.format(constraintname, tablename)
#     try:
#         with cr.savepoint(flush=False):
#             cr.execute(query1, log_exceptions=False)
#             cr.execute(query2, (definition,), log_exceptions=False)
#             _schema.debug("Table %r: added constraint %r as %s", tablename, constraintname, definition)
#     except Exception as e:
#         _logger.error(ustr(e))
#         raise Exception("Table %r: unable to add constraint %r as %s", tablename, constraintname, definition)
#
#
# odoo.tools.add_constraint = add_constraint


# def set_not_null(cr, tablename, columnname):
#     """ Add a NOT NULL constraint on the given column. """
#     query = 'ALTER TABLE "{}" ALTER COLUMN "{}" SET NOT NULL'.format(tablename, columnname)
#     try:
#         with cr.savepoint(flush=False):
#             cr.execute(query, log_exceptions=False)
#             _schema.debug("Table %r: column %r: added constraint NOT NULL", tablename, columnname)
#     except Exception as e:
#         _logger.error(ustr(e))
#         raise Exception("Table %r: unable to set NOT NULL on column %r", tablename, columnname)
# odoo.tools.sql.set_not_null = set_not_null


class OneshareHyperModel(models.AbstractModel):
    _log_access = False
    _hyper_field = "time"
    _retention_policy = False
    _compression_policy = False
    _dimensions = []
    _auto = True  # automatically create database backend
    _register = False  # not visible in ORM registry, meant to be python-inherited only
    _abstract = False  # not abstract
    _transient = False  # not transient
    _description = "Hyper Model"

    @api.model
    def raw_bulk_create(self, val_list, fetch=True):
        if not isinstance(val_list, list) or not val_list:
            return
        cr = self.env.cr
        fields = val_list[0].keys()
        fields_str = ",".join(fields)
        query = f"""
                INSERT INTO public.{self._table} ({fields_str}) VALUES %s {'RETURNING id' if fetch else ''};
                """
        tmpls = [f"%({f})s" for f in fields]
        tmpls_str = "({})".format(",".join(tmpls))
        if sys.version_info < (3, 8):  # psycopg2 版本小于2.8
            result = execute_values(
                cr, query, argslist=val_list, page_size=100, template=tmpls_str
            )
            if fetch:
                result = cr.fetchall()
        else:
            result = execute_values(
                cr,
                query,
                argslist=val_list,
                page_size=100,
                fetch=fetch,
                template=tmpls_str,
            )
        return result

    @api.model
    def raw_bulk_write(self, val_list, fetch=True):
        if not isinstance(val_list, list) or not val_list:
            return
        cr = self.env.cr
        fields = val_list[0].keys()
        fields_str = ",".join(fields)
        sets = [f"{f} = e.{f}" for f in fields]
        sets_str = "{}".format(",".join(sets))
        query = f"""
                    UPDATE public.{self._table} AS t
                    SET {sets_str}
                    FROM (VALUES %s) AS e({fields_str})
                    WHERE e.id = t.id;
                    """
        tmpls = [f"%({f})s" for f in fields]
        tmpls_str = "({})".format(",".join(tmpls))
        result = execute_values(
            cr, query, argslist=val_list, page_size=100, fetch=fetch, template=tmpls_str
        )
        return result

    @classmethod
    def _build_model_attributes(cls, pool):
        cls._hyper_interval = getattr(cls, "_hyper_interval", "1 month")
        cls._hyper_field = getattr(cls, "_hyper_field", "time")
        super(OneshareHyperModel, cls)._build_model_attributes(pool)

    @api.model
    def _add_magic_fields(self):
        # cyclic import
        from odoo import fields

        # this field 'id' must override any other column or field
        self._add_field("id", fields.Id(automatic=True))

        if self._hyper_field not in self._fields:
            self._add_field(
                self._hyper_field, fields.Date(default=fields.Date.today, required=True)
            )

    def create_index(cr, indexname, tablename, expressions):
        """Create the given index unless it exists."""
        if index_exists(cr, indexname):
            return
        args = ", ".join(expressions)
        sql = 'CREATE INDEX "{}" ON "{}" ({})'
        if ENV_TIMESCALE_ENABLE:
            sql = 'CREATE INDEX "{}" ON "{}" ({}) WITH (timescaledb.transaction_per_chunk)'
        cr.execute(sql.format(indexname, tablename, args))
        _schema.debug("Table %r: created index %r (%s)", tablename, indexname, args)

    def _execute_sql(self):
        super(OneshareHyperModel, self)._execute_sql()
        if ENV_TIMESCALE_ENABLE:
            self._execute_hyper_sql()

    def _execute_hyper_sql(self):
        self._cr.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
        self._cr.execute("""CREATE EXTENSION IF NOT EXISTS "uuid-ossp" CASCADE""")
        cmd = """ALTER TABLE %s DROP CONSTRAINT IF EXISTS %s_pkey""" % (
            self._table,
            self._table,
        )
        self._cr.execute(cmd)
        self._cr.commit()
        cmd = (
            """SELECT create_hypertable('%s', '%s',if_not_exists => TRUE,chunk_time_interval => interval '%s')"""
            % (
                self._table,
                self._hyper_field,
                self._hyper_interval,
            )
        )
        self._cr.execute(cmd)
        self._cr.commit()
        _logger.info("HyperTable '%s': created", self._table)

    def _add_dimensions(self):
        """

        Modify this model's database table constraints so they match the one in
        _dimensions.

        """
        cr = self._cr

        def add(par_num, definition):
            query = (
                """SELECT add_dimension('%s', '%s', number_partitions => %d, if_not_exists => true)"""
                % (self._table, definition, par_num)
            )
            try:
                cr.execute(query)
                cr.commit()
                _logger.info(
                    "Table '%s': added dimension '%s' ", self._table, definition
                )
            except Exception as e:
                _logger.error(ustr(e))
                _logger.warning(
                    "Table '%s': unable to add constraint '%s'!\n"
                    "If you want to have it, you should update the records and execute manually:\n%s",
                    self._table,
                    definition,
                    query,
                )
                cr.rollback()

        par_num = 2 ** (len(self._dimensions) + 1)
        for definition in self._dimensions:
            add(par_num, definition)

    def _add_retention_policy(self):
        if not ENV_TIMESCALE_ENABLE or not self._retention_policy:
            return
        remove_cmd = """SELECT remove_retention_policy('%s', if_exists => true);""" % (
            self._table,
        )
        self._cr.execute(remove_cmd)
        self._cr.commit()
        cmd = (
            """SELECT add_retention_policy('%s', INTERVAL '%s', if_not_exists => true);"""
            % (
                self._table,
                self._retention_policy,
            )
        )
        self._cr.execute(cmd)
        self._cr.commit()
        _logger.info(
            "Add Retention Policy For Table '%s':, Interval: %s created",
            self._table,
            self._retention_policy,
        )

    def _add_compression_policy(self):
        # FIXME: 一旦设定可压缩后，就不能解除
        if not ENV_TIMESCALE_ENABLE or not self._compression_policy:
            return
        cmd = """ALTER TABLE %s SET (timescaledb.compress);""" % (self._table,)
        self._cr.execute(cmd)
        self._cr.commit()
        # 移除已有的策略
        # remove_cmd = '''SELECT remove_compression_policy('%s', if_exists => true);''' % (
        #     self._table,)
        # self._cr.execute(remove_cmd)
        cmd = (
            """SELECT add_compression_policy('%s', INTERVAL '%s', if_not_exists => true);"""
            % (
                self._table,
                self._compression_policy,
            )
        )
        self._cr.execute(cmd)
        self._cr.commit()
        _logger.info(
            "Add Compression Policy For Table '%s':, Interval: %s created",
            self._table,
            self._compression_policy,
        )

    def _add_sql_constraints(self):
        # must_create_table = not table_exists(self._cr, self._table)
        super(OneshareHyperModel, self)._add_sql_constraints()
        self._cr.commit()
        if ENV_TIMESCALE_ENABLE:
            self._execute_hyper_sql()  # 先执行sql保证其变为hyper table
            self._add_dimensions()
            self._add_retention_policy()
            self._add_compression_policy()  # 增加温数据


odoo.models.OneshareHyperModel = OneshareHyperModel
