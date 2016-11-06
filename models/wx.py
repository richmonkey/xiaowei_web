# -*- coding: utf-8 -*-
import logging
import time

class WX(object):
    #保存公众号的access_token
    @classmethod
    def set_access_token(cls, rds, wx_appid, access_token, expires):
        key = "wx_token_%s"%wx_appid
        rds.set(key, access_token)
        rds.expire(key, expires)
    
    @classmethod
    def get_access_token(cls, rds, wx_appid):
        key = "wx_token_%s"%wx_appid
        return rds.get(key)

    @classmethod
    def set_componet_access_token(cls, rds, access_token, expires):
        key = "component_access_token"
        rds.set(key, access_token)
        rds.expire(key, expires)

    @classmethod
    def get_component_access_token(cls, rds):
        key = "component_access_token"
        return rds.get(key)

    @classmethod
    def set_ticket(cls, rds, ticket):
        key = "component_ticket"
        rds.set(key, ticket)

    @classmethod
    def get_ticket(cls, rds):
        key = "component_ticket"
        return rds.get(key)

    
class WXUser(object):
    def __init__(self):
        self.gh_id = None
        self.openid = None

        #gobelieve平台的appid
        self.appid = 0
        self.uid = 0
        self.wx_appid = ""
        self.store_id = 0
        self.seller_id = 0
        self.seller_timestamp = 0
        self.timestamp = 0

    @classmethod
    def gen_id(cls, rds):
        key = "wx_users_id"
        return rds.incr(key)

    @classmethod
    def get_wx_user(cls, rds, gh_id, openid):
        key = "wx_users_%s_%s"%(gh_id, openid)
        logging.debug("wx user key:%s", key)

        appid, uid, wx_appid, store_id, seller_id, seller_timestamp, timestamp = rds.hmget(key, "appid", "uid", "wx_appid", "store_id", "seller_id", 'seller_timestamp', 'timestamp')

        if not appid or not uid or not store_id:
            return None
        u = WXUser()
        u.gh_id = gh_id
        u.openid = openid
        u.appid = int(appid)
        u.uid = int(uid)
        u.wx_appid = wx_appid
        u.store_id = int(store_id)
        u.seller_id = int(seller_id) if seller_id else 0
        u.seller_timestamp = int(seller_timestamp) if seller_timestamp else 0
        u.timestamp = int(timestamp) if timestamp else 0
        return u

    @classmethod
    def save_wx_user(cls, rds, u):
        key = "wx_users_%s_%s"%(u.gh_id, u.openid)

        obj = {
            "appid":u.appid,
            "uid":u.uid,
            "wx_appid":u.wx_appid,
            "store_id":u.store_id,
            "seller_id":u.seller_id,
            'seller_timestamp':u.seller_timestamp,
            'timestamp':u.timestamp
        }
        logging.debug("save wx user:%s, %s", key, obj)
        rds.hmset(key, obj)

    @classmethod
    def set_seller_id(cls, rds, gh_id, openid, seller_id):
        key = "wx_users_%s_%s"%(gh_id, openid)
        rds.hset(key, "seller_id", seller_id)

    @classmethod
    def set_timestamp(cls, rds, gh_id, openid, timestamp):
        key = "wx_users_%s_%s"%(gh_id, openid)
        rds.hset(key, "timestamp", timestamp)

    @classmethod
    def set_seller_timestamp(cls, rds, gh_id, openid, timestamp):
        key = "wx_users_%s_%s"%(gh_id, openid)
        rds.hset(key, "seller_timestamp", timestamp)

    @classmethod
    def bind_openid(cls, rds, appid, uid, openid):
        now = int(time.time())
        key = "users_%d_%d"%(appid, uid)

        obj = {
            "wx_openid":openid,
            "wx_timestamp":now
        }
        rds.hmset(key, obj)

    @classmethod
    def set_user_name(cls, rds, appid, uid, name, avatar=''):
        key = "users_%d_%d"%(appid, uid)

        obj = {
            "name":name,
            "avatar":avatar
        }
        rds.hmset(key, obj)
