# -*- coding: utf-8 -*-
import logging
import sys
import time
import json
import requests

from models import Seller
from models import WX
from models import WXUser
from models import App
from models import Client

import config

if config.DEBUG:
    #使用代理服务器访问微信接口
    from utils.wx import WXOpenAPI2 as WXOpenAPI
    from utils.wx import WXMPAPI2 as WXMPAPI
else:
    from utils.wx import WXOpenAPI
    from utils.wx import WXMPAPI

TOKEN = config.WX_TOKEN
ENCODING_AES_KEY = config.WX_ENCODING_AES_KEY
APPID = config.WX_COMPONENT_APPID
APPSECRET = config.WX_COMPONENT_APPSECRET


def get_component_access_token(rds):
    component_token = WX.get_component_access_token(rds)
    if not component_token:
        ticket = WX.get_ticket(rds)
        if not ticket:
            return None

        wx = WXOpenAPI(APPID, APPSECRET)
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

    wx = WXOpenAPI(APPID, APPSECRET, access_token)
    r = wx.request_pre_auth_code()
    if r.get('errcode'):
        logging.error("request pre auth code error:%s %s", 
                      r['errcode'], r['errmsg'])
        return None
    
    pre_auth_code = r['pre_auth_code']
    expires = r['expires_in']
    logging.debug("request pre auth code:%s expires:%s", 
                  pre_auth_code, r['expires_in'])
    
    return pre_auth_code

def get_access_token(rds, db, wx_appid):
    access_token = WX.get_access_token(rds, wx_appid)
    if not access_token:
        app = App.get_wx(db, wx_appid)
        if not app:
            return None
        refresh_token = app['refresh_token']

        component_token = get_component_access_token(rds)
        if not component_token:
            return None

        wx = WXOpenAPI(APPID, APPSECRET, component_token)

        r = wx.refresh_auth(wx_appid, refresh_token)

        if r.get('errcode'):
            logging.error("refresh auto error:%s %s", 
                          r['errcode'], r['errmsg'])
            return None

        token = r['authorizer_access_token']
        expires = r['expires_in']
        authorizer_refresh_token = r['authorizer_refresh_token']

        #提前10分钟过期
        if expires > 20*60:
            expires = expires - 10*60

        if authorizer_refresh_token != refresh_token:
            logging.error("old refresh token:%s new refresh token:%s", 
                          refresh_token, authorizer_refresh_token)
        else:
            logging.debug("refresh token is unchanged")

        WX.set_access_token(rds, wx_appid, token, expires)
        access_token = token

    return access_token


def get_user(rds, db, gh_id, openid):
    now = int(time.time())
    u = WXUser.get_wx_user(rds, gh_id, openid)
    if not u:
        wx = App.get_wx_by_ghid(db, gh_id)
        if not wx:
            logging.error("invalid gh_id:%s", gh_id)
            return None

        store_id = wx['store_id']
        if not store_id:
            logging.error("can't find store id with gh_id:%s", gh_id)
            return None

        access_token = get_access_token(rds, db, wx['wx_app_id'])
        if not access_token:
            logging.error("can't get access token")
            return None

        mp = WXMPAPI(access_token)

        
        uid = WXUser.gen_id(rds)
        u = WXUser()
        u.gh_id = gh_id
        u.openid = openid
        u.appid = wx['appid']
        u.wx_appid = wx['wx_app_id']
        u.uid = uid
        u.store_id = store_id
        u.timestamp = now
        u.seller_id = 0
        WXUser.save_wx_user(rds, u)
        WXUser.bind_openid(rds, u.appid, u.uid, openid)

        r = mp.get_user_by_openid(openid)
        if r.get('errcode'):
            logging.error("get user error:%s %s", 
                          r['errcode'], r['errmsg'])
        else:
            avatar = r.get('headimgurl', '')
            name = r.get('nickname', '')
            logging.debug("gh_id:%s openid:%s name:%s avatar:%s", gh_id, openid, name, avatar)
            WXUser.set_user_name(rds, u.appid, u.uid, name, avatar)
    elif now - u.timestamp > 24*3600:
        #更新用户信息
        wx = App.get_wx_by_ghid(db, gh_id)
        if not wx:
            logging.error("invalid gh_id:%s", gh_id)
            return None

        store_id = wx['store_id']
        if store_id and u.store_id != store_id:
            WXUser.set_store_id(rds, gh_id, openid, store_id)
            WXUser.set_seller_id(rds, gh_id, openid, 0)
            logging.debug("store changed, gh_id:%s openid:%s store id:%s -> %s", gh_id, openid, u.store_id, store_id)
            
        access_token = get_access_token(rds, db, wx['wx_app_id'])
        if not access_token:
            logging.error("can't get access token")
            return None

        mp = WXMPAPI(access_token)
        r = mp.get_user_by_openid(openid)
        if r.get('errcode'):
            logging.error("get user error:%s %s", 
                          r['errcode'], r['errmsg'])
        else:
            avatar = r.get('headimgurl', '')
            name = r.get('nickname', '')
            logging.debug("gh_id:%s openid:%s name:%s avatar:%s", gh_id, openid, name, avatar)
            WXUser.set_user_name(rds, u.appid, u.uid, name, avatar)
            WXUser.set_timestamp(rds, gh_id, openid, now)
        
    return u


