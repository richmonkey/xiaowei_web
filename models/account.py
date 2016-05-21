# -*- coding: utf-8 -*-
"""
"""
import time
import logging
from website.core import EmailUsageType
from website.core import ObjectType
class Account():
    @classmethod
    def get_account(cls, db, account_id):
        sql = "SELECT id, name, number as email, password, email_checked, store_id FROM seller WHERE id=%s"
        r = db.execute(sql, account_id)
        return r.fetchone()

    @classmethod
    def get_account_with_email(cls, db, email):
        sql = "SELECT id, name, number as email, password, email_checked, store_id FROM seller WHERE number=%s"
        r = db.execute(sql, email)
        return r.fetchone()

    @classmethod
    def reset_password(cls, db, account_id, password):
        sql = "UPDATE seller SET password=%s WHERE id=%s"
        db.execute(sql, (password, account_id))

    @classmethod
    def set_email_checked(cls, db, account_id, checked):
        sql = "UPDATE seller SET email_checked=%s WHERE id=%s"
        db.execute(sql, (checked, account_id))

    @classmethod
    def get_verify_email(cls, db, code, usage):
        sql = "SELECT * FROM verify_email WHERE code=%s AND usage_type=%s"
        result = db.execute(sql, (code, usage))
        row = result.fetchone()
        return row

    @classmethod
    def delete_verify_email(cls, db, code, usage):
        sql = "DELETE FROM verify_email WHERE code=%s AND usage_type=%s"
        db.execute(sql, (code, usage))
        

    @classmethod
    def get_verify_count(cls, db, email):
        today_time = int(time.time())
        result = db.execute(
            "SELECT COUNT(0) AS email_count FROM verify_email "
            "WHERE email=%s AND usage_type=%s AND (ctime BETWEEN %s AND %s)",
            (email, EmailUsageType.DEVELOPER_RESET_PWD, today_time - 86400, today_time)
        )
        row = result.fetchone()
        return row['email_count']

    @classmethod
    def insert_verify_email(cls, db, email, code, usage, account_id):
        today_time = int(time.time())
        sql = "INSERT INTO verify_email(email, usage_type, code, ctime, ro_id) VALUES(%s,%s,%s,%s,%s)"
        db.execute(sql, (email, usage, code, today_time, account_id))
