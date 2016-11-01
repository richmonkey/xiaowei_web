# -*- coding: utf-8 -*-
from utils.type_definition import TypeDefinition


class AppType(TypeDefinition):
    """客户端类型
    """
    CONFIDENTIAL = 2
    PUBLIC = 1


class PlatformType(TypeDefinition):
    """客户端类型
    """
    ANDROID = 1
    IOS = 2


class ObjectType(TypeDefinition):
    """全局对象类型
    """
    USER = 1
    ACCOUNT = 2
    DEVELOPER = 3
    CHANNEL = 4
    APP = 5
    CLIENT = 6
    PACKAGE = 7


class RoleType(TypeDefinition):
    """角色对象类型
    """
    DEVELOPER = 1
    SELLER = 2


class EmailUsageType(TypeDefinition):
    """邮件类型
    """
    DEVELOPER_VERIFY = 1
    DEVELOPER_RESET_PWD = 2

    # 客服注册
    SELLER_VERIFY = 3
    SELLER_RESET_PWD = 4


class GrantType(TypeDefinition):
    SMS_CODE = 1
    CLIENT_CREDENTIALS = 2
    ACCOUNT_CREDENTIALS = 3
    SNS_TOKEN = 4


class DeveloperPermType(TypeDefinition):
    """
    权限掩码
    """
    # 1
    STATS = 0b0000000000000001
    # 2
    RECONCILIATION = 0b0000000000000010
    # 4
    PUSH = 0b0000000000000100
    # 8
    APPS = 0b0000000000001000
    # 16
    ACCOUNT = 0b0000000000010000
    # 65535
    ADMIN = 0b1111111111111111


class PushAppType(TypeDefinition):
    """推送应用类型
    """
    GAME = 1
    APP = 2


class PushType(TypeDefinition):
    """推送类型
    1-4 通知(1打开应用,3打开网页,4打开应用指定页面),5 消息
    """
    OPEN_APP = 1
    OPEN_URL = 3
    OPEN_APP_ACTIVITY = 4
    MESSAGE = 5
    OPEN_SELF_APP = 6
    OPEN_SELF_APP_ACTIVITY = 7


class PushChannelType(TypeDefinition):
    """ 推送渠道类型
    """
    CHANNEL_WEB = 0  # 网页推送
    CHANNEL_SMART = 1  # 规则推送
    CHANNEL_VIRTUAL = 2  # 虚拟推送
