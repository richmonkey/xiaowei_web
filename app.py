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



@app.context_processor
def pjax_processor():
    def get_template(base, pjax=None):
        pjax = pjax or 'pjax.html'
        if 'X-PJAX' in request.headers:
            return pjax
        else:
            return base

    return dict(pjax=get_template)


@app.context_processor
def pagination_processor():
    def pagination(url, pager, template=None, params={}):
        template = template or 'mod/pagination.html'
        pager._dict['current'] = int(math.ceil(( pager.offset + 1 ) / float(pager.limit)))
        pager._dict['total_page'] = int(math.ceil(pager.rows_found / float(pager.limit)))
        prev_offset = pager.offset - pager.limit
        pager._dict['prev_offset'] = prev_offset if prev_offset >= 0 else 0
        pager._dict['params'] = params
        pager._dict['url'] = url
        return Markup(render_template(template, data=pager))

    return dict(pagination=pagination)


@app.template_filter('datetime')
def datetime_filter(n, format='%Y-%m-%d %H:%M'):
    arr = time.localtime(n)
    return time.strftime(format, arr)


from flask import Blueprint, redirect, url_for
from website.blueprint_utils import login_required

wx = Blueprint('wx', __name__, template_folder='templates', static_folder='static')



def _im_login_required(f):
    return login_required(f, redirect_url_for='.wx_index')

@wx.route('/wx')
@_im_login_required
def wx_index():
    return redirect(url_for('application.app_index'))


# 初始化接口
def init_app(app):
    app.teardown_appcontext(app_teardown)
    app.before_request(before_request)
    for error in range(400, 420) + range(500, 506):
        app.error_handler_spec[None][error] = http_error_handler
    app.register_error_handler(ResponseMeta, response_meta_handler)
    app.register_error_handler(Exception, generic_error_handler)

    from utils.mail import Mail

    Mail.init_app(app)

    # 注册接口
    from website.api import api
    from website.web import web
    from website.application import app as application
    from website.question import question
    from website.account import account


    app.register_blueprint(api)
    app.register_blueprint(web)
    app.register_blueprint(application)
    app.register_blueprint(question)
    app.register_blueprint(account)

    app.register_blueprint(wx)


init_app(app)
RedisSession.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=61001)
