# -*- coding: utf-8 -*-
from distutils.util import strtobool
import tempfile
import os
import shutil
import psycopg2
from psycopg2 import sql
import odoo
import zipfile
from odoo.models import SUPERUSER_ID
from contextlib import closing
from odoo.service.db import check_db_management_enabled, exp_db_exist, DatabaseExists
import logging

_logger = logging.getLogger(__name__)

ENV_TIMESCALE_ENABLE = strtobool(os.getenv("ENV_TIMESCALE_ENABLE", "false"))


def _create_empty_database(name):
    db = odoo.sql_db.db_connect("postgres")
    with closing(db.cursor()) as cr:
        chosen_template = odoo.tools.config["db_template"]
        cr.execute(
            "SELECT datname FROM pg_database WHERE datname = %s",
            (name,),
            log_exceptions=False,
        )
        if cr.fetchall():
            raise DatabaseExists("database %r already exists!" % (name,))
        else:
            cr.autocommit(True)  # avoid transaction block

            # 'C' collate is only safe with template0, but provides more useful indexes
            collate = sql.SQL(
                "LC_COLLATE 'C'" if chosen_template == "template0" else ""
            )
            cr.execute(
                sql.SQL("CREATE DATABASE {} ENCODING 'unicode' {} TEMPLATE {}").format(
                    sql.Identifier(name), collate, sql.Identifier(chosen_template)
                )
            )

    if odoo.tools.config["unaccent"]:
        try:
            db = odoo.sql_db.db_connect(name)
            with closing(db.cursor()) as cr:
                cr.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
                cr.commit()
        except psycopg2.Error:
            pass

    if ENV_TIMESCALE_ENABLE:
        _add_timescale_extension(name)


def _timescale_pre_restore(name):
    if not ENV_TIMESCALE_ENABLE:
        return
    db = odoo.sql_db.db_connect(name)
    try:
        with closing(db.cursor()) as cr:
            cr.execute("SELECT timescaledb_pre_restore()")
            cr.commit()
    except Exception as e:
        _logger.error("SELECT timescaledb_pre_restore() Failed")


def _timescale_post_restore(name):
    if not ENV_TIMESCALE_ENABLE:
        return
    db = odoo.sql_db.db_connect(name)
    try:
        with closing(db.cursor()) as cr:
            cr.execute("SELECT timescaledb_post_restore()")
            cr.commit()
    except Exception as e:
        _logger.error("SELECT timescaledb_post_restore() Failed")


def _add_timescale_extension(name):
    if not ENV_TIMESCALE_ENABLE:
        return
    db = odoo.sql_db.db_connect(name)
    try:
        with closing(db.cursor()) as cr:
            cr.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            cr.execute("""CREATE EXTENSION IF NOT EXISTS "uuid-ossp" CASCADE""")
            cr.commit()
    except Exception as e:
        _logger.error("Extension For TIMESCALEDB Failed")


@check_db_management_enabled
def restore_db(db, dump_file, copy=False):
    if not isinstance(db, str):
        raise AssertionError
    if exp_db_exist(db):
        _logger.info("RESTORE DB: %s already exists", db)
        raise Exception("Database already exists")

    _create_empty_database(db)
    if ENV_TIMESCALE_ENABLE:
        _timescale_pre_restore(db)

    filestore_path = None
    with tempfile.TemporaryDirectory() as dump_dir:
        if zipfile.is_zipfile(dump_file):
            # v8 format
            with zipfile.ZipFile(dump_file, "r") as z:
                # only extract known members!
                filestore = [m for m in z.namelist() if m.startswith("filestore/")]
                z.extractall(dump_dir, ["dump.sql"] + filestore)

                if filestore:
                    filestore_path = os.path.join(dump_dir, "filestore")

            pg_cmd = "psql"
            pg_args = ["-q", "-f", os.path.join(dump_dir, "dump.sql")]

        else:
            # <= 7.0 format (raw pg_dump output)
            pg_cmd = "pg_restore"
            pg_args = ["--no-owner", dump_file]

        args = []
        args.append("--dbname=" + db)
        pg_args = args + pg_args

        if odoo.tools.exec_pg_command(pg_cmd, *pg_args):
            raise Exception("Couldn't restore database")

        registry = odoo.modules.registry.Registry.new(db)
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, SUPERUSER_ID, {})
            if copy:
                # if it's a copy of a database, force generation of a new dbuuid
                env["ir.config_parameter"].init(force=True)
            if filestore_path:
                filestore_dest = env["ir.attachment"]._filestore()
                shutil.move(filestore_path, filestore_dest)
    if ENV_TIMESCALE_ENABLE:
        _timescale_post_restore(db)
    _logger.info("RESTORE DB: %s", db)


if ENV_TIMESCALE_ENABLE:
    odoo.service.db.restore_db = restore_db
    odoo.service.db._create_empty_database = _create_empty_database
