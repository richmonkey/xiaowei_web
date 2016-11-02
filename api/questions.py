# -*- coding: utf-8 -*-
from flask import session, request, g
from .blueprint_utils import login_required
import logging
import xmlrpclib

import config
from models import Question

from blueprint import api
from .blueprint_utils import make_response
from exception import MainException

rpc = xmlrpclib.ServerProxy(config.RPC)


@api.route("/questions", methods=["GET"])
@login_required
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

    return make_response(
        200,
        data={
            'pagination': {
                'offset': offset,
                'limit': limit,
                'rows_found': rows_found,
            },
            'data': questions,
        }
    )


@api.route("/questions", methods=["POST"])
@login_required
def question_post():
    q = request.form.get('question', '')
    a = request.form.get('answer', '')
    if not q or not a:
        raise MainException.QUESTION_INVALID

    uid = session['user']['id']
    store_id = session['user']['store_id']

    qid = Question.add(g._db, q, a, store_id)

    # 更新robotd的问题库
    try:
        rpc.refresh_questions()
    except xmlrpclib.ProtocolError as err:
        logging.warning("refresh questions err:%s", err)
    except Exception as err:
        logging.warning("refresh questions err:%s", err)

    return make_response(200, data={'id': qid})


@api.route("/questions/<int:question_id>", methods=["DELETE"])
@login_required
def question_delete(question_id):
    Question.delete(g._db, question_id)
    # 更新robotd的问题库
    try:
        rpc.refresh_questions()
    except xmlrpclib.ProtocolError as err:
        logging.warning("refresh questions err:%s", err)
    except Exception as err:
        logging.warning("refresh questions err:%s", err)

    return MainException.OK
