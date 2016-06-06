# -*- coding: utf-8 -*-
from flask import Blueprint, session, request, g, render_template, url_for, redirect
from website.web import web
from website.blueprint_utils import login_required
import md5
import os
import time
import logging
import xmlrpclib

import config
from models import Question

question = Blueprint('question', __name__, template_folder='templates', static_folder='static')
rpc = xmlrpclib.ServerProxy(config.RPC)

def _im_login_required(f):
    return login_required(f, redirect_url_for='wx.wx_index')


@question.route("/question", methods = ["GET"])
@_im_login_required
def question_index():
    db = g._imdb

    uid = session['user']['id']
    store_id = session['user']['store_id']

    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))

    rows_found = Question.get_question_count(db, store_id)
    questions = Question.get_page_question(db, store_id, offset, limit)

    g.pagination.setdefault()
    g.pagination.rows_found = rows_found
    g.pagination.limit = limit
    g.pagination.offset = offset

    return render_template('question/question.html',
                           data={'offset': offset,
                                 'list': questions,
                                 'pagination': g.pagination,
                                 })



@question.route("/question", methods = ["POST"])
@_im_login_required
def question_post():
    q = request.form.get('question', '')
    a = request.form.get('answer', '')
    if not q or not a:
        return "0"

    uid = session['user']['id']
    store_id = session['user']['store_id']

    qid = Question.add(g._db, q, a, store_id)

    #更新robotd的问题库
    try:
        rpc.refresh_questions()
    except xmlrpclib.ProtocolError as err:
        logging.warning("refresh questions err:%s", err)
    except Exception as err:
        logging.warning("refresh questions err:%s", err)

    return redirect(url_for('.question_index'))


@question.route("/question/add", methods = ["GET"])
@_im_login_required
def question_add():
    uid = session['user']['id']
    store_id = session['user']['store_id']

    return render_template('question/question_add.html', data={"store_id":store_id})

