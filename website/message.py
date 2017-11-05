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
from flask import render_template, render_template_string
import hashlib

from website.blueprint_utils import login_required
from utils.parse import Parse
from utils.reply import Reply
from utils.WXBizMsgCrypt import WXBizMsgCrypt
from utils.func import random_ascii_string
from utils.fs import FS
from utils.func import get_image_size
from utils.func import amr_duration
from utils.func import UnknownImageFormat
import random

import config

if config.DEBUG:
    #使用代理服务器访问微信接口
    from utils.wx import WXOpenAPI2 as WXOpenAPI
    from utils.wx import WXMPAPI2 as WXMPAPI
else:
    from utils.wx import WXOpenAPI
    from utils.wx import WXMPAPI

import redis
import logging
import sys
import time
import json
import md5
import struct
import math
import requests

from models import Seller
from models import WX
from models import WXUser
from models import App
from models import Client
from models import Supporter

root = Blueprint('message', __name__, template_folder='templates', static_folder='static')

TOKEN = config.WX_TOKEN
ENCODING_AES_KEY = config.WX_ENCODING_AES_KEY
APPID = config.WX_COMPONENT_APPID
APPSECRET = config.WX_COMPONENT_APPSECRET

from wx_token import get_user
from wx_token import get_access_token
from wx_token import gen_pre_auth_code
from wx_token import get_component_access_token

def _im_login_required(f):
    return login_required(f, redirect_url_for='.wx_index')


def send_customer_message(customer_appid, customer_id, store_id, 
                          seller_id, content):
    url = config.IM_RPC_URL + "/post_customer_message"
    obj = {"customer_appid":customer_appid, "customer_id":customer_id, 
           "store_id":store_id, "seller_id":seller_id, "content":content}

    try:
        res = requests.post(url, data=json.dumps(obj))
        if res.status_code != 200:
            logging.warning("login error:%s %s", res.status_code, res.text)
            return False
        else:
            logging.debug("send customer message success")
            return True
    except Exception, e:
        logging.error("send customer message exception:%s", e)
        return False


def check_signature(signature, timestamp, nonce):
    arr = [TOKEN, timestamp, nonce]
    arr.sort()
    tmpstr = "%s%s%s" % tuple(arr)
    tmpstr = hashlib.sha1(tmpstr).hexdigest()

    return tmpstr == signature

@root.route("/wx/test_auth")
def test_auth():
    rds = g.im_rds
    db = g._db
    pre_auth_code = gen_pre_auth_code(rds)
    if not pre_auth_code:
        return "error"

    seller_id = 100088
    redirect_uri = url_for(".auth_callback", uid=seller_id, _external=True)
    return render_template("wx/test_auth.html", appid=APPID, pre_auth_code=pre_auth_code, redirect_uri=redirect_uri)

    
@root.route("/wx/auth")
@_im_login_required
def auth():
    rds = g.im_rds
    db = g._db
    pre_auth_code = gen_pre_auth_code(rds)
    if not pre_auth_code:
        return "error"

    seller_id = session['user']['id']
    redirect_uri = url_for(".auth_callback", uid=seller_id, _external=True)
    return render_template("wx/auth.html", appid=APPID, pre_auth_code=pre_auth_code, redirect_uri=redirect_uri)

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

    logging.debug("auth callback code:%s uid:%s store_id:%s", 
                  auth_code, uid, store_id)

    component_token = get_component_access_token(rds)
    if not component_token:
        return "授权失败"

    wx = WXOpenAPI(APPID, APPSECRET, component_token)
    r = wx.request_auth(auth_code)
    if r:
        info = r['authorization_info']
        logging.debug("auth callback info:%s", info)
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

        is_app = False
        AUTHORIZATION_MESSAGE = 1
        AUTHORIZATION_CONTACT = 19
        if AUTHORIZATION_MESSAGE in fids:
            #公众号
            is_app = False
        elif AUTHORIZATION_CONTACT in fids:
            #小程序
            is_app = True
        else:
            logging.warning("no message authorization")
            return "没有消息权限"

        app_info = wx.request_info(wx_appid)
        if not app_info:
            logging.warning("request app info fail")
            return "获取公众号信息失败"
        name = app_info['authorizer_info']['nick_name']
        gh_id = app_info['authorizer_info']['user_name']

        app = App.get_wx(db, wx_appid)
        if app:
            Client.update_wx(db, wx_appid, refresh_token, 1)
            if app['store_id'] != 0 and app['store_id'] != store_id:
                return "已被其它账号授权"
            if app['store_id'] == 0:
                App.set_store_id(db, app['id'], store_id)
        else:
            App.create_wx(db, name, gh_id, wx_appid, refresh_token, store_id, is_app)
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


def handle_unauthorized(authorizer_appid):
    db = g._db
    Client.set_wx_unauthorized(db, authorizer_appid)

def handle_authorized(data):
    authorizer_appid = data.get('AuthorizerAppid')
    authorization_code = data.get('AuthorizationCode')
    code_expire = data.get('AuthorizationCodeExpiredTime')

    logging.debug("authorized appid:%s code:%s expire:%s", 
                  authorizer_appid, authorization_code, code_expire)

    rds = g.im_rds
    db = g._db
    auth_code = authorization_code
    store_id = 0

    component_token = get_component_access_token(rds)
    if not component_token:
        return "授权失败"

    wx = WXOpenAPI(APPID, APPSECRET, component_token)
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

        is_app = False
        AUTHORIZATION_MESSAGE = 1
        AUTHORIZATION_CONTACT = 19
        if AUTHORIZATION_MESSAGE in fids:
            #公众号
            is_app = False
        elif AUTHORIZATION_CONTACT in fids:
            #小程序
            is_app = True
        else:
            logging.warning("no message authorization")
            return "没有消息权限"

        app_info = wx.request_info(wx_appid)
        if not app_info:
            logging.warning("request app info fail")
            return "获取公众号信息失败"
        name = app_info['authorizer_info']['nick_name']
        gh_id = app_info['authorizer_info']['user_name']

        app = App.get_wx(db, wx_appid)
        if app:
            Client.update_wx(db, wx_appid, refresh_token, 1)
            if app['store_id'] != 0 and app['store_id'] != store_id:
                return "已被其它账号授权"
        else:
            App.create_wx(db, name, gh_id, wx_appid, refresh_token, store_id, is_app)
        WX.set_access_token(rds, wx_appid, access_token, expires_in)
        return "授权成功"
    else:
        return "获取令牌失败"

def handle_ticket(data):
    rds = g.im_rds
    appid = data.get("AppId")
    create_time = data.get("CreateTime")
    ticket = data.get('ComponentVerifyTicket')
    logging.debug("appid:%s create time:%s ticket:%s", 
                  appid, create_time, ticket)

    WX.set_ticket(rds, ticket)


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

    try:
        data = Parse.parse(request.data)
        encrypted_data = data.get("Encrypt")
        wx_crypt = WXBizMsgCrypt(TOKEN, ENCODING_AES_KEY, APPID)
        r, xml = wx_crypt.DecryptTicket(request.data, msg_signature, timestamp, nonce)
        logging.debug("ret:%s xml:%s", r, xml)
        if r == 0 and xml:
            data = Parse.parse(xml)
    except Exception, e:
        logging.error("exception:%s", e)
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


def get_one_supporter(db, rds, store_id):
    online_sellers = []
    sellers = Seller.get_sellers(db, store_id)

    if not sellers:
        return None

    for seller in sellers:
        status = Supporter.get_user_status(rds, seller['id'])
        seller['status'] = status
        if status == Supporter.STATUS_ONLINE:
            online_sellers.append(seller)

    if len(online_sellers) == 0:
        #假设第一个客服是管理员
        seller = sellers[0]
    else:
        index = random.randint(0, len(online_sellers) - 1)
        seller = sellers[index]

    name = ""
    if seller.has_key('name') and seller['name']:
        name = seller['name'].split('@')[0]

    resp = {
        "seller_id":seller['id'], 
        "name":name,
        "status":seller["status"]
    }
    return resp


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

    logging.debug("receive wx message:%s %s %s", wx_appid, r, xml)

    data = Parse.parse(xml)
    msg_type = data.get('MsgType')

    # 接收到事件
    if msg_type == 'event':
        logging.debug("event:%s", data.get('Event'))
        event = data.get('Event')
        session = data.get('SessionFrom')
        openid = data.get('FromUserName')
        gh_id = data.get('ToUserName')
        if event == 'user_enter_tempsession' and session:
            #设置来自小程序的微信用户名
            u = get_user(rds, db, gh_id, openid)
            if u:
                logging.debug("set user name:%s %s %s", gh_id, openid, session)
                WXUser.set_user_name(rds, u.appid, u.uid, session)
        return ''
    # 接收到其他消息
    else:
        openid = data.get('FromUserName')
        gh_id = data.get('ToUserName')

        # 消息格式检查
        if msg_type not in ('text', 'image', 'voice', 'location'):
            msg = Reply.text(openid, gh_id, '该消息格式不支持, 目前只支持文本,图片,语音,位置')
            _, m = wx_crypt.EncryptMsg(msg, nonce, timestamp)
            return m

        logging.debug("msg:%s %s %s", openid, gh_id, msg_type)

        u = get_user(rds, db, gh_id, openid)
        logging.debug("appid:%s uid:%s store id:%s seller id:%s", u.appid, u.uid, u.store_id, u.seller_id)
        if msg_type == 'text':
            content = data.get('Content')
            logging.debug("text content:%s", content)
            obj = {"text":content}
        elif msg_type == 'location':
            x = data.get("Location_X")
            y = data.get("Location_Y")
            obj = {"location":{"latitude":x, "longitude":y}}
        elif msg_type == 'image':
            access_token = get_access_token(rds, db, u.wx_appid)
            if not access_token:
                logging.error("can't get access token")
                return ''

            mp = WXMPAPI(access_token)
            media = mp.get_media(data.get("MediaId"))
            try:
                width, height = get_image_size(media)
            except UnknownImageFormat, e:
                width = 0
                height = 0
   
            ext = ".jpg"
            name = md5.new(media).hexdigest()
            path = "/images/" + name + ext
            r = FS.upload(path, media)
            if not r:
                logging.error("fs upload image error")
                return ''

            url = config.IM_URL + "/images/" + name + ext
            image2 = {"url":url, "width":width, "height":height}
            obj = {"image":url, "image2":image2}
            logging.debug("image url:%s width:%s height:%s", url, width, height)
        elif msg_type == 'voice':
            access_token = get_access_token(rds, db, u.wx_appid)
            if not access_token:
                logging.error("can't get access token")
                return ''

            mp = WXMPAPI(access_token)
            media = mp.get_media(data.get("MediaId"))

            md5_value = md5.new(media).hexdigest()
            path = "/audios/" + md5_value
            r = FS.upload(path, media)
            if not r:
                logging.error("fs upload audio error")
                return ''

            duration = amr_duration(media)
            url = config.IM_URL + "/audios/" + md5_value
            obj = {"audio":{"url":url, "duration":duration}}
        else:
            logging.debug("unsupport msg type:%s", msg_type)
            obj = None

        now = int(time.time())
        if u.seller_id == 0:
            seller = get_one_supporter(db, rds, u.store_id)
            if not seller:
                logging.warning("no supporter:%d", u.store_id)
            else:
                logging.debug("got seller id:%s", seller['seller_id'])
                WXUser.set_seller_id(rds, gh_id, openid, seller['seller_id'])
                WXUser.set_seller_timestamp(rds, gh_id, openid, now)
                u.seller_id = seller['seller_id']
        elif now - u.seller_timestamp > 3600:
            sellers = Seller.get_sellers(db, u.store_id)
            if not sellers:
                raise ResponseMeta(400, 'store no supporter')

            deleted = True
            for s in sellers:
                if s['id'] == u.seller_id:
                    deleted = False
                    break
                            
            if not deleted:
                WXUser.set_seller_timestamp(rds, gh_id, openid, now)
            else:
                #客服已经被删除
                seller = get_one_supporter(db, rds, u.store_id)
                if not seller:
                    logging.warning("no supporter:%d", u.store_id)
                    u.seller_id = 0
                else:
                    WXUser.set_seller_id(rds, gh_id, openid, seller['seller_id'])
                    WXUser.set_seller_timestamp(rds, gh_id, openid, now)
                    u.seller_id = seller['seller_id']


        if obj and u.seller_id:
            c = json.dumps(obj)
            logging.debug("send customer message store id:%s seller_id:%s content:%s", u.store_id, u.seller_id, c)
            send_customer_message(u.appid, u.uid, u.store_id, u.seller_id, c)
        
        if u.seller_id == 0:
            #todo raise exception
            pass

    return ''



@root.route('/wx/contact')
def validate_contact():
    req = request.args
    signature = req.get('signature', '')
    timestamp = req.get('timestamp', '')
    nonce = req.get('nonce', '')
    echostr = req.get('echostr')
    if check_signature(signature, timestamp, nonce):
        return echostr
    else:
        return ''

@root.route('/wx/contact', methods=['POST'])
def wx_contact():
    req = request.args
    signature = req.get('signature', '')
    timestamp = req.get('timestamp', '')
    nonce = req.get('nonce', '')
    if not check_signature(signature, timestamp, nonce):
        logging.warning("check signature fail")
        return ''

    logging.debug("req args:%s", req)
    logging.debug("data:%s", request.data)
    return 'success'
