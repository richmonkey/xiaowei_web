# -*- coding: utf-8 -*-
from flask import Blueprint, session, request, g, render_template, url_for, abort, Response, redirect
import flask

from website.web import web
from website.blueprint_utils import login_required
from website.core import PlatformType

from utils.func import random_ascii_string

from models import Store
from models import Group
from models import Seller
from models import Question
from models import App
from models import Client
import md5
import os
import time
import json
import logging
import xmlrpclib
import config

app = Blueprint('application', __name__, template_folder='templates', static_folder='static')

def make_response(status_code, data = None):
    if data:
        res = flask.make_response(json.dumps(data), status_code)
        res.headers['Content-Type'] = "application/json"
    else:
        res = flask.make_response("", status_code)

    return res



def INVALID_PARAM():
    e = {"error":"非法输入"}
    logging.warn("非法输入")
    return make_response(400, e)

def _im_login_required(f):
    return login_required(f, redirect_url_for='.app_index')


@app.before_request
def before_request():
    g.uri_path = request.path


@app.route('/app')
@_im_login_required
def app_index():
    """
    store 模块首页

    """
    uid = session['user']['id']
    store_id = session['user']['store_id']

    db = g._imdb
    apps = App.get_apps(db, store_id)

    return render_template('app/index.html', data={'list':apps})


@app.route('/app/add')
@_im_login_required
def app_add():
    """

    """
    data = {}
    data['method'] = 'add'
    data["game"] = {}
    data["game"]["name"] = ""
    data["game"]["id"] = ""
    data["game"]["major_category"] = {}
    data["game"]["minor_category"] = {}
    data["game"]["clients"] = [{'platform_type': PlatformType.ANDROID, 'is_active': 0},
                               {'platform_type': PlatformType.IOS, 'is_active': 0}]
    
    return render_template('app/add.html', data=data)


@app.route('/app/detail/<int:appid>')
@_im_login_required
def app_detail(appid):
    """
    store 详情

    """
    db = g._db
    app = App.get_app(db, appid)

    return render_template('app/detail.html', app=app)


@web.route('/app/<int:appid>')
@_im_login_required
def app_edit(appid):
    """
    创建游戏
    """
    app = App.get_app(g._db, appid)
    return render_template('app/edit.html', data={'game': app, 'method': 'edit'})


@app.route('/app/<int:appid>', methods=['POST'])
@_im_login_required
def app_edit_post(appid):
    """
    修改应用
    """
    db = g._db
    android, ios = _get_clients()

    developer_id = 0
    if android:
        push_types = request.form.getlist('push_type')
        xinge_access_id = request.form.get('xinge_access_id', '')
        xinge_secret_key = request.form.get('xinge_secret_key', '')
        mi_appid = request.form.get('mi_appid', '')
        mi_secret_key = request.form.get('mi_secret_key', '')
        hw_appid = request.form.get('hw_appid', '')
        hw_secret_key = request.form.get('hw_secret_key', '')
        gcm_sender_id = request.form.get('gcm_sender_id', '')
        gcm_api_key = request.form.get('gcm_api_key', '')
        
        c = Client.get_android(db, appid)
        if not c:
            client_id = Client.gen_id(db)
            Client.create_client(db, client_id, appid, developer_id, PlatformType.ANDROID, android['platform_identity'])
            Client.create_android(db, client_id, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key)
        else:
            Client.update_android(db, c['id'], xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key)
 
    if ios:
        sandbox_key_file = request.files.get('sandbox_key')
        if sandbox_key_file:
            filename = sandbox_key_file.filename
            ext = os.path.splitext(filename)[1]
            if ext == '.p12':
                sandbox_key = sandbox_key_file.read()
                sandbox_key_secret = request.form.get('sandbox_key_secret')
            else:
                sandbox_key = ""
                sandbox_key_secret = ""
        else:
            sandbox_key = ""
            sandbox_key_secret = ""

        production_key_file = request.files.get('production_key')
        if production_key_file:
            filename = production_key_file.filename
            ext = os.path.splitext(filename)[1]
            if ext == '.p12':
                production_key = production_key_file.read()
                production_key_secret = request.form.get('production_key_secret')
            else:
                production_key = ""
                production_key_secret = ""

        else:
            production_key = ""
            production_key_secret = ""

        c = Client.get_ios(db, appid)
        if not c:
            client_id = Client.gen_id(db)
            Client.create_client(db, client_id, appid, developer_id, PlatformType.IOS, ios['platform_identity'])
            Client.create_ios(db, client_id, sandbox_key, sandbox_key_secret, production_key, production_key_secret)
        else:
            Client.update_ios(db, c['id'], sandbox_key, sandbox_key_secret, production_key, production_key_secret)


    return redirect(url_for('.app_detail', appid=appid))


@app.route('/app/complete/<int:app_id>')
@_im_login_required
def app_complete(app_id):
    """
    游戏创建完成
    """
    db = g._db

    app = App.get_app(db, app_id)
    
    return render_template('app/complete.html', app=app)




@app.route('/app', methods=['POST'])
@_im_login_required
def app_add_post():
    """
    创建应用
    """
    db = g._db

    store_id = session['user']['store_id']

    name = request.form.get('name')

    key = random_ascii_string(32)
    secret = random_ascii_string(32)

    android, ios = _get_clients()

    developer_id = 0

    db.begin()
    appid = App.gen_id(db)
    App.create_app(db, appid, name, developer_id, key, secret, store_id)

    if android:
        push_types = request.form.getlist('push_type')
        xinge_access_id = request.form.get('xinge_access_id', '')
        xinge_secret_key = request.form.get('xinge_secret_key', '')
        mi_appid = request.form.get('mi_appid', '')
        mi_secret_key = request.form.get('mi_secret_key', '')
        hw_appid = request.form.get('hw_appid', '')
        hw_secret_key = request.form.get('hw_secret_key', '')
        gcm_sender_id = request.form.get('gcm_sender_id', '')
        gcm_api_key = request.form.get('gcm_api_key', '')

        client_id = Client.gen_id(db)
        Client.create_client(db, client_id, appid, developer_id, PlatformType.ANDROID, android['platform_identity'])
        Client.create_android(db, client_id, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid, hw_secret_key, gcm_sender_id, gcm_api_key)


    if ios:
        sandbox_key_file = request.files.get('sandbox_key')
        if sandbox_key_file:
            filename = sandbox_key_file.filename
            ext = os.path.splitext(filename)[1]
            if ext == '.p12':
                sandbox_key = sandbox_key_file.read()
                sandbox_key_secret = request.form.get('sandbox_key_secret')
            else:
                sandbox_key = ""
                sandbox_key_secret = ""
        else:
            sandbox_key = ""
            sandbox_key_secret = ""

        production_key_file = request.files.get('production_key')
        if production_key_file:
            filename = production_key_file.filename
            ext = os.path.splitext(filename)[1]
            if ext == '.p12':
                production_key = production_key_file.read()
                production_key_secret = request.form.get('production_key_secret')
            else:
                production_key = ""
                production_key_secret = ""

        else:
            production_key = ""
            production_key_secret = ""

        client_id = Client.gen_id(db)
        Client.create_client(db, client_id, appid, developer_id, PlatformType.IOS, ios['platform_identity'])
        Client.create_ios(db, client_id, sandbox_key, sandbox_key_secret, production_key, production_key_secret)

        
    db.commit()

    return redirect(url_for('.app_complete', app_id=appid))


def _get_clients():
    android = None
    if request.form.get('android_identity'):
        android = {
            'platform_type': PlatformType.ANDROID,
            'platform_identity': request.form.get('android_identity'),
            'is_active': 1,
        }

    ios = None
    if request.form.get('ios_identity'):
        ios = {
            'platform_type': PlatformType.IOS,
            'platform_identity': request.form.get('ios_identity'),
            'is_active': 1,
        }
    return android, ios

