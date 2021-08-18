#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import time
import urllib
import urllib.request
import random

import requests
import pymysql
import sqlite3
from bs4 import BeautifulSoup

TYPE_ANJUKE = 0
TYPE_58 = 1
TYPE_LIANJIA = 3

# Some User Agents
hds = [{'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}, \
       {
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'}, \
       {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'}, \
       {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'}, \
       {
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36'}, \
       {
           'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'}, \
       {
           'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'}, \
       {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0'}, \
       {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'}, \
       {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'}, \
       {
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'}, \
       {'User-Agent': 'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11'}, \
       {'User-Agent': 'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11'}]


# TODO
def get_html_list(url):
    try:
        # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
        #                          'Chrome/51.0.2704.63 Safari/537.36'}
        headers = hds[random.randint(0, len(hds) - 1)]
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except Exception as e:
        print('get html: ', e)
        return None


# TODO
def write_file(file_name, content):
    fd = open(file_name, 'wb+')
    fd.write(content)
    fd.close()


# TODO
def read_file(file_name):
    fd = open(file_name, 'r')
    lines = fd.readlines()
    fd.close()
    return lines


# url = "https://tianjin.anjuke.com/sale/wuqingqu/"
url = 'https://tianjin.anjuke.com/sale/wuqingqu-q-tjycj/#'
"""
url = "https://tianjin.anjuke.com/prop/view/A1572029927?from=filter&spread=filtersearch&invalid=1&position=1&kwtype=filter&now_time=1548398057"

text = get_html_list(url)

#print text.encode('utf8')

# write file
write_file('index.html', text.encode('utf8'))
"""


class house_info:
    def __init__(self):
        # 房源ID
        self.id = ''
        # 标题
        self.title = ''
        # 发布日期
        self.date = 1990
        # 小区
        self.village = ''
        # 户型
        self.house_plan = ''
        # 建筑面积
        self.area = 0.00
        # 价格
        self.price = 0.00
        # 建筑年代
        self.build_year = ''
        # 朝向
        self.orientation = ''
        # 楼层
        self.floor = ''
        # 房本年限
        self.room_year = ''
        # 唯一住房
        self.sole = ''
        # 详情页网址
        self.detail_web = ''
        # 房源类型 0：anjuke
        self.type = TYPE_ANJUKE
        # 小区名
        self.communityName = ''


# 当前日期
local_date = time.strftime("%Y%m%d", time.localtime())


class house_info_db:
    def __init__(self, db_name):
        # sqllite
        # self.con = sqlite3.connect(db_name, check_same_thread=False)
        # mysql
        self.con = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='ershoufang',
                                   charset='utf8')
        self.cur = self.con.cursor()

        # 当前日期建表
        global local_date
        # 房源ID,标题,发布日期,小区,户型,建筑面积,价格,建筑年代,朝向,楼层,房本年限,唯一住房,详情页网址,房源类型，小区名
        self.cur.execute(
            'create table if not exists house_info_%s(id VARCHAR(30) primary key,title VARCHAR(100),' % local_date +
            'date VARCHAR(10),village VARCHAR(30),house_plan VARCHAR(10),area float(10,2),price float(10,2),' +
            'build_year VARCHAR(10),orientation VARCHAR(10),floor VARCHAR(10),room_year VARCHAR(10),' +
            'sole VARCHAR(10),detail_web VARCHAR(100),type int,communityName VARCHAR(30));')
        self.con.commit()

    def insert(self, info):
        try:
            # 当前日期
            local_date = time.strftime("%Y%m%d", time.localtime())
            sql = 'insert into house_info_%s values ("%s","%s",%d,"%s","%s","%f","%f","%s","%s","%s","%s","%s", "%s", %d, "%s")' % \
                  (local_date, info.id, info.title, info.date, info.village, info.house_plan, info.area, info.price,
                   info.build_year, info.orientation, info.floor, info.room_year, info.sole, info.detail_web, info.type, info.communityName)
            # sql = sql.decode('utf-8')
            self.cur.execute(sql)
            self.con.commit()
        except Exception as e:
            self.con.rollback()
            print('insert: ', e)

    def query_ids(self, type, id_list):
        # 当前日期
        global local_date
        sql = 'select id from house_info_%s where type=%d;' % (local_date, type)
        self.cur.execute(sql)
        results = self.cur.fetchall()
        for result in results:
            id_list.append(result[0])

    def query_max_date(self, type):
        # 当前日期
        global local_date
        sql = 'select max(date) from house_info_%s where type=%d;' % (local_date, type)
        self.cur.execute(sql)
        results = self.cur.fetchone()
        if len(results) > 0 and results[0]:
            return int(results[0])
        else:
            return 0


"""
# 自定义三目运算符
def yes_or_no(value1, value2, yes, no):
    if value1 == value2:
        return yes
    return no
"""


# 2019年01月25日 -> 20190105
def format_date(str_date):
    str_date = str_date.replace(u'年', '').replace(u'月', '').replace(u'日', '').replace(u'-', '')
    if len(str_date) == 4:
        localtime = time.localtime(time.time())
        str_date = str(localtime.tm_year) + str_date
    return str_date


# 20190131
def get_localdate():
    localtime = time.localtime(time.time())
    return localtime.tm_year


# 从数据库获取缓存信息：id_list and max_date
def get_info_from_db(db, type, id_list):
    max_date = db.query_max_date(type)
    # if max_date == 0:
    db.query_ids(type, id_list)
    return max_date


# 下载图片
def download_img(url_list, path):
    name = 0
    if len(url_list) == 0:
        return
    if not os.path.exists(path):
        os.makedirs(path)
    for url in url_list:
        try:
            urllib.urlretrieve(url, os.path.join(path, '%d.jpg' % name))
        except Exception as e:
            print('[url:error] -> [%s:%s]' % (url, e))
        name += 1


# 链家下载图片
def download_img_lianjia(url_list, path, name):
    if len(url_list) == 0:
        return
    if not os.path.exists(path):
        os.makedirs(path)
    for url in url_list:
        try:
            urllib.request.urlretrieve(url, os.path.join(path, '%s.jpg' % name))
        except Exception as e:
            print('[url:error] -> [%s:%s]' % (url, e))


# 获取属性值：清除字段中的多余字符
def get_text(tags, index, begin, end):
    text = tags[index].get_text()
    text = text.replace('	', '').replace('\n', '').replace(' ', '')
    # 只有当end为-1时，获取到结束
    if end == -1:
        text = text[begin:]
    else:
        text = text[begin:end]
    return text


def get_text_foramt(text):
    return text.replace('	', '').replace('\n', '').replace(' ', '')
