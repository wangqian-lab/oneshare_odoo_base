# -*- coding: utf-8 -*-

import collections
import functools
import json
import logging
import os
import pprint
import random
import time

import psycopg2
import werkzeug.wrappers
from jsonschema import validate, ValidationError
from odoo.addons.oneshare_utils.http import oneshare_json_fail_response

from odoo import http
from odoo.tools import ustr

SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "604800"))  # 1 weeks in seconds

import odoo
from odoo.http import (
    AuthenticationError,
    Response,
    Root,
    SessionExpiredException,
    WebRequest,
    request,
    rpc_request,
    rpc_response,
    serialize_exception,
)
from odoo.service.server import memory_info
from odoo.tools import date_utils

try:
    import psutil
except ImportError:
    psutil = None

_logger = logging.getLogger(__name__)


class ApiJsonRequest(WebRequest):
    _request_type = "apijson"

    def __init__(self, *args):
        super(ApiJsonRequest, self).__init__(*args)

        self.jsonp_handler = None
        self.params = collections.OrderedDict(
            self.httprequest.values or self.httprequest.args
        )

        args = self.httprequest.args
        jsonp = args.get("jsonp")
        self.jsonp = jsonp
        request = None
        request_id = args.get("id")

        if jsonp and self.httprequest.method == "POST":
            # jsonp 2 steps step1 POST: save call
            def handler():
                self.session[
                    "jsonp_request_{}".format(request_id)
                ] = self.httprequest.form["rb"]
                self.session.modified = True
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                r = werkzeug.wrappers.Response(request_id, headers=headers)
                return r

            self.jsonp_handler = handler
            return
        elif jsonp and args.get("rb"):
            # jsonp method GET
            request = args.get("rb")
        elif jsonp and request_id:
            # jsonp 2 steps step2 GET: run and return result
            request = self.session.pop("jsonp_request_{}".format(request_id), "{}")
        else:
            # regular jsonrpc2
            request = self.httprequest.get_data().decode(self.httprequest.charset)

        # Read POST content or POST Form Data named "request"
        try:
            if request:
                self.ApiJsonRequest = json.loads(
                    request, object_pairs_hook=collections.OrderedDict
                )
            else:
                self.ApiJsonRequest = None
        except ValueError:
            msg = "Invalid JSON data: {!r}".format(request)
            _logger.info("%s: %s", self.httprequest.path, msg)
            self.ApiJsonRequest = None

        self.context = self.params.pop("context", dict(self.session.context))

    @staticmethod
    def _json_response(result=None, error=None):
        response = {}
        if error:
            response["error"] = error
        if result and isinstance(result, dict):
            result = Response(**result)
        mime = "application/json"
        status = error and error.pop("code") or result.status_code
        body = (
            response
            and json.dumps(response, default=date_utils.json_default)
            or result.data
        )

        return Response(
            body,
            status=status,
            headers=[("Content-Type", mime), ("Content-Length", len(body))],
        )

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
        to arbitrary responses. Anything returned (except None) will
        be used as response."""
        try:
            return super(ApiJsonRequest, self)._handle_exception(exception)
        except Exception:
            if not isinstance(
                exception,
                (
                    odoo.exceptions.Warning,
                    SessionExpiredException,
                    odoo.exceptions.except_orm,
                    werkzeug.exceptions.NotFound,
                ),
            ):
                _logger.exception("Exception during JSON request handling.")
            error = {
                "code": 500,
                "message": "Odoo Server Error",
                "data": serialize_exception(exception),
                "openapi_message": exception.args[0],
            }
            if isinstance(exception, psycopg2.InternalError):
                error["message"] = "500: Internal Server Error"
            if isinstance(exception, werkzeug.exceptions.NotFound):
                error["code"] = 404
                error["message"] = "404: Not Found"
            if isinstance(exception, AuthenticationError):
                error["code"] = 100
                error["message"] = "Odoo Session Invalid"
            if isinstance(exception, SessionExpiredException):
                error["code"] = 100
                error["message"] = "Odoo Session Expired"
            return self._json_response(error=error)

    def dispatch(self):
        if self.jsonp_handler:
            return self.jsonp_handler()
        try:
            rpc_request_flag = rpc_request.isEnabledFor(logging.DEBUG)
            rpc_response_flag = rpc_response.isEnabledFor(logging.DEBUG)
            if rpc_request_flag or rpc_response_flag:
                endpoint = self.endpoint.method.__name__
                model = self.params.get("model")
                method = self.params.get("method")
                args = self.params.get("args", [])

                start_time = time.time()
                start_memory = 0
                if psutil:
                    start_memory = memory_info(psutil.Process(os.getpid()))
                if rpc_request and rpc_response_flag:
                    rpc_request.debug(
                        "%s: %s %s, %s", endpoint, model, method, pprint.pformat(args)
                    )

            result = self._call_function(**self.params)

            if rpc_request_flag or rpc_response_flag:
                end_time = time.time()
                end_memory = 0
                if psutil:
                    end_memory = memory_info(psutil.Process(os.getpid()))
                logline = "{}: {} {}: time:{:.3f}s mem: {}k -> {}k (diff: {}k)".format(
                    endpoint,
                    model,
                    method,
                    end_time - start_time,
                    start_memory / 1024,
                    end_memory / 1024,
                    (end_memory - start_memory) / 1024,
                )
                if rpc_response_flag:
                    rpc_response.debug("%s, %s", logline, pprint.pformat(result))
                else:
                    rpc_request.debug(logline)
            return self._json_response(result)
        except Exception as e:
            return self._handle_exception(e)


# Copy of http.route adding routing 'type':'api'
def api_route(route=None, **kw):
    routing = kw.copy()
    if not ("type" not in routing or routing["type"] in ("http", "json", "apijson")):
        raise AssertionError

    def decorator(f):
        if route:
            if isinstance(route, list):
                routes = route
            else:
                routes = [route]
            routing["routes"] = routes

        @functools.wraps(f)
        def response_wrap(*args, **kw):
            if routing.get("schema") and getattr(request, "ApiJsonRequest", None):
                try:
                    validate(request.ApiJsonRequest, routing.get("schema"))
                except ValidationError as e:
                    msg = ustr(e)
                    return oneshare_json_fail_response(msg=msg)
            response = f(*args, **kw)
            if isinstance(response, Response) or f.routing_type in ("apijson", "json"):
                return response

            if isinstance(response, (bytes, str)):
                return Response(response)

            if isinstance(response, werkzeug.exceptions.HTTPException):
                response = response.get_response(request.httprequest.environ)
            if isinstance(response, werkzeug.wrappers.BaseResponse):
                response = Response.force_type(response)
                response.set_default()
                return response

            _logger.warning(
                "<function %s.%s> returns an invalid response type for an http request",
                f.__module__,
                f.__name__,
            )
            return response

        response_wrap.routing = routing
        response_wrap.original_func = f
        return response_wrap

    return decorator


odoo.http.api_route = api_route

get_request_original = Root.get_request

setup_lang_original = Root.setup_lang


def api_get_request(self, httprequest):
    # deduce type of request
    org_name = httprequest.headers.get("x-org-name", "")
    if not isinstance(org_name, str):
        return get_request_original(self, httprequest)

    if (
        org_name.upper() == "ONESHARE"
        and httprequest.headers.get("content-type", "") == "application/json"
    ):
        return ApiJsonRequest(httprequest)

    return get_request_original(self, httprequest)


ENV_DEFAULT_LANGUAGE = os.getenv("ENV_DEFAULT_LANGUAGE", "zh_CN")


def api_setup_lang(self, httprequest):
    if ENV_DEFAULT_LANGUAGE:
        httprequest.session.context["lang"] = ENV_DEFAULT_LANGUAGE
    else:
        setup_lang_original(self, httprequest)


def session_gc(session_store):
    if random.random() < 0.001:
        # we keep session one week
        last_week = time.time() - SESSION_TIMEOUT
        for fname in os.listdir(session_store.path):
            path = os.path.join(session_store.path, fname)
            try:
                if os.path.getmtime(path) < last_week:
                    os.unlink(path)
            except OSError:
                pass


http.session_gc = session_gc

Root.setup_lang = api_setup_lang
Root.get_request = api_get_request
