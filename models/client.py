# -*- coding: utf-8 -*-
import time
from website.core import ObjectType
from website.core import PlatformType

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
    def create_client(cls, db, client_id, appid, developer_id, platform_type, platform_identity, is_active=1):
        now = int(time.time())
        sql = "INSERT INTO client(id, app_id, developer_id, platform_type, platform_identity, ctime, utime, is_active) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, appid, developer_id, platform_type, platform_identity, now, now, is_active))
        return r.lastrowid

    @classmethod
    def create_android(cls, db, client_id, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key):
        now = int(time.time())
        sql = "INSERT INTO client_certificate(client_id, update_time, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, now, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key))
        return r.lastrowid

    @classmethod
    def create_ios(cls, db, client_id, sandbox_key, sandbox_key_secret, production_key, production_key_secret):
        now = int(time.time())
        sql = "INSERT INTO client_apns(client_id, sandbox_key, sandbox_key_secret, production_key, production_key_secret, sandbox_key_utime, production_key_utime) VALUES(%s, %s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, sandbox_key, sandbox_key_secret, production_key, production_key_secret, now, now))
        return r.lastrowid

    @classmethod
    def update_ios(cls, db, client_id, sandbox_key, sandbox_key_secret, production_key, production_key_secret):
        now = int(time.time())
        sql = "UPDATE client_apns SET sandbox_key=%s, sandbox_key_secret=%s, production_key=%s, production_key_secret=%s, sandbox_key_utime=%s, production_key_utime=%s WHERE client_id=%s"
        r = db.execute(sql, (sandbox_key, sandbox_key_secret, production_key, production_key_secret, now, now, client_id))
        return r.rowcount

    @classmethod
    def update_android(cls, db, client_id, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key):
        now = int(time.time())
        sql = "UPDATE client_certificate SET xinge_access_id=%s, xinge_secret_key=%s, mi_appid=%s, mi_secret_key=%s, hw_appid=%s, hw_secret_key=%s, gcm_sender_id=%s, gcm_api_key=%s, update_time=%s WHERE client_id=%s"

        r = db.execute(sql, (xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key, now, client_id))
        return r.rowcount
                       
    @classmethod
    def create_wx(cls, db, client_id, gh_id, wx_appid, refresh_token, is_app):
        sql = "INSERT INTO client_wx(client_id, gh_id, wx_app_id, refresh_token, is_authorized, is_app) VALUES(%s, %s, %s, %s, %s, %s)"
        r = db.execute(sql, (client_id, gh_id, wx_appid, refresh_token, 1, 1 if is_app else 0))
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
    def update_wx(cls, db, wx_appid, refresh_token, is_authorized):
        sql = "UPDATE client_wx SET refresh_token=%s, is_authorized=%s WHERE wx_app_id=%s"
        
        is_auth = 1 if is_authorized else 0
        r = db.execute(sql, (refresh_token, is_auth, wx_appid))
        return r.rowcount


    @classmethod
    def get_android(cls, db, appid):
        sql = "SELECT id, app_id, platform_type FROM client WHERE app_id=%s AND platform_type=%s"
        r = db.execute(sql, (appid, cls.CLIENT_ANDROID))
        return r.fetchone()

    @classmethod
    def get_ios(cls, db, appid):
        sql = "SELECT id, app_id, platform_type FROM client WHERE app_id=%s AND platform_type=%s"
        r = db.execute(sql, (appid, cls.CLIENT_IOS))
        return r.fetchone()

