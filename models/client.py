# -*- coding: utf-8 -*-
import time
from website.core import ObjectType

class Client(object):
    CLIENT_ANDROID = 1
    CLIENT_IOS = 2
    CLIENT_WX = 3

    @classmethod
    def gen_id(cls, db):
        obj_type = ObjectType.CLIENT
        result = db.execute("INSERT INTO _object (`type`) VALUES (%s)", obj_type)
        return result.lastrowid


    @classmethod
    def create_client(cls, db, client_id, appid, developer_id, platform_type, platform_identity):
        now = int(time.time())
        sql = "INSERT INTO client(id, app_id, developer_id, platform_type, platform_identity, ctime, utime) VALUES(%s, %s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, appid, developer_id, platform_type, platform_identity, now, now))
        return r.lastrowid

    @classmethod
    def create_wx(cls, db, client_id, gh_id, wx_appid, refresh_token):
        sql = "INSERT INTO client_wx(client_id, gh_id, wx_app_id, refresh_token, store_id, is_authorized) VALUES(%s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, gh_id, wx_appid, refresh_token, store_id, 1))
        return r.lastrowid


    @classmethod
    def set_wx_unauthorized(cls, db, wx_appid):
        sql = "UPDATE client_wx SET is_authorized=%s WHERE wx_app_id=%s"
        r = db.execute(sql, (0, wx_appid))
        return r.rowcount

    @classmethod
    def set_wx_authorized(cls, db, wx_appid):
        sql = "UPDATE client_wx SET is_authorized=%s WHERE wx_app_id=%s"
        r = db.execute(sql, (1, wx_appid))
        return r.rowcount

    @classmethod
    def set_wx_store_id(cls, db, wx_appid, store_id):
        sql = "UPDATE client_wx SET store_id=%s WHERE wx_app_id=%s"
        r = db.execute(sql, (store_id, wx_appid))
        return r.rowcount
        
    @classmethod
    def update_wx(cls, db, wx_appid, refresh_token, is_authorized):
        sql = "UPDATE client_wx SET refresh_token=%s, is_authorized=%s WHERE wx_app_id=%s"
        
        is_auth = 1 if is_authorized else 0
        r = db.execute(sql, (refresh_token, is_auth, wx_appid))
        return r.rowcount

