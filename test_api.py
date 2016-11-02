# -*- coding: utf-8 -*-

import requests
import urllib
import urllib2

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import threading
import json
import sys
import base64

URL = "http://127.0.0.1:61001/api"
# URL = "http://dev.kefu.gobelieve.io/api"

email = "houxuehua49@gmail.com"
password = "111111"

email2 = "houxuehua@gobelieve.io"
password2 = "111111"

url = URL + "/user/login"
r = requests.post(url, data={"email": email, "password": password})
print r.content

# url = URL + "/user/send_verify_email"
# r = requests.post(url, data={"email": email2, "password": password2})
# print r.content

# url = URL + "/user/resend_verify_email"
# r = requests.post(url, data={"email": email2})
# print r.content

# url = URL + "/user/verify"
# r = requests.post(url, data={"code": "foNodNcWsfwHYdnUWSwOb0of0If42Gnc5Qd3DZKu"})
# print r.status_code, r.content

# url = URL + "/user/send_reset_email"
# r = requests.post(url, data={"email": email})
# print r.status_code, r.content

# url = URL + "/user/reset_password"
# r = requests.post(url, data={"code": "jZAoJxNG7GZ5CfDxzdYkN2Jpi1r0kfwTq7E3MRJv", 'password': password})
# print r.status_code, r.content

# url = URL + "/user/change_password"
# r = requests.post(url, data={"old_value": password, 'new_value': password})
# print r.status_code, r.content

url = URL + "/apps"
r = requests.get(url)
print r.status_code, r.content
result = json.loads(r.content)

if result:
    app_id = 7

    url = URL + "/apps/{}".format(app_id)
    r = requests.get(url)
    print r.status_code, r.content

url = URL + "/apps"
r = requests.post(url, data={'name': '测试'})
print r.status_code, r.content

url = URL + "/questions"
r = requests.post(url, data={"question": "test", "answer": "answer"})
print r.status_code
question_id = json.loads(r.content)['id']

url = URL + "/questions"
r = requests.get(url)
print r.status_code, r.content

url = URL + "/questions/{}".format(question_id)
r = requests.delete(url)
print r.status_code, r.content

url = URL + "/sellers"
r = requests.get(url)
print r.status_code, r.content

url = URL + "/sellers"
r = requests.post(url, data={"name": "test", "password": "test"})
print r.status_code, r.content
seller_id = json.loads(r.content)['id']

url = URL + "/sellers/{}".format(seller_id)
r = requests.delete(url)
print r.status_code, r.content

url = URL + "/wx"
r = requests.get(url)
print r.status_code, r.content

url = URL + "/wx/{}".format(1500)
r = requests.get(url)
print r.status_code, r.content

#
# # 创建store
# url = URL + "/stores"
# r = requests.post(url, data={"name": "test"}, headers=headers)
# print r.content
# obj = json.loads(r.content)
# store_id = obj['store_id']
#
# # 获取store列表
# url = URL + "/stores"
# r = requests.get(url, headers=headers)
# print r.content
#
# FIX_MODE = 1
# ONLINE_MODE = 2
# BROADCAST_MODE = 3
#
# # 设置客服模式
# url = URL + "/stores/%s" % store_id
# r = requests.patch(url, data={"mode": BROADCAST_MODE}, headers=headers)
# print "set mode:", r.status_code
#
# # 创建seller
# url = URL + "/stores/%s/sellers" % store_id
# r = requests.post(url, data={"name": "test", "password": "111111"}, headers=headers)
# print r.content
# obj = json.loads(r.content)
# seller_id = obj['seller_id']
#
# # 修改销售名称和密码
# url = URL + "/stores/%s/sellers/%s" % (store_id, seller_id)
# r = requests.patch(url, data={"name": "test_name", "password": "123456"}, headers=headers)
# print "set name/password:", r.status_code
#
# # 获取销售员列表
# url = URL + "/stores/%s/sellers" % store_id
# r = requests.get(url, headers=headers)
# print r.content
#
# # 删除销售人员
# url = URL + "/stores/%s/sellers/%s" % (store_id, seller_id)
# r = requests.delete(url, headers=headers)
# print r.status_code
#
# # 删除store
# url = URL + "/stores/%s" % store_id
# r = requests.delete(url, headers=headers)
# print r.status_code
