# -*- coding: utf-8 -*-
import time
from website.core import ObjectType
from client import Client
from utils.func import random_ascii_string

class WXApp(object):
    def __init__(self):
        self.gh_id = ""
        self.appid = 0
        self.name = ""
        self.developer_id = 0

class App(object):
    @classmethod
    def gen_id(cls, db):
        obj_type = ObjectType.APP
        result = db.execute("INSERT INTO _object (`type`) VALUES (%s)", obj_type)
        return result.lastrowid

    @classmethod
    def create_app(cls, db, appid, name, developer_id, key, secret, store_id=0):
        now = int(time.time())
        sql = "INSERT INTO app(`id`, `name`, developer_id, ctime, `key`, secret, store_id) VALUES(%s, %s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (appid, name, developer_id, now, key, secret, store_id))
        return r.lastrowid

    @classmethod
    def delete_by_developer(cls, db, appid, developer_id):
        sql = "SELECT id FROM client WHERE app_id=%s AND developer_id=%s"
        rs = db.execute(sql, (appid, developer_id))
        client_ids = [str(row['id']) for row in rs.fetchall()]
        if client_ids:
            db.execute("DELETE FROM client WHERE id IN ({})".format(','.join(client_ids)))

        db.execute("DELETE FROM app WHERE id=%s AND developer_id=%s", 
                   (appid, developer_id))


    @classmethod
    def get_wx(cls, db, gh_id):
        sql = "SELECT app.id as id, app.name as name, app.developer_id as developer_id FROM client_wx, client, app WHERE gh_id=%s and client_wx.client_id=client.id and client.app_id=app.id"
        r = db.execute(sql, gh_id)
        obj = r.fetchone()
        wx = WXApp()
        wx.gh_id = gh_id
        wx.appid = obj['id']
        wx.name = obj['name']
        wx.developer_id = obj['developer_id']
        return wx
     
    @classmethod
    def create_wx(cls, db, name, gh_id, wx_appid, refresh_token, store_id):
        db.begin()
        appid = App.gen_id(db)
        app_key = random_ascii_string(32)
        app_secret = random_ascii_string(32)
        developer_id = 0
     
        App.create_app(db, appid, name, developer_id, app_key, app_secret, store_id)
     
        client_id = Client.gen_id(db)
     
        Client.create_client(db, client_id, appid, developer_id, 
                             Client.CLIENT_WX, "")
     
        Client.create_wx(db, client_id, gh_id, wx_appid, 
                         refresh_token)
     
        db.commit()
        return appid

    @classmethod
    def get_wx_app(cls, db, appid):
        sql = "SELECT app.id as id, app.name as name FROM app, client, client_wx WHERE app.id=%s AND client.app_id=app.id AND client.id=client_wx.client_id"
        r = db.execute(sql, appid)
        return r.fetchone()

    @classmethod
    def get_wx(cls, db, wx_appid):
        sql = "SELECT app.id as appid, app.name as name, app.developer_id as developer_id, app.store_id as store_id, client_wx.client_id as client_id, client_wx.gh_id as gh_id, client_wx.wx_app_id as wx_app_id, client_wx.refresh_token as refresh_token, client_wx.is_authorized as is_authorized FROM app, client, client_wx WHERE client_wx.wx_app_id=%s AND client_wx.client_id=client.id AND client.app_id=app.id"
        r = db.execute(sql, wx_appid)
        return r.fetchone()

    @classmethod
    def get_wx_by_ghid(cls, db, gh_id):
        sql = "SELECT app.id as appid, app.name as name, app.developer_id as developer_id, app.store_id as store_id, client_wx.client_id as client_id, client_wx.gh_id as gh_id, client_wx.wx_app_id as wx_app_id, client_wx.refresh_token as refresh_token, client_wx.is_authorized as is_authorized FROM app, client, client_wx WHERE gh_id=%s and client_wx.client_id=client.id and client.app_id=app.id"
        r = db.execute(sql, gh_id)
        obj = r.fetchone()
        return obj

    @classmethod
    def get_wx_count(cls, db, store_id):
        sql = "SELECT count(client.id) as count FROM client_wx, client, app WHERE client_wx.client_id=client.id AND app.id=client.app_id AND app.store_id=%s"
        r = db.execute(sql, store_id)
        obj = r.fetchone()
        return obj['count']


    @classmethod
    def get_wx_page(cls, db, store_id, offset, limit):
        sql = "SELECT app.id as id, app.name as name, app.store_id as store_id, client_wx.gh_id as gh_id, client_wx.wx_app_id as wx_app_id, client_wx.is_authorized as is_authorized FROM client_wx, client, app WHERE client_wx.client_id=client.id AND app.store_id=%s AND client.app_id=app.id LIMIT %s, %s"
        r = db.execute(sql, (store_id, offset, limit))
        return list(r.fetchall())


    @classmethod
    def set_store_id(cls, db, appid, store_id):
        sql = "UPDATE app SET store_id=%s WHERE id=%s"
        r = db.execute(sql, (store_id, appid))
        return r.rowcount
