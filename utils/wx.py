# -*- coding: utf-8 -*-
import requests
import time
import json
import socket
try:
    import socks
except Exception:
    pass


APIROOT = 'https://api.weixin.qq.com'
URL = APIROOT + '/cgi-bin/component'

#接口文档
#https://open.weixin.qq.com/cgi-bin/showdocument?action=dir_list&t=resource/res_list&verify=1&id=open1453779503&token=&lang=zh_CN

#开放平台api
class WXOpenAPI(object):
    def __init__(self, app_id='', secret='', token=''):
        """
        连接微信，获取token
        """
        self.app_id = app_id
        self.secret = secret
        self.token = token

    #获取第三方平台component_access_token
    def request_token(self, ticket):
        try:
            url = URL + "/api_component_token"
            print url
            obj = {
                "component_appid":self.app_id,
                "component_appsecret":self.secret,
                "component_verify_ticket":ticket
            }
            
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            r = requests.post(url, headers=headers, data=json.dumps(obj))
            result = r.json()
            return result
        except Exception as e:
            print e
            return None

    #获取预授权码pre_auth_code
    def request_pre_auth_code(self):
        try:
            url = URL + "/api_create_preauthcode"
            obj = {
                "component_appid":self.app_id,
            }

            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            params = {"component_access_token":self.token}
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            result = r.json()
            return result
        except Exception as e:
            return None

    #使用授权码换取公众号的接口调用凭据和授权信息
    def request_auth(self, authorization_code):
        try:
            url = URL + "/api_query_auth"
            obj = {
                "component_appid":self.app_id,
                "authorization_code":authorization_code
            }

            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            params = {"component_access_token":self.token}
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            
            result = r.json()
            return result
        except Exception as e:
            return None

    #获取（刷新）授权公众号的接口调用凭据（令牌）
    def refresh_auth(self, auth_appid, refresh_token):
        try:
            url = URL + "/api_authorizer_token"
            obj = {
                "component_appid":self.app_id,
                "authorizer_appid":auth_appid,
                "authorizer_refresh_token":refresh_token
            }

            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            params = {"component_access_token":self.token}
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            
            result = r.json()
            return result
        except Exception as e:
            return None

    #获取授权方的公众号帐号基本信息
    #appid 公众号appid
    def request_info(self, appid):
        try:
            url = URL + "/api_get_authorizer_info"
            obj = {
                "component_appid":self.app_id,
                "authorizer_appid":appid
            }
            params = {"component_access_token":self.token}
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'
            
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            result = r.json()
            return result
        except Exception as e:
            return None


class WXOpenAPI2(WXOpenAPI):

    #获取第三方平台component_access_token
    def request_token(self, ticket):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXOpenAPI2, self).request_token(ticket)
        socket.socket = default_socket
        return r

    #获取预授权码pre_auth_code
    def request_pre_auth_code(self):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXOpenAPI2, self).request_pre_auth_code()
        socket.socket = default_socket
        return r

        
    #使用授权码换取公众号的接口调用凭据和授权信息
    def request_auth(self, authorization_code):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXOpenAPI2, self).request_auth(authorization_code)
        socket.socket = default_socket
        return r

    #获取（刷新）授权公众号的接口调用凭据（令牌）
    def refresh_auth(self, auth_appid, refresh_token):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXOpenAPI2, self).refresh_auth(auth_appid, refresh_token)
        socket.socket = default_socket
        return r

    #获取授权方的公众号帐号基本信息
    #appid 公众号appid
    def request_info(self, appid):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXOpenAPI2, self).request_info(appid)
        socket.socket = default_socket
        return r



MP_URL = APIROOT + '/cgi-bin'

#公众平台api
class WXMPAPI(object):
    def __init__(self, token=''):
        """
        连接微信，获取token
        """
        self.token = token

    def request(self, url='', method='get', params=None, data=None, files=None, flag=False, baseurl=MP_URL, headers=None, stream=False):
        """
        请求API接口，带access_token
        """
        if headers is None and not files:
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

        _params = params
        if not _params:
            _params = {}
        _params['access_token'] = self.token

        _data = data
        if _data:
            _data = json.dumps(_data, ensure_ascii=False).encode('utf-8')

        r = getattr(requests, method)(baseurl + url, headers=headers, params=_params, data=_data, files=files, stream=stream)
        result = r.json()
        return result

    def request_media(self, url='', method='get', params=None, data=None, files=None, flag=False, baseurl=MP_URL, headers=None, stream=False):
        """
        请求API接口，带access_token
        """
        if headers is None and not files:
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

        _params = params
        if not _params:
            _params = {}
        _params['access_token'] = self.token

        _data = data
        if _data:
            _data = json.dumps(_data, ensure_ascii=False).encode('utf-8')

        r = getattr(requests, method)(baseurl + url, headers=headers, params=_params, data=_data, files=files, stream=stream)
        return r.content
    
    @staticmethod
    def get_qrcode(ticket):
        """
        获取二维码图片的url
        """
        return 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=' + ticket

    def get_user_by_openid(self, openid):
        """
        获取用户信息
        """
        result = self.request(url='/user/info', params={
            'openid': openid,
            'lang': 'zh_CN'
        })
        return result

    def get_material_count(self):
        """
        获取素材库总数
        """
        result = self.request(url='/material/get_materialcount')
        return result

    def create_menu(self, menu):
        """
        创建菜单
        """
        result = self.request(url='/menu/create', method='post', data=menu)
        return result

    def delete_menu(self):
        """
        删除菜单
        """
        result = self.request(url='/menu/delete')
        return result

    def get_users(self, next_openid=''):
        """
        获取微信的关注用户
        """
        params = {}
        if next_openid:
            params['next_openid'] = next_openid
        result = self.request(url='/user/get', params=params)
        return result


    def send_text_message(self, openid, text):
        data = {
            'touser': openid,
            'msgtype': 'text',
            'text': {
                'content': text
            }
        }
        return self.send_message(data)

    def send_common_message(self, openid, msgtype, content):
        data = {
            'touser': openid,
            'msgtype': msgtype,
            msgtype: content
        }
        return self.send_message(data)

    def send_message(self, data):
        result = self.request('/message/custom/send', method='post', data=data)
        return result

    def send_template_message(self, openid, obj):
        url = obj.get('url')
        template_id = obj.get('template_id')
        data = {
            'touser': openid,
            'template_id': template_id,
            'data': obj.get('data')
        }
        if url:
            data['url'] = url

        result = self.request('/message/template/send', method='post', data=data)
        return result

    def add_media(self, media_type, media):
        result = self.request('/media/upload', method='post', params={
            'type': media_type
        }, files=media)
        return result

    def get_media(self, media_id):
        result = self.request_media(url='/media/get', headers={}, params={
            'media_id': media_id
        })
        return result

    def add_group(self, name):
        result = self.request(url='/groups/create', method='post', data={
            'group': {'name': name}
        })
        return result

    def get_groups(self):
        result = self.request(url='/groups/get')
        return result

    def set_group(self, group_id, openids):
        if isinstance(openids, list):
            result = self.request(url='/groups/members/batchupdate', method='post', data={
                'openid_list': openids,
                'to_groupid': group_id
            })
        else:
            result = self.request(url='/groups/members/update', method='post', data={
                'openid': openids,
                'to_groupid': group_id
            })
        return result


class WXMPAPI2(WXMPAPI):
    def send_message(self, data):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXMPAPI2, self).send_message(data)
        socket.socket = default_socket
        return r

    def get_user_by_openid(self, openid):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXMPAPI2, self).get_user_by_openid(openid)
        socket.socket = default_socket
        return r

    def get_media(self, media_id):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7778)
        socket.socket = socks.socksocket
        r = super(WXMPAPI2, self).get_media(media_id)
        socket.socket = default_socket
        return r

