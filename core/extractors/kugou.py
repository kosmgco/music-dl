#!/usr/bin/env python  
# -*- coding:utf-8 _*-
"""
@author: HJK 
@file: kugou.py 
@time: 2019-01-08

酷狗音乐搜索和下载

"""

import datetime
from core.common import *
from core.exceptions import *
from core.extractor import Extractor
from utils.customlog import CustomLog

logger = CustomLog(__name__).getLogger()


class Kugou(Extractor):
    def __init__(self, session):
        super(Kugou, self).__init__(session)

    def search(self, keyword, count=5) -> list:
        ''' 搜索音乐 '''
        params = {
            'keyword': keyword,
            'platform': 'WebFilter',
            'format': 'json',
            'page': 1,
            'pagesize': count
        }
        self.session.headers.update(glovar.FAKE_HEADERS)
        self.session.headers.update({'referer': 'http://www.kugou.com'})

        music_list = []
        resp = self.session.get('http://songsearch.kugou.com/song_search_v2', params=params)
        if resp.status_code != requests.codes.ok:
            raise RequestError(resp.text)
        j = resp.json()
        if j['status'] != 1:
            raise ResponseError(j)

        for m in j['data']['lists']:
            music = {
                'title': m['SongName'],
                'id': m['Scid'],
                'hash': m['FileHash'],
                'duration': str(datetime.timedelta(seconds=m['Duration'])),
                'singer': m['SingerName'],
                'album': m['AlbumName'],
                'size': round(m['FileSize'] / 1048576, 2),
                'source': 'kugou'
            }
            # 如果有更高品质的音乐选择高品质（尽管好像没什么卵用）
            if m['SQFileHash'] and m['SQFileHash'] != '00000000000000000000000000000000':
                music['hash'] = m['SQFileHash']
            elif m['HQFileHash'] and m['HQFileHash'] != '00000000000000000000000000000000':
                music['hash'] = m['HQFileHash']

            music_list.append(music)

        return music_list

    def download(self, music):
        ''' 根据hash从酷狗下载音乐 '''
        params = {
            'cmd': 'playInfo',
            'hash': music['hash']
        }
        self.session.headers.update(glovar.FAKE_HEADERS)
        self.session.headers.update({
            'referer': 'http://m.kugou.com',
            'User-Agent': glovar.IOS_USERAGENT
        })

        r = self.session.get('http://m.kugou.com/app/i/getSongInfo.php', params=params)
        if r.status_code != requests.codes.ok:
            raise RequestError(r.text)
        j = r.json()
        if j['status'] != 1:
            raise ResponseError(j)

        music = {
            'ext': j.get('extName', ''),
            'name': j.get('fileName', '') + '.' + j.get('extName', ''),
            'size': round(j.get('fileSize') / 1048576, 2),
            'rate': j.get('bitRate', ''),
            'url': j.get('url')
        }
        music_download(music)
