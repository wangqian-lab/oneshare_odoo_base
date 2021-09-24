# -*- encoding: utf-8 -*-

from http import HTTPStatus
from odoo.http import Response
from odoo.tools import ustr
from odoo.exceptions import UserError
import logging
import pprint
import functools
from typing import Literal
import json
import requests
import copy
from tenacity import retry, wait_random_exponential, RetryError
from json import JSONEncoder
import datetime

_logger = logging.getLogger(__name__)

MAGIC_ERROR_CODE = 59999  # 永远不会定义

DEFAULT_METHOD = 'post'

DEFAULT_HEADERS = {'Content-Type': 'application/json'}

ONESHARE_HTTP_ERROR_CODE = {
    40001: "Tightening Tool Is Not Success Configuration"
}


def _default_headers():
    return copy.deepcopy(DEFAULT_HEADERS)


def oneshare_http_request_stop(retry_state):
    if isinstance(retry_state.outcome, ValueError) or retry_state.attempt_number >= 5:
        return True
    else:
        return False


HTTP_METHOD_MODE = Literal['get', 'post', 'put', 'delete', 'options', 'head']


@retry(stop=oneshare_http_request_stop, wait=wait_random_exponential(multiplier=1, min=2, max=60), reraise=True)
def _send_request(full_url, method: HTTP_METHOD_MODE, headers, data, auth=None, timeout=6):
    m = getattr(requests, method)
    if not m:
        raise ValueError('Can Not Found The Method: {}'.format(method))
    if data and method in ['post', 'put']:
        payload = json.dumps(data)
    else:
        payload = None
    if payload:
        return m(url=full_url, data=payload, headers=headers, timeout=timeout, auth=auth)
    else:
        return m(url=full_url, headers=headers, timeout=timeout, auth=auth)


def _do_http_request(url, method: HTTP_METHOD_MODE = DEFAULT_METHOD, data=None, headers=DEFAULT_HEADERS, auth=None,
                     verify=False):
    try:
        _logger.debug('Do Request: {}, Data: {}'.format(url, pprint.pformat(data, indent=4)))
        resp = _send_request(full_url=url, method=method, data=data, headers=headers, auth=auth)
        if resp.status_code > 400:
            raise UserError(
                'Do Request: {} Fail, Status Code: {}, resp: {}'.format(url, resp.status_code, resp.text))
        else:
            return resp.json()
    except Exception as e:
        _logger.exception('HTTP Request URL:{} Except: {}'.format(url, ustr(e)))
        raise e


def http_request(method, url, auth=None):
    def decorator(f):
        @functools.wraps(f)
        def request_wrap(*args, **kw):
            rAuth = auth
            if kw.get('auth') and not rAuth:
                rAuth = kw.get('auth')
            data = f(*args, **kw)
            if data and not isinstance(data, dict):
                _logger.error('Function: {0}.{1}, HTTP Request Data Is Invalid'.format(f.__module__, f.__name__))
                return None
            headers = _default_headers()
            if not method or not url:
                raise ValueError('Http Request, Params method & url Is Required')
            full_url = url
            return _do_http_request(full_url, method, data, headers, rAuth, verify=False)

        return request_wrap

    return decorator


# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def oneshare_json_success_resp(status_code=HTTPStatus.OK, **kwargs):
    headers = [('Content-Type', 'application/json')]
    if status_code == HTTPStatus.NO_CONTENT:
        resp = Response(status=status_code, headers=headers)
        return resp
    if status_code > HTTPStatus.BAD_REQUEST:
        _logger.error("Success Response The Status Code Must Be Less Than 400, But Now Is {0}".format(status_code))
        return Response(HTTPStatus.OK, headers=headers)
    data = {
        "status_code": status_code,
        "msg": kwargs.get("msg") or kwargs.get("message"),
    }
    extra = kwargs.get("extra", "") or kwargs.get("extra_info", "")
    if extra:
        data.update({
            "extra": extra
        })
    body = json.dumps(data, cls=DateTimeEncoder)
    headers.append(('Content-Length', len(body)))
    resp = Response(body, status=status_code, headers=headers)
    return resp


def oneshare_json_fail_response(error_code=MAGIC_ERROR_CODE, status_code=HTTPStatus.BAD_REQUEST, **kwargs):
    msg = ONESHARE_HTTP_ERROR_CODE.get(error_code)
    if not msg:
        _logger.error("Error Code: {0} Is Not Defined".format(error_code))
        msg = kwargs.get("msg") or kwargs.get("message"),
    data = {
        "status_code": status_code,
        "msg": msg,
        "extra": kwargs.get("extra", "") or kwargs.get("extra_info", "")
    }
    body = json.dumps(data, cls=DateTimeEncoder)
    headers = [('Content-Type', 'application/json'), ('Content-Length', len(body))]
    return Response(body, status=status_code, headers=headers)
