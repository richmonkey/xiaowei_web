# -*- coding: utf-8 -*-
import time
from website.core import ObjectType

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

