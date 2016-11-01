# -*- coding: utf-8 -*-
from flask import session, request, g
from werkzeug.security import generate_password_hash
from .blueprint_utils import login_required

from models import Seller

from blueprint import api
from .blueprint_utils import make_response
from exception import MainException


@api.route('/sellers')
@login_required
def store_seller():
    """
    store 销售人员

    """
    db = g._imdb
    store_id = session['user']['store_id']

    sellers = Seller.get_sellers(db, store_id)

    return make_response(200, sellers)


@api.route('/sellers', methods=["POST"])
@login_required
def store_seller_post():
    """
    store 添加商店人员

    """
    db = g._imdb
    store_id = session['user']['store_id']

    form = request.form
    name = form.get('name', '')
    password = form.get('password', '')
    number = form.get('number', '')
    if not name or not password or not store_id:
        return MainException.SELLER_INVALID

    if not number:
        number = None
    password = generate_password_hash(password)

    seller_id = Seller.add_seller(db, name, password, store_id, number, 0)

    return make_response(200, {"id": seller_id})


@api.route('/sellers/<int:seller_id>', methods=["DELETE"])
@login_required
def store_seller_delete(seller_id):
    store_id = session['user']['store_id']
    db = g._imdb

    Seller.delete_seller(db, store_id, seller_id)
    return make_response(200)
