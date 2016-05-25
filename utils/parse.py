# -*- coding: utf-8 -*-
from xml.dom import minidom

class Parse:
    @staticmethod
    def parse(xml):
        doc = minidom.parseString(xml)
        root = doc.documentElement
        result = {}
        for node in root.childNodes:
            if node.nodeType == 1:
                tagName = node.nodeName
                textNode = node.firstChild
                if textNode:
                    value = textNode.nodeValue
                else:
                    value = ''
                result[tagName] = value
        return result

    @staticmethod
    def getMsgType(obj):
        """
        获取消息类型，根据<MsgType>节点
        1. 普通消息
            文本消息: text
            图片消息: image
            语音消息: voice
            视频消息: video
            小视频消息: shortvideo
            地理位置消息: location
            链接消息: link
        2. 事件消息: event，根据<Event>节点
            订阅事件: subscribe。若是扫描二维码，根据<EventKey>节点，得到：qrscene_为前缀，后面为二维码的参数值
            取消订阅事件：unsubscribe
            已关注后扫描事件：SCAN
            上报地理位置：LOCATION
            自定义菜单点击：CLICK
            点击菜单链接跳转：VIEW
        """
        msg_type = obj.get('MsgType')
        return msg_type

    @staticmethod
    def getEventType(obj):
        event_key = obj.get('EventKey')
        return event_key
