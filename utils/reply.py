# -*- coding: utf-8 -*-
import time


class Reply:
    @staticmethod
    def text(toUser='', fromUser='', content=''):
        xml = """<xml>
<ToUserName><![CDATA[{toUser}]]></ToUserName>
<FromUserName><![CDATA[{fromUser}]]></FromUserName>
<CreateTime>{now}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>
"""
        xml = xml.format(
            toUser=toUser,
            fromUser=fromUser,
            content=content,
            now=int(time.time())
        )

        return xml

    @staticmethod
    def news(toUser='', fromUser='', articles=None):
        arr = []
        for article in articles:
            item = """<item>
<Title><![CDATA[{title}]]></Title>
<Description><![CDATA[{description}]]></Description>
<PicUrl><![CDATA[{picurl}]]></PicUrl>
<Url><![CDATA[{url}]]></Url>
</item>
"""
            arr.append(item.format(
                title=article.get('title'),
                description=article.get('description'),
                picurl=article.get('picurl'),
                url=article.get('url')
            ))
        xml = """<xml>
<ToUserName><![CDATA[{toUser}]]></ToUserName>
<FromUserName><![CDATA[{fromUser}]]></FromUserName>
<CreateTime>{now}</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>{count}</ArticleCount>
<Articles>{articles}</Articles>
</xml>"""
        xml = xml.format(
            toUser=toUser,
            fromUser=fromUser,
            now=int(time.time()),
            count=len(articles),
            articles=''.join(arr)
        )

        return xml
