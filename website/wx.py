# -*- coding: utf-8 -*-
from flask import Blueprint, session, request, g, render_template, url_for, abort, Response, redirect
import flask

from website.web import web
from website.blueprint_utils import login_required

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

wx = Blueprint('wx', __name__, template_folder='templates', static_folder='static')


def make_response(status_code, data=None):
    if data:
        res = flask.make_response(json.dumps(data), status_code)
        res.headers['Content-Type'] = "application/json"
    else:
        res = flask.make_response("", status_code)

    return res


def INVALID_PARAM():
    e = {"error": "非法输入"}
    logging.warn("非法输入")
    return make_response(400, e)


def _im_login_required(f):
    return login_required(f, redirect_url_for='.wx_index')


@wx.before_request
def before_request():
    g.uri_path = request.path


@wx.route('/wx')
@_im_login_required
def wx_index():
    """
    store 模块首页

    """
    uid = session['user']['id']
    store_id = session['user']['store_id']

    db = g._imdb
    wxs = App.get_wxs(db, store_id)

    return render_template('wx/index.html', data={'list': wxs})


@wx.route('/wx/add')
@_im_login_required
def wx_add():
    """

    """
    return redirect(url_for("message.auth"))


@wx.route('/wx', methods=['DELETE'])
@_im_login_required
def wx_delete():
    """

    """
    _id = request.form.get('id')
    App.delete_app(_id)
    return ''


@wx.route('/wx/detail/<int:appid>')
@_im_login_required
def wx_detail(appid):
    """
    store 详情

    """
    db = g._db
    app = App.get_wx_app(db, appid)

    return render_template('wx/detail.html', data={'info': app})
