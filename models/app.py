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
    def create_app(cls, db, appid, name, developer_id, key, secret):
        now = int(time.time())
        sql = "INSERT INTO app(`id`, `name`, developer_id, ctime, `key`, secret) VALUES(%s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (appid, name, developer_id, now, key, secret))
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
     
        App.create_app(db, appid, name, developer_id, app_key, app_secret)
     
        client_id = Client.gen_id(db)
     
        Client.create_client(db, client_id, appid, developer_id, 
                             Client.CLIENT_WX, "")
     
        Client.create_wx(db, client_id, gh_id, wx_appid, 
                         refresh_token, store_id)
     
        db.commit()
        return appid

