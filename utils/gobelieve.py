# -*- coding: utf-8 -*-
import requests
import base64
import md5
import json
import logging
import config

def login_gobelieve(uid, uname, appid, appsecret, device_id = '', platform = ''):
    url = config.GOBELIEVE_URL + "/auth/grant"
    obj = {"uid":uid, "user_name":uname}
    if device_id and platform:
        obj["device_id"] = device_id
        obj["platform_id"] = platform

    m = md5.new(appsecret)
    secret = m.hexdigest()
    basic = base64.b64encode(str(appid) + ":" + secret)

    headers = {'Content-Type': 'application/json; charset=UTF-8',
               'Authorization': 'Basic ' + basic}
     
    res = requests.post(url, data=json.dumps(obj), headers=headers)
    if res.status_code != 200:
        logging.warning("login error:%s %s", res.status_code, res.text)
        return None

    obj = json.loads(res.text)
    return obj["data"]["token"]


def send_sys_message(uid, msg, appid, appsecret):
    url = config.GOBELIEVE_URL + "/messages/systems"
    obj = {"receiver":uid, "content":msg}

    m = md5.new(appsecret)
    secret = m.hexdigest()
    basic = base64.b64encode(str(appid) + ":" + secret)

    headers = {'Content-Type': 'application/json; charset=UTF-8',
               'Authorization': 'Basic ' + basic}
     
    res = requests.post(url, data=json.dumps(obj), headers=headers)
    if res.status_code != 200:
        logging.warning("login error:%s %s", res.status_code, res.text)
    else:
        logging.debug("send system message success")



