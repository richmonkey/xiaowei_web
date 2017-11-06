# -*- coding: utf-8 -*-
import requests
from flask import request, Blueprint, g, session, redirect
from flask import render_template_string, render_template
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
import flask
import md5
import json
import base64
import logging

from models.store import Store
from models.app import App

from utils.gobelieve import login_gobelieve
import config

app = Blueprint('customer', __name__)

error_html = """<!DOCTYPE html>
<html>
<head>
<title>客服</title>
</head>
<body>


<p>{{error}}</p>

</body>
</html>"""


@app.route("/chat/pc/index.html")
def chat():
    store = request.args.get('store')
    uid = request.args.get('uid')
    appid = request.args.get('appid')
    token = request.args.get('token')
    username = request.args.get('name', '')
    device_id = request.args.get('device_id', '')
    if not store and appid:
        store = App.get_store_id(g._db, int(appid))
        logging.debug("store id:%s", store)
        if not store:
            return render_template_string(error_html, error="非法的应用id")

    if not store:
        return render_template_string(error_html, error="未指定商店id")

    s = Store.get_store(g._db, int(store))
    if s:
        name = s['name']
    else:
        name = ""

    if uid and appid and token:
        return render_template("customer/pc_chat.html",
                               host=config.HOST,
                               customerAppID=int(appid),
                               customerID=int(uid),
                               customerToken=token,
                               name=name,
                               apiURL=config.IM_URL,
                               storeID=int(store))


    #check cookie
    co_username = request.cookies.get('username', '')
    co_uid = request.cookies.get('uid')
    co_token = request.cookies.get('token')

    if co_username == username and co_uid and co_token:
        appid = config.ANONYMOUS_APP_ID
        uid = int(co_uid)
        token = co_token
        return render_template("customer/pc_chat.html",
                               host=config.HOST,
                               customerAppID=appid,
                               customerID=uid,
                               customerToken=token,
                               name=name,
                               apiURL=config.IM_URL,
                               storeID=int(store))

    # 生成临时用户
    rds = g.im_rds
    key = "anonymous_id"
    uid = rds.incr(key)
    appid = config.ANONYMOUS_APP_ID
    token = login_gobelieve(uid, username,
                            config.ANONYMOUS_APP_ID,
                            config.ANONYMOUS_APP_SECRET,
                            device_id=device_id)
    resp = flask.make_response(render_template("customer/pc_chat.html",
                                               host=config.HOST,
                                               customerAppID=appid,
                                               customerID=uid,
                                               customerToken=token,
                                               name=name,
                                               apiURL=config.IM_URL,
                                               storeID=int(store)))

    resp.set_cookie('token', token)
    resp.set_cookie('uid', str(uid))
    resp.set_cookie('username', username)
    return resp
