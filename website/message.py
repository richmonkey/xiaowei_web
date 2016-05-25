# -*- coding: utf-8 -*-
"""
微信回调请求
"""
from flask import request
from flask import Flask
from flask import Blueprint
from flask import url_for
from flask import g
from flask import session
from flask import render_template_string
import hashlib

from website.blueprint_utils import login_required
from utils.parse import Parse
from utils.reply import Reply
from utils.WXBizMsgCrypt import WXBizMsgCrypt
from utils.func import random_ascii_string

import config

if config.DEBUG:
    #使用代理服务器访问微信接口
    from utils.wx import WXAPI2 as WXAPI
else:
    from utils.wx import WXAPI

import redis
import logging
import sys
import time
import json
import requests

from utils.mysql import Mysql
from models import Seller
from models import WX
from models import WXUser
from models import App
from models import Client

root = Blueprint('message', __name__, template_folder='templates', static_folder='static')

TOKEN = config.WX_TOKEN
ENCODING_AES_KEY = config.WX_ENCODING_AES_KEY
APPID = config.WX_COMPONENT_APPID
APPSECRET = config.WX_COMPONENT_APPSECRET

def _im_login_required(f):
    return login_required(f, redirect_url_for='.wx_index')


def send_customer_message(customer_appid, customer_id, store_id, 
                          seller_id, content):
    url = config.IM_RPC_URL + "/post_customer_message"
    obj = {"customer_appid":customer_appid, "customer_id":customer_id, 
           "store_id":store_id, "seller_id":seller_id, "content":content}
     
    res = requests.post(url, data=json.dumps(obj))
    if res.status_code != 200:
        logging.warning("login error:%s %s", res.status_code, res.text)
        return 0
    else:
        logging.debug("send customer message success")
        obj = json.loads(res.content)
        return obj['data']['seller_id']


def check_signature(signature, timestamp, nonce):
    arr = [TOKEN, timestamp, nonce]
    arr.sort()
    tmpstr = "%s%s%s" % tuple(arr)
    tmpstr = hashlib.sha1(tmpstr).hexdigest()

    return tmpstr == signature


auth_html = """
<!DOCTYPE html>
<html>
    <head>
    </head>
    <body>
      <a href="https://mp.weixin.qq.com/cgi-bin/componentloginpage?component_appid={{ appid }}&pre_auth_code={{ pre_auth_code }}&redirect_uri={{ redirect_uri }}">微信公众号登陆授权</a>
    </body>
</html>
"""

@root.route("/wx/test_auth")
def test_auth():
    rds = g.im_rds
    db = g._db
    pre_auth_code = WX.get_pre_auth_code(rds)
    if not pre_auth_code:
        pre_auth_code = gen_pre_auth_code(rds)
        if not pre_auth_code:
            return "error"

    seller_id = 100073
    redirect_uri = url_for(".auth_callback", uid=seller_id, _external=True)
    return render_template_string(auth_html, appid=APPID, pre_auth_code=pre_auth_code, redirect_uri=redirect_uri)

    
@root.route("/wx/auth")
@_im_login_required
def auth():
    rds = g.im_rds
    db = g._db
    pre_auth_code = WX.get_pre_auth_code(rds)
    if not pre_auth_code:
        pre_auth_code = gen_pre_auth_code(rds)
        if not pre_auth_code:
            return "error"

    seller_id = session['user']['id']
    redirect_uri = url_for(".auth_callback", uid=seller_id, _external=True)
    return render_template_string(auth_html, appid=APPID, pre_auth_code=pre_auth_code, redirect_uri=redirect_uri)

@root.route('/wx/auth/<int:uid>/callback')
def auth_callback(uid):
    rds = g.im_rds
    db = g._db
    auth_code = request.args.get('auth_code')
    expires_in = request.args.get('expires_in')
    if not auth_code or not expires_in:
        return "非法调用"

    seller = Seller.get_seller(db, uid)
    store_id = seller['store_id']

    component_token = get_component_access_token(rds)
    if not component_token:
        return "授权失败"

    wx = WXAPI(APPID, APPSECRET, component_token)
    r = wx.request_auth(auth_code)
    if r:
        info = r['authorization_info']
        wx_appid = info['authorizer_appid']
        access_token = info['authorizer_access_token']
        expires_in = info['expires_in']
        #提前10分钟过期
        if expires_in > 20*60:
            expires_in = expires_in - 10*60

        refresh_token = info['authorizer_refresh_token']
        funcs = info['func_info']
        fids = []
        for f in funcs:
            fid = f['funcscope_category']['id']
            fids.append(fid)
        
        AUTHORIZATION_MESSAGE = 1
        if AUTHORIZATION_MESSAGE not in fids:
            logging.warning("no message authorization")
            return "没有消息权限"

        app_info = wx.request_info(wx_appid)
        if not app_info:
            logging.warning("request app info fail")
            return "获取公众号信息失败"
        name = app_info['authorizer_info']['nick_name']
        gh_id = app_info['authorizer_info']['user_name']

        app = Client.get_wx(db, wx_appid)
        if app:
            if app['store_id'] != store_id:
                return "已被其它账号授权"
            Client.update_wx(db, wx_appid, refresh_token, 1)
        else:
            App.create_wx(db, name, gh_id, wx_appid, refresh_token, store_id)
        WX.set_access_token(rds, wx_appid, access_token, expires_in)
        return "授权成功"
    else:
        return "获取令牌失败"

@root.route('/wx/messages')
def validate():
    req = request.args
    signature = req.get('signature', '')
    timestamp = req.get('timestamp', '')
    nonce = req.get('nonce', '')
    echostr = req.get('echostr')
    if check_signature(signature, timestamp, nonce):
        return echostr
    else:
        return ''

def get_component_access_token(rds):
    component_token = WX.get_component_access_token(rds)
    if not component_token:
        ticket = WX.get_ticket(rds)
        if not ticket:
            return None

        wx = WXAPI(APPID, APPSECRET)
        r = wx.request_token(ticket)
        logging.debug("request token:%s", r)
        if r.get('errcode'):
            logging.error("request token error:%s %s", 
                          r['errcode'], r['errmsg'])
            return None

        access_token = r['component_access_token']
        expires = r['expires_in']
        #提前10分钟过期
        if expires > 20*60:
            expires = expires - 10*60
        logging.debug("request component access token:%s expires:%s", 
                      access_token, r['expires_in'])
        WX.set_componet_access_token(rds, access_token, expires)
        
        component_token = access_token

    return component_token

def gen_pre_auth_code(rds):
    access_token = get_component_access_token(rds)
    if not access_token:
        return None

    wx = WXAPI(APPID, APPSECRET, access_token)
    r = wx.request_pre_auth_code()
    if r.get('errcode'):
        logging.error("request pre auth code error:%s %s", 
                      r['errcode'], r['errmsg'])
        return None
    
    pre_auth_code = r['pre_auth_code']
    expires = r['expires_in']
    #提前5分钟过期
    if expires > 10*60:
        expires = expires - 5*60
    WX.set_pre_auth_code(rds, pre_auth_code, expires)
    logging.debug("request pre auth code:%s expires:%s", 
                  pre_auth_code, r['expires_in'])
    
    return pre_auth_code

def handle_unauthorized(authorizer_appid):
    db = g._db
    Client.set_wx_unauthorized(db, authorizer_appid)

def handle_authorized(data):
    authorizer_appid = data.get('AuthorizerAppid')
    authorization_code = data.get('AuthorizationCode')
    code_expire = data.get('AuthorizationCodeExpiredTime')

    logging.debug("authorized appid:%s code:%s expire:%s", 
                  authorizer_appid, authorization_code, code_expire)
        

def handle_ticket(data):
    rds = g.im_rds
    appid = data.get("AppId")
    create_time = data.get("CreateTime")
    ticket = data.get('ComponentVerifyTicket')
    logging.debug("appid:%s create time:%s ticket:%s", 
                  appid, create_time, ticket)

    WX.set_ticket(rds, ticket)
    pre_auth_code = WX.get_pre_auth_code(rds)
    if not pre_auth_code:
        gen_pre_auth_code(rds)


@root.route("/wx/test", methods=['GET'])
def test():
    #ticket = "ticket@@@Ro4TsP70suthsnwUul98DWqxhQN6MA74xhAzhwui7RocSEWpb8mz89g5149p4-rW2CERrAclp9v9mzl5KR80lg"

    #handle_ticket(ticket)
    #authorizer_appid = 'wx1f07af5198cd5c3a'
    #handle_unauthorized(authorizer_appid)
    return ''

@root.route('/wx/messages', methods=['POST'])
def wx_message():
    req = request.args
    signature = req.get('signature', '')
    timestamp = req.get('timestamp', '')
    nonce = req.get('nonce', '')
    if not check_signature(signature, timestamp, nonce):
        logging.warning("check signature fail")
        return ''

    logging.debug("req args:%s", req)
    logging.debug("data:%s", request.data)
    msg_signature = req.get('msg_signature')
    if not msg_signature:
        logging.warning("msg signature is None")
        return ''

    wx_crypt = WXBizMsgCrypt(TOKEN, ENCODING_AES_KEY, APPID)
    r, xml = wx_crypt.DecryptTicket(request.data, msg_signature, timestamp, nonce)
    logging.debug("ret:%s xml:%s", r, xml)
    data = Parse.parse(xml)

    info_type = data.get('InfoType')
    logging.debug("info type:%s", info_type)
    if info_type == "component_verify_ticket":
        handle_ticket(data)
    elif info_type == 'authorized':
        handle_authorized(data)
    elif info_type == 'unauthorized':
        authorizer_appid = data.get('AuthorizerAppid')
        handle_unauthorized(authorizer_appid)
    else:
        pass

    return 'success'


@root.route('/wx/<wx_appid>/callback', methods=['POST'])
def receive(wx_appid):
    db = g._db
    rds = g.im_rds
    req = request.args
    signature = req.get('signature', '')
    timestamp = req.get('timestamp', '')
    nonce = req.get('nonce', '')
    if not check_signature(signature, timestamp, nonce):
        logging.warning("check signature fail")
        return ''

    msg_signature = req.get('msg_signature')
    if not msg_signature:
        logging.warning("msg signature is None")
        return ''

    wx_crypt = WXBizMsgCrypt(TOKEN, ENCODING_AES_KEY, APPID)
    r, xml = wx_crypt.DecryptMsg(request.data, msg_signature, timestamp, nonce)

    logging.debug("receive:%s %s %s", wx_appid, r, xml)

    data = Parse.parse(xml)
    msg_type = data.get('MsgType')

    # 接收到事件
    if msg_type == 'event':
        logging.debug("event:%s", data.get('Event'))
        return ''
    # 接收到其他消息
    else:
        openid = data.get('FromUserName')
        gh_id = data.get('ToUserName')

        # 消息格式检查
        if msg_type not in ('text', 'image', 'voice'):
            return Reply.text(openid, gh_id, '该消息格式不支持, 目前只支持文本,图片或者语音')

        content = data.get('Content')
        logging.debug("msg:%s %s %s %s", openid, gh_id, msg_type, content)

        u = WXUser.get_wx_user(rds, gh_id, openid)
        if not u:
            wx = App.get_wx(db, gh_id)
            if not wx:
                logging.error("invalid gh_id:%s", gh_id)
                return ''

            store_id = Client.get_store_id(db, gh_id)
            if not store_id:
                logging.error("can't find store id with gh_id:%s", gh_id)
                return ''
            
            uid = WXUser.gen_id(rds)
            u = WXUser()
            u.gh_id = gh_id
            u.openid = openid
            u.appid = wx.appid
            u.uid = uid
            u.store_id = store_id
            u.seller_id = 0
            WXUser.save_wx_user(rds, u)
            WXUser.bind_openid(rds, u.appid, u.uid, openid)

        logging.debug("store id:%s seller id:%s", u.store_id, u.seller_id)
        if msg_type == 'text':
            obj = {"text":content}
            c = json.dumps(obj)
            seller_id = send_customer_message(u.appid, u.uid, u.store_id, u.seller_id, c)
            if seller_id != u.seller_id:
                WXUser.set_seller_id(rds, gh_id, openid, seller_id)
        else:
            logging.debug("unsupport msg type:%s", msg_type)

    return ''
