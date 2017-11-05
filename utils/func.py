# -*- coding: utf-8 -*-
import re
import string
import urllib
import urlparse
import random
import base64
from StringIO import StringIO
import struct
from itertools import izip, cycle
import logging
from logging.handlers import TimedRotatingFileHandler
import os

LETTERS = 0b001
DIGITS = 0b010
PUNCTUATION = 0b100

LOGGERS = {}


def valid_email(email):
    email = str(email)
    if len(email) > 7:
        pattern = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        if re.match(pattern, email) is not None:
            return True

    return False


def random_ascii_string(length, mask=None):
    if mask is None:
        mask = LETTERS | DIGITS

    unicode_ascii_characters = ''
    if mask & LETTERS:
        unicode_ascii_characters += string.ascii_letters.decode('ascii')
    if mask & DIGITS:
        unicode_ascii_characters += string.digits.decode('ascii')
    if mask & PUNCTUATION:
        unicode_ascii_characters += string.punctuation.decode('ascii')

    if not unicode_ascii_characters:
        return ''

    rnd = random.SystemRandom()
    return ''.join([rnd.choice(unicode_ascii_characters) for _ in xrange(length)])


def url_query_params(url):
    """
    从特定的url中提取出query string字典
    """
    return dict(urlparse.parse_qsl(urlparse.urlparse(url).query, True))


def url_dequery(url):
    """
    去掉url中query string
    """
    url = urlparse.urlparse(url)
    return urlparse.urlunparse((url.scheme,
                                url.netloc,
                                url.path,
                                url.params,
                                '',
                                url.fragment))


def build_url(base, additional_params=None):
    """
    url中增加query string参数
    """
    url = urlparse.urlparse(base)
    query_params = {}
    query_params.update(urlparse.parse_qsl(url.query, True))
    if additional_params is not None:
        query_params.update(additional_params)
        for k, v in additional_params.iteritems():
            if v is None:
                query_params.pop(k)

    return urlparse.urlunparse((url.scheme,
                                url.netloc,
                                url.path,
                                url.params,
                                urllib.urlencode(query_params),
                                url.fragment))


def xor_crypt_string(data, key, encode=False, decode=False):
    if decode:
        missing_padding = 4 - len(data) % 4
        if missing_padding:
            data += b'=' * missing_padding
        data = base64.decodestring(data)
    xored = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(key)))
    if encode:
        return base64.encodestring(xored).strip().strip('=')
    return xored


def init_logger(name):
    log_dir = getattr(init_logger, 'log_dir', None)
    log_formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s %(funcName)s %(filename)s:%(lineno)d: %(message)s')

    if not log_dir:
        if 'stdout' not in LOGGERS:
            LOGGERS['stdout'] = logger = logging.getLogger()
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(log_formatter)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.DEBUG)

        return LOGGERS['stdout']

    logger = LOGGERS.get(name)
    if logger is not None:
        return logger

    if name is None:
        logfile_name = 'root'
    else:
        logfile_name = name

    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, logfile_name),
        'midnight', 1, 15)
    file_handler.suffix = '%Y%m%d'
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    LOGGERS[name] = logger

    return logger


COUNTRY_ZONE = ('86',)


def parse_mobile(mobile_str):
    match = re.findall(r'^(\+({0}))?(\d+)$'.format('|'.join(COUNTRY_ZONE)), mobile_str)
    if match:
        zone, mobile = match[0][-2:]
        if '+' in mobile_str and not zone:
            return None
        if not zone:
            zone = '86'
        return valid_mobile(zone, mobile)
    return None


def valid_mobile(mobile_zone, mobile):
    if mobile_zone == '86' and re.match(r'^1\d{10}$', mobile) is not None:
        return mobile_zone, mobile

    return None

def amr_duration(body):
    packed_size = [12, 13, 15, 17, 19, 20, 26, 31, 5, 0, 0, 0, 0, 0, 0, 0]
    duration = -1
    length = len(body)
    pos = 6
    frame_count = 0
    packed_pos = -1
     
    if length == 0:
        return 0

    while pos <= length:
        if pos == length:
            duration = (length-6)/650
            break
        t, = struct.unpack("!B", body[pos])
        packed_pos = (t >> 3) & 0x0F
        pos += packed_size[packed_pos] + 1
        frame_count += 1
     
    duration += frame_count*20
    duration = math.ceil(duration/1000.0)
    return duration


class UnknownImageFormat(Exception):
    pass

def get_image_size(data):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct modules from core
    """
    size = len(data)
    input = StringIO(data)

    height = -1
    width = -1
    data = input.read(25)

    if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
        # GIFs
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)
    elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
          and (data[12:16] == 'IHDR')):
        # PNGs
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)
    elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
        # older PNGs?
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)
    elif (size >= 2) and data.startswith('\377\330'):
        # JPEG
        msg = " raised while trying to decode as JPEG."
        input.seek(0)
        input.read(2)
        b = input.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = input.read(1)
                while (ord(b) == 0xFF): b = input.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    input.read(3)
                    h, w = struct.unpack(">HH", input.read(4))
                    break
                else:
                    input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                b = input.read(1)
            width = int(w)
            height = int(h)
        except struct.error:
            raise UnknownImageFormat("StructError" + msg)
        except ValueError:
            raise UnknownImageFormat("ValueError" + msg)
        except Exception as e:
            raise UnknownImageFormat(e.__class__.__name__ + msg)
    else:
        raise UnknownImageFormat(
            "Sorry, don't know how to get information from this file."
        )

    return width, height
