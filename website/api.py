# -*- coding: utf-8 -*-
from flask import Blueprint, request, json, session, url_for, g
from flask import current_app, url_for
import flask
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import md5

from models import Account
from models import Group
from models import Store
from models import Seller

from core import RoleType, MainException, EmailUsageType, ResponseMeta
from blueprint_utils import login_required
from blueprint_utils import require_basic_auth
from utils.func import init_logger
from utils.func import random_ascii_string

import config

LOGGER = init_logger(__name__)

api = Blueprint('api', __name__, url_prefix='/api')

def publish_message(rds, channel, msg):
    rds.publish(channel, msg)


##################user######################
@api.route('/login', methods=['POST'])
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


@api.route('/send_verify_email', methods=['POST'])
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

    db.begin()
    group_id = Group.create_group(db, appid, 0, '', False)
    store_id = Store.create_store(db, '', group_id, 0)
    account_id = Seller.add_seller(db, email, password, store_id, email, 0)
    Group.add_group_member(db, group_id, account_id)
    Account.insert_verify_email(db, email, code, EmailUsageType.SELLER_VERIFY, account_id)
    db.commit()

    content = "%d,%d,%d"%(group_id, appid, 0)
    publish_message(g.im_rds, "group_create", content)

    content = "%d,%d"%(group_id, account_id)
    publish_message(g.im_rds, "group_member_add", content)


    if 'user' not in session:
        session['user'] = {}

    session['user']['id'] = account_id
    session['user']['email'] = email
    session['user']['email_checked'] = 0
    session['user']['store_id'] = store_id
    session['user']['name'] = email

    account = {
        "id":account_id,
        "email":email,
        "email_checked":0,
    }

    send_verify_email(email, code, email_cb=url_for('account.register_valid', code='', _external=True))

    return send_response(account)


@api.route('/verify_email', methods=['POST'])
def verify_email():
    """
    """
    account_obj = _get_account(g._db)
    if not account_obj:
        raise MainException.ACCOUNT_NOT_FOUND

    if account_obj.get('email_checked'):
        raise MainException.ACCOUNT_EMAIL_CHECKED

    code = random_ascii_string(40)
    email = account_obj.get('email')

    send_verify_email(email, code, url_for('account.register_valid', code='', _external=True))
    Account.insert_verify_email(g._db, email, code, EmailUsageType.SELLER_VERIFY, account_obj.get('id'))

    return MainException.OK


@api.route('/send_reset_email', methods=['POST'])
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

    send_reset_email(email, code, url_for('web.password_forget_check', mail=email, code='', _external=True))
    
    Account.insert_verify_email(g._db, email, code, 
                                EmailUsageType.SELLER_RESET_PWD, 
                                account_obj['id'])

    return MainException.OK


@api.route('/change_password', methods=['PUT'])
@login_required
def me_password():
    account = _get_account(g._db)

    if not account:
        raise MainException.ACCOUNT_NOT_FOUND

    if request.data:
        data = json.loads(request.data)
        if check_password_hash(account.get('password'), data.get('old_value')):
            new_password = data.get('new_value')
            Account.reset_password(g._db, account.get('id'), new_password)
            return MainException.OK
        else:
            raise MainException.ACCOUNT_PASSWORD_WRONG
    else:
        raise MainException.ACCOUNT_PASSWORD_INVALID


@api.route('/reset_password', methods=['POST'])
def reset_password():
    if not request.data:
        raise MainException.ACCOUNT_PASSWORD_INVALID

    data = json.loads(request.data)
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

def make_response(status_code, data = None):
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
        mail.send_message("GoBelieve开发者平台邮箱验证",
                          recipients=[email],
                          html="感谢注册GoBelieve开发者平台，使用GoBelieve开发者服务。<br/>"
                               "请点击以下按钮进行邮箱验证，以便您正常使用GoBelieve开发者平台的更多功能：<br/>"
                               "<a href=\"{url}\">马上验证邮箱</a> <br/>"
                               "如果您无法点击以上链接，请复制以下网址到浏览器里直接打开：<br/>"
                               "{url} <br/>"
                               "如果您并未申请GoBelieve开发者平台的相关服务，可能是其他用户误输入了您的邮箱地址。请忽略此邮件。".format(url=url))
    except Exception, e:
        logging.exception(e)


def send_reset_email(code, email_cb):
    mail = current_app.extensions.get('mail')
    if email_cb == 'debug':
        url = url_for('.reset_password', code=code, _external=True)
    else:
        url = email_cb + code
    try:
        mail.send_message("GoBelieve开发者平台密码重置",
                          recipients=[self.email],
                          html="本邮件是应您在GoBelieve开发者平台上提交的重置密码请求，从而发到您邮箱的重置密码的邮件。<br/>"
                               "如果您没有提交重置密码请求而收到此邮件，我们非常抱歉打扰您，请忽略本邮件。<br/>"
                               "要重置您在GoBelieve开发者平台上的用户密码，请点击以下链接：<br/>"
                               "<a href=\"{url}\">密码重置</a> <br/>"
                               "该链接会在浏览器上打开一个页面，让您来重设密码。如果无法点击请复制到浏览器地址栏里：<br/>"
                               "{url} <br/>"
                               "上述地址24小时内有效。".format(url=url))
    except Exception, e:
        logging.exception(e)

