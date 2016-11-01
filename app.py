# -*- coding: utf-8 -*-
""" 程序入口
"""
import config
import time, math
import redis

from flask import g, request, render_template
from utils.pager import Pager
from utils.response_meta import ResponseMeta
from utils.request import Request
from utils.func import init_logger
from utils.mysql import Mysql
from config import APP_MODE
from config import MYSQL

from flask import Flask, Markup, render_template, request

from utils.func import init_logger
from utils.session import RedisSession
import config

app = Flask(__name__)
app.config.from_object(config)

rds = redis.StrictRedis(host=config.REDIS_HOST,
                        port=config.REDIS_PORT,
                        db=config.REDIS_DB,
                        password=config.REDIS_PASSWORD)

LOGGER = init_logger(__name__)

init_logger(None)


def http_error_handler(err):
    LOGGER.error(err)
    return render_template('error.html', description=str(err))


def response_meta_handler(response_meta):
    return response_meta.get_response()


def generic_error_handler(err):
    LOGGER.exception(err)
    return ResponseMeta(http_code=500, description='Server Internal Error!' if APP_MODE == 'Production' else str(err))


def before_request():
    g.headers = {}
    g.pagination = Pager(request.args)
    g.request = Request(request)
    g.auth = None
    g.perms = {}

    g.im_rds = rds

    cnf = MYSQL
    g._db = Mysql(*cnf)
    g._imdb = g._db


def app_teardown(exception):
    try:
        db = getattr(g, '_db', None)
        if db:
            db.close()
    except Exception:
        pass


# 初始化接口
def init_app(app):
    app.teardown_appcontext(app_teardown)
    app.before_request(before_request)
    # for error in range(400, 420) + range(500, 506):
    #     app.error_handler_spec[None][error] = http_error_handler
    app.register_error_handler(ResponseMeta, response_meta_handler)
    app.register_error_handler(Exception, generic_error_handler)

    from utils.mail import Mail

    Mail.init_app(app)

    # 注册接口
    from api.blueprint import api
    # from website.web import web
    # from website.application import app as application
    # from website.question import question
    # from website.account import account

    from api import *

    app.register_blueprint(api)
    # app.register_blueprint(web)
    # app.register_blueprint(application)
    # app.register_blueprint(question)
    # app.register_blueprint(account)

    # app.register_blueprint(wx)


init_app(app)
RedisSession.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=61001)
