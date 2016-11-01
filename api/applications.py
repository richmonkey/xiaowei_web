# -*- coding: utf-8 -*-
from flask import session, request, g

from blueprint_utils import login_required, make_response
from models.core import PlatformType

from utils.func import random_ascii_string

from models import App
from models import Client
import os

from blueprint import api


@api.route('/apps')
@login_required
def app_index():
    """
    store 模块首页

    """
    uid = session['user']['id']
    store_id = session['user']['store_id']

    db = g._imdb
    apps = App.get_apps(db, store_id)

    data = []
    for app in apps:
        wx_client = App.get_client_wx_by_app_id(g._imdb, app['id'])
        if not wx_client:
            data.append(app)

    return make_response(200, data=data)


@api.route('/apps/<int:appid>')
@login_required
def app_detail(appid):
    """
    store 详情

    """
    db = g._db
    app = App.get_app(db, appid)

    return make_response(200, app)


@api.route('/apps/<int:appid>', methods=['PUT'])
@login_required
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
            Client.create_android(db, client_id, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid,
                                  hw_secret_key, gcm_sender_id, gcm_api_key)
        else:
            Client.update_android(db, c['id'], xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid,
                                  hw_secret_key, gcm_sender_id, gcm_api_key)

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

    return make_response(200)


@api.route('/apps', methods=['POST'])
@login_required
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
        Client.create_android(db, client_id, xinge_access_id, xinge_secret_key, mi_appid, mi_secret_key, hw_appid,
                              hw_secret_key, gcm_sender_id, gcm_api_key)

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

    return make_response(200, data={'id': appid})


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
