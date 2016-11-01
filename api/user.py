# -*- coding: utf-8 -*-
from flask import request, json, session, g
from flask import current_app, url_for
import flask
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import time

from models import Account
from models import Store
from models import Seller

from exception import MainException
from models.core import EmailUsageType
from blueprint_utils import login_required
from utils.func import init_logger
from utils.func import random_ascii_string

from blueprint import api

import config

LOGGER = init_logger(__name__)


def publish_message(rds, channel, msg):
    rds.publish(channel, msg)


##################user######################
@api.route('/user/login', methods=['POST'])
def login_post():
    """
    """
    account_obj = _get_account_by_email(g._db, request.form.get('email', ''))
    if account_obj:
        print account_obj
        account_password = account_obj.get('password')
        password = request.form.get('password', '')
        if check_password_hash(account_password, password):
            account = account_obj
        else:
            raise MainException.ACCOUNT_PASSWORD_WRONG
    else:
        raise MainException.ACCOUNT_NOT_FOUND

    if not account_obj.get('email_checked'):
        raise MainException.ACCOUNT_EMAIL_NOT_CHECK

    if 'user' not in session:
        session['user'] = {}

    LOGGER.debug("account:%s", account)
    if account:
        session['user']['name'] = account.get('name')
        session['user']['id'] = account.get('id')
        session['user']['email'] = account.get('email')
        session['user']['email_checked'] = account.get('email_checked')
        session['user']['store_id'] = account.get('store_id')

    return send_response(account)


@api.route('/user/send_verify_email', methods=['POST'])
def verify_mail():
    """
    """
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    password = generate_password_hash(password)

    account_obj = _get_account_by_email(g._db, email)
    if account_obj:
        raise MainException.ACCOUNT_DUPLICATE

    code = random_ascii_string(40)

    appid = config.KEFU_APPID
    db = g._db

    mode = 1  # fix_mode
    db.begin()
    store_id = Store.create_store(db, '', 0, mode, 0)
    account_id = Seller.add_seller(db, email, password, store_id, email, 0)
    Account.insert_verify_email(db, email, code, EmailUsageType.SELLER_VERIFY, account_id)
    db.commit()

    Store.add_seller_id(g.im_rds, store_id, account_id)

    account = {
        "id": account_id,
        "email": email,
        "email_checked": 0,
    }

    send_verify_email(email, code, email_cb=url_for('account.register_valid', code='', _external=True))

    return send_response(account)


@api.route('/user/resend_verify_email', methods=['POST'])
def user_verify_email():
    """
    """
    email = request.form.get('email', '')
    account_obj = Account.get_account_with_email(g._db, email)
    if not account_obj:
        raise MainException.ACCOUNT_NOT_FOUND

    if account_obj.get('email_checked'):
        raise MainException.ACCOUNT_EMAIL_CHECKED

    code = random_ascii_string(40)
    email = account_obj.get('email')

    send_verify_email(email, code, url_for('account.register_valid', code='', _external=True))
    Account.insert_verify_email(g._db, email, code, EmailUsageType.SELLER_VERIFY, account_obj.get('id'))

    return MainException.OK


@api.route('/user/valid', methods=['POST'])
def register_valid():
    code = request.form.get('code', '')

    expires_in = 86400

    if code:
        verify_email = Account.get_verify_email(g._db, code)

        if not verify_email:
            raise MainException.ACCOUNT_INVALID_EMAIL_CODE

        if verify_email['usage_type'] != EmailUsageType.SELLER_VERIFY:
            raise MainException.ACCOUNT_INVALID_EMAIL_CODE

        account_obj = Account.get_account(g._db, verify_email['ro_id'])

        confirm = False
        if account_obj and \
                verify_email and \
                        account_obj['id'] == verify_email['ro_id'] and \
                                verify_email['ctime'] + expires_in > time.time():
            confirm = True

        Account.delete_verify_email(g._db, code, EmailUsageType.SELLER_VERIFY)
        if confirm:
            Account.set_email_checked(g._db, verify_email['ro_id'], 1)
            return make_response(200)
        else:
            error = '确认邮件失败'
            logging.debug("error:%s %s %s %s", error, account_obj, verify_email, session['user'])
            return MainException.ACCOUNT_INVALID_EMAIL_CODE
    else:
        return MainException.ACCOUNT_INVALID_EMAIL_CODE


@api.route('/user/send_reset_email', methods=['POST'])
def reset_mail():
    """
    """
    email = request.form.get('email', '')

    if not email:
        raise MainException.ACCOUNT_NOT_FOUND

    account_obj = _get_account_by_email(g._db, email)
    if not account_obj:
        raise MainException.ACCOUNT_NOT_FOUND

    count = Account.get_verify_count(g._db, email)
    if count > 5:
        raise MainException.EMAIL_TOO_OFTEN

    code = random_ascii_string(40)

    send_reset_email(email, code, url_for('account.password_forget_check', mail=email, code='', _external=True))

    Account.insert_verify_email(g._db, email, code,
                                EmailUsageType.SELLER_RESET_PWD,
                                account_obj['id'])

    return MainException.OK


@api.route('/user/change_password', methods=['POST'])
@login_required
def me_password():
    account = _get_account(g._db)

    if not account:
        raise MainException.ACCOUNT_NOT_FOUND

    if request.form:
        data = request.form
        if check_password_hash(account.get('password'), data.get('old_value')):
            new_password = data.get('new_value')
            Account.reset_password(g._db, account.get('id'), new_password)
            return MainException.OK
        else:
            raise MainException.ACCOUNT_PASSWORD_WRONG
    else:
        raise MainException.ACCOUNT_PASSWORD_INVALID


@api.route('/user/reset_password', methods=['POST'])
def reset_password():
    if not request.form:
        raise MainException.ACCOUNT_PASSWORD_INVALID

    data = request.form
    code = data.get('code')
    password = data.get('password')
    password = generate_password_hash(password)

    if code:
        verify_email = Account.get_verify_email(g._db, code, EmailUsageType.SELLER_RESET_PWD)
        if verify_email:
            seller_id = verify_email['ro_id']
            Seller.set_seller_password(g._db, 0, seller_id, password)
            return MainException.OK

    raise MainException.ACCOUNT_INVALID_EMAIL_CODE


def _get_account(db):
    if 'user' in session:
        account_obj = Account.get_account(db, session['user']['id'])
        if not account_obj:
            raise None
        return account_obj
    else:
        return None


def _get_account_by_email(db, email):
    account = Account.get_account_with_email(db, email)
    return account


def send_response(result):
    response = flask.make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'

    return response


def make_response(status_code, data=None):
    if data:
        res = flask.make_response(json.dumps(data), status_code)
        res.headers['Content-Type'] = "application/json"
    else:
        res = flask.make_response("", status_code)

    return res


def send_verify_email(email, code, email_cb):
    if email_cb is None:
        return
    mail = current_app.extensions.get('mail')
    if email_cb == 'debug':
        url = url_for('.confirm_email', code=code, _external=True)
    else:
        url = email_cb + code

    try:
        mail.send_message("小微客服邮箱验证",
                          recipients=[email],
                          html="感谢注册小微客服。<br/>"
                               "请点击以下按钮进行邮箱验证：<br/>"
                               "<a href=\"{url}\">马上验证邮箱</a> <br/>"
                               "如果您无法点击以上链接，请复制以下网址到浏览器里直接打开：<br/>"
                               "{url} <br/>"
                               "如果您并未申请小微客服，可能是其他用户误输入了您的邮箱地址。请忽略此邮件。".format(url=url))
    except Exception, e:
        logging.exception(e)


def send_reset_email(email, code, email_cb):
    mail = current_app.extensions.get('mail')
    if email_cb == 'debug':
        url = url_for('.reset_password', code=code, _external=True)
    else:
        url = email_cb + code
    try:
        mail.send_message("小微客服密码重置",
                          recipients=[email],
                          html="本邮件是应您在小微客服上提交的重置密码请求，从而发到您邮箱的重置密码的邮件。<br/>"
                               "如果您没有提交重置密码请求而收到此邮件，我们非常抱歉打扰您，请忽略本邮件。<br/>"
                               "要重置您在小微客服的用户密码，请点击以下链接：<br/>"
                               "<a href=\"{url}\">密码重置</a> <br/>"
                               "该链接会在浏览器上打开一个页面，让您来重设密码。如果无法点击请复制到浏览器地址栏里：<br/>"
                               "{url} <br/>"
                               "上述地址24小时内有效。".format(url=url))
    except Exception, e:
        logging.exception(e)
