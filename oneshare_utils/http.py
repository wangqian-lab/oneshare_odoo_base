# -*- encoding: utf-8 -*-

from http import HTTPStatus
from odoo.http import Response
import logging
import json
from json import JSONEncoder
import datetime

_logger = logging.getLogger(__name__)

MAGIC_ERROR_CODE = 59999  # 永远不会定义

ONESHARE_HTTP_ERROR_CODE = {
    40001: "Tightening Tool Is Not Success Configuration"
}


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
