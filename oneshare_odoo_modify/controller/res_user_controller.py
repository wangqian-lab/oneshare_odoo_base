# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID, api, _
from odoo.http import request, Response
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.oneshare_utils.http import (
    oneshare_json_success_resp,
    oneshare_json_fail_response,
)
from odoo.tools import ustr, image_process
from odoo.addons.phone_validation.tools import phone_validation

import logging

_logger = logging.getLogger(__name__)

api_change_user_info = {
    "type": "object",
    "properties": {
        "login": {"type": "string"},  # 登陆用户名
        "mobile": {"type": "string"},  # 手机号码
        "password": {"type": "string"},  # 密码
        "student": {"type": "string"},  # 如果是家长，学生名称
        "avatar": {"type": "string"},  # 头像, base64 数据
    },
    "required": [
        "login",
        "mobile",
    ],
}

api_change_password = {
    "type": "object",
    "properties": {
        "old_password": {"type": "string"},  # 原始密码
        "new_password": {"type": "string"},  # 修改的密码
        "confirm_password": {"type": "string"},  # 确认修改密码
    },
    "required": [
        "old_password",
        "new_password",
        "confirm_password",
    ],
}


class ResUserController(http.Controller):
    @http.api_route(
        "/api/v1/user/change_password",
        type="apijson",
        methods=["PUT"],
        auth="user",
        cors="*",
        csrf=False,
        schema=api_change_user_info,
    )
    def change_password(self, **kwargs):
        """
        修改密码API, 修改完后需要重新登陆
        :param kwargs:
        :return:
        """
        params = request.ApiJsonRequest
        old_password = params.get("old_password")
        new_password = params.get("new_password")
        confirm_password = params.get("confirm_password")
        if new_password != confirm_password:
            msg = _("The new password and its confirmation must be identical.")

            return oneshare_json_fail_response(msg=msg)
        msg = _("Error, password not changed !")
        try:
            if request.env["res.users"].change_password(old_password, new_password):
                extra = {"new_password": new_password}
                msg = _("Success, password changed!")
                return oneshare_json_success_resp(msg=msg, **extra)
        except AccessDenied as e:
            msg = e.args[0]
            if msg == AccessDenied().args[0]:
                msg = _(
                    "The old password you provided is incorrect, your password was not changed."
                )
        except UserError as e:
            msg = e.args[0]
        return oneshare_json_fail_response(msg=msg)

    @http.api_route(
        "/api/v1/user/info",
        type="apijson",
        methods=["PUT"],
        auth="user",
        cors="*",
        csrf=False,
        schema=api_change_user_info,
    )
    def change_user_info(self, **kwargs):
        params = request.ApiJsonRequest
        login = params.get("login")
        password = params.get("password")
        avatar = params.get("avatar")
        user_id = request.env.user
        need_relogin = False
        extra = {"relogin": False}
        cr = request.env.cr
        val = {}
        if login and login != request.session.login:
            val.update({"login": login})
        if password:
            val.update({"password": password})
            need_relogin = True
        if avatar:
            val.update({"image_1920": image_process(avatar, verify_resolution=True)})
        ret = user_id.write(val)
        if ret and need_relogin:
            extra.update({"relogin": True})

        if not ret:
            return oneshare_json_fail_response(msg="change user info fail", **extra)

        # 修改手机号码
        sms_number = params.get("mobile", "").strip(" ")
        # fixme: 默认中国
        default_country_id = request.env.ref("base.cn")
        sanitize_res = phone_validation.phone_sanitize_numbers_w_record(
            [sms_number], record=None, country=default_country_id
        )[sms_number]
        mobile_phone = sanitize_res["sanitized"]
        if mobile_phone:
            ret = user_id.partner_id.write({"mobile": mobile_phone})
        else:
            return oneshare_json_fail_response(
                msg=f"change user: {login} mobile: {sms_number} Error: {sanitize_res['code']}",
                **extra,
            )
        if ret:
            cr.commit()
            return oneshare_json_success_resp(msg="change user info success", **extra)
        return oneshare_json_fail_response(msg="change user info fail", **extra)
