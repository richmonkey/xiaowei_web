# -*- coding: utf-8 -*-
from flask import session, g

from .blueprint_utils import login_required

from models import App

from blueprint import api
from .blueprint_utils import make_response
from exception import MainException


@api.route('/wx')
@login_required
def wx_index():
    """
    store 模块首页

    """
    uid = session['user']['id']
    store_id = session['user']['store_id']

    db = g._imdb
    wxs = App.get_wxs(db, store_id)

    return make_response(200, wxs)


@api.route('/wx/<int:appid>', methods=['DELETE'])
@login_required
def wx_delete(appid):
    """

    """
    App.delete_app(g._db, appid)
    return MainException.OK


@api.route('/wx/<int:appid>')
@login_required
def wx_detail(appid):
    """
    store 详情

    """
    db = g._db
    app = App.get_wx_app(db, appid)

    return make_response(200, app)
