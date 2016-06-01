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
    def create_wx(cls, db, client_id, gh_id, wx_appid, refresh_token, store_id):
        sql = "INSERT INTO client_wx(client_id, gh_id, wx_app_id, refresh_token, store_id, is_authorized) VALUES(%s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, gh_id, wx_appid, refresh_token, store_id, 1))
        return r.lastrowid

    @classmethod
    def get_app(cls, db, gh_id):
        sql = "SELECT app.id as id, app.name as name, app.developer_id as developer_id FROM client_wx, client, app WHERE gh_id=%s and client_wx.client_id=client.id and client.app_id=app.id"
        r = db.execute(sql, gh_id)
        obj = r.fetchone()
        return obj

    @classmethod
    def get_wx_app(cls, db, appid):
        sql = "SELECT app.id as id,  app.name as name FROM app, client, client_wx WHERE app.id=%s AND client.app_id=app.id AND client.id=client_wx.client_id"
        r = db.execute(sql, appid)
        return r.fetchone()

    @classmethod
    def get_wx(cls, db, wx_appid):
        sql = "SELECT client_id, gh_id, wx_app_id, refresh_token, store_id, is_authorized FROM client_wx WHERE wx_app_id=%s"
        r = db.execute(sql, wx_appid)
        return r.fetchone()

    @classmethod
    def get_wx_by_ghid(cls, db, gh_id):
        sql = "SELECT app.id as appid, app.name as name, app.developer_id as developer_id, client_wx.client_id as client_id, client_wx.gh_id as gh_id, client_wx.wx_app_id as wx_app_id, client_wx.refresh_token as refresh_token, client_wx.store_id as store_id, client_wx.is_authorized as is_authorized FROM client_wx, client, app WHERE gh_id=%s and client_wx.client_id=client.id and client.app_id=app.id"
        r = db.execute(sql, gh_id)
        obj = r.fetchone()
        return obj

    @classmethod
    def get_wx_count(cls, db, store_id):
        sql = "SELECT count(client.id) as count FROM client_wx, client WHERE client_wx.client_id=client.id AND client_wx.store_id=%s"
        r = db.execute(sql, store_id)
        obj = r.fetchone()
        return obj['count']


    @classmethod
    def get_wx_page(cls, db, store_id, offset, limit):
        sql = "SELECT app.id as id, app.name as name, client_wx.gh_id as gh_id, client_wx.wx_app_id as wx_app_id, client_wx.store_id as store_id, client_wx.is_authorized as is_authorized FROM client_wx, client, app WHERE client_wx.client_id=client.id AND client_wx.store_id=%s AND client.app_id=app.id LIMIT %s, %s"
        r = db.execute(sql, (store_id, offset, limit))
        return list(r.fetchall())

    @classmethod
    def get_store_id(cls, db, gh_id):
        sql = "SELECT store_id FROM client_wx WHERE client_wx.gh_id=%s"
        r = db.execute(sql, gh_id)
        obj = r.fetchone()
        if not obj:
            return 0
        return obj['store_id']


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

