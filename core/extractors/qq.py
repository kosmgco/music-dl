#!/usr/bin/env python  
#-*- coding:utf-8 _*-  
"""
@author: HJK 
@file: qq.py
@time: 2019-01-09

QQ音乐搜索和下载

"""

import datetime
import random
from core.common import *
from core.exceptions import *
from core.extractor import Extractor
from utils.customlog import CustomLog

logger = CustomLog(__name__).getLogger()

class QQ(Extractor):
    def __init__(self,session):
        super(QQ, self).__init__(session)

    def search(self, keyword, count=5) -> list:
        ''' 搜索音乐 '''
        params = {
            'w': keyword,
            'format': 'json',
            'p': 1,
            'n': count
        }
        self.session.headers.update(glovar.FAKE_HEADERS)
        self.session.headers.update({
            'referer': 'http://m.y.qq.com',
            'User-Agent': glovar.IOS_USERAGENT
        })

        music_list = []
        r = self.session.get('http://c.y.qq.com/soso/fcgi-bin/search_for_qq_cp', params=params)
        if r.status_code != requests.codes.ok:
            raise RequestError(r.text)
        j = r.json()
        if j['code'] != 0:
            raise ResponseError(j)

        for m in j['data']['song']['list']:
            # 获得歌手名字
            singers = []
            for singer in m['singer']:
                singers.append(singer['name'])

            # size = m['size320'] or m['size128']
            size = m['size128']
            music = {
                'title': m['songname'],
                'id': m['songid'],
                'mid': m['songmid'],
                'duration': str(datetime.timedelta(seconds=m['interval'])),
                'singer': '、'.join(singers),
                'album': m['albumname'],
                # 'ext': m['ExtName'],
                'size': round(size / 1048576, 2),
                'source': 'qq'
            }

            music_list.append(music)

        return music_list


    def download(self, music):
        ''' 根据songmid等信息获得下载链接 '''
        # 计算vkey
        guid = str(random.randrange(1000000000, 10000000000))
        params = {
            'guid': guid,
            'format': 'json',
            'json': 3
        }
        self.session.headers.update(glovar.FAKE_HEADERS)
        self.session.headers.update({
            'referer': 'http://y.qq.com',
            'User-Agent': glovar.IOS_USERAGENT
        })

        r = self.session.get('http://base.music.qq.com/fcgi-bin/fcg_musicexpress.fcg', params=params)
        if r.status_code != requests.codes.ok:
            raise RequestError(r.text)
        j = r.json()
        if j['code'] != 0:
            raise ResponseError(j)

        vkey = j['key']

        for prefix in ['M800', 'M500', 'C400']:
            url = 'http://dl.stream.qqmusic.qq.com/%s%s.mp3?vkey=%s&guid=%s&fromtag=1' % \
                  (prefix, music['mid'], vkey, guid)
            size = content_length(self.session, url)
            if size > 0:
                music['url'] = url
                music['rate'] = 320 if prefix == 'M800' else 128
                music['size'] = round(size / 1048576, 2)
                break

        music['name'] = '%s - %s.mp3' % (music['title'], music['singer'])

        music_download(music)
