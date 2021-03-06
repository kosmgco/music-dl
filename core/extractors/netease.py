#!/usr/bin/env python  
#-*- coding:utf-8 -*-  
"""
@author: HJK 
@file: netease.py 
@time: 2019-01-11

网易云音乐下载

"""

import binascii
import json
import datetime
from Crypto.Cipher import AES
from core.common import *
from core.exceptions import *
from core.extractor import Extractor


class Netease(Extractor):
    def __init__(self, session):
        super(Netease, self).__init__(session)

    def search(self, keyword, count=5) -> list:
        ''' 从网易云音乐搜索 '''
        eparams = {
            'method': 'POST',
            'url': 'http://music.163.com/api/cloudsearch/pc',
            'params': {
                's': keyword,
                'type': 1,
                'offset': 0,
                'limit': count
            }
        }
        data = {'eparams': self._encode_netease_data(eparams)}

        self.session.headers.update(glovar.FAKE_HEADERS)
        self.session.headers.update({
            'referer': 'http://music.163.com/',
        })
        r = self.session.post('http://music.163.com/api/linux/forward', data=data)

        if r.status_code != requests.codes.ok:
            raise RequestError(r.text)
        j = r.json()
        if j['code'] != 200:
            raise ResponseError(j)

        music_list = []
        for m in j['result']['songs']:
            if m['privilege']['fl'] == 0:
                # 没有版权
                continue
            # 获得歌手名字
            singers = []
            for singer in m['ar']:
                singers.append(singer['name'])
            # 获得最优音质的文件大小
            if m['privilege']['fl'] >= 320000:
                size = m['h']['size']
            elif m['privilege']['fl'] >= 192000:
                size = m['m']['size']
            else:
                size = m['l']['size']

            music = {
                'title': m['name'],
                'id': m['id'],
                'duration': str(datetime.timedelta(seconds=int(m['dt']/1000))),
                'singer': '、'.join(singers),
                'album': m['al']['name'],
                'size': round(size / 1048576, 2),
                'source': 'netease'
            }
            music_list.append(music)

        return music_list


    def download(self, music):
        ''' 从网易云音乐下载 '''
        eparams = {
            'method': 'POST',
            'url': 'http://music.163.com/api/song/enhance/player/url',
            'params': {
                'ids': [music['id']],
                'br': 320000,
            }
        }
        data = {'eparams': self._encode_netease_data(eparams)}

        self.session.headers.update(glovar.FAKE_HEADERS)
        self.session.headers.update({
            'referer': 'http://music.163.com/',
        })
        r = self.session.post('http://music.163.com/api/linux/forward', data=data)

        if r.status_code != requests.codes.ok:
            raise RequestError(r.text)
        j = r.json()
        if j['code'] != 200:
            raise ResponseError(j)

        music['url'] = j['data'][0]['url']
        music['rate'] = int(j['data'][0]['br'] / 1000)
        music['size'] = round(j['data'][0]['size'] / 1048576, 2)
        music['name'] = '%s - %s.mp3' % (music['title'], music['singer'])

        music_download(music)


    def _encode_netease_data(self, data) -> str:
        data = json.dumps(data)
        key = binascii.unhexlify('7246674226682325323F5E6544673A51')
        encryptor = AES.new(key, AES.MODE_ECB)
        # 补足data长度，使其是16的倍数
        pad = 16 - len(data) % 16
        fix = chr(pad) * pad
        return binascii.hexlify(encryptor.encrypt(data + fix)).upper().decode()

