#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import os
import time
import urllib
import requests
import json
from bs4 import BeautifulSoup
from src.common import *
import urllib.request
import logging
from apscheduler.schedulers.blocking import BlockingScheduler


# 第一步，创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Log等级总开关  此时是INFO
local_date = time.strftime("%Y-%m-%d", time.localtime())
# 第二步，创建一个handler，用于写入日志文件
logfile = './log/%s_ershoufang.log' % local_date
fh = logging.FileHandler(logfile, mode='a')  # open的打开模式这里可以进行参考
fh.setLevel(logging.INFO)  # 输出到file的log等级的开关

# 第三步，再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # 输出到console的log等级的开关

# 第四步，定义handler的输出格式（时间，文件，行数，错误级别，错误提示）
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 第五步，将logger添加到handler里面
logger.addHandler(fh)
logger.addHandler(ch)

# 监控间隔 6000秒
sleep_time = 6000
# 详情页间隔，防止被反爬虫
sleep_time_detail = 10
# 使用 random.randint(5, 30)替代
# 数据库
db_name = 'house_info'
# 按照最新排序
# base_url = "https://tj.lianjia.com/ershoufang/wuqing/" # 武清
base_url = 'https://tj.lianjia.com/ershoufang/yangcun/'  # 杨村

# warning_num,如果出现反爬虫次数超过10次，停止爬虫
warning_num = 0


# 解析房屋详情
# return
#       -1: 小于当天日期，不再继续
#       1: 获取网页失败，可能受限制 2: 失败，可能乱码
#       0: 正常
def get_detail(url, max_date, info):
    global warning_num
    html_text = get_html_list(url)
    if not html_text:
        logger.warning('get %s fail' % url)
        # print('get %s fail' % url)
        return 1
    write_file('html/tmp/detail_%s.html' % info.id, html_text.encode('utf-8'))
    soup = BeautifulSoup(html_text, "html.parser")
    # 调试版本
    # soup = BeautifulSoup(open('html/lianjia_detail.html'), "html.parser")

    tag = soup.find('div', class_='introContent')
    if tag is None:
        logger.warning('get %s fail' % url)
        # print('get %s fail' % url)
        return 1
    tag_tmp = tag.find('div', class_='content')
    tags = tag_tmp.find_all('li')

    # 户型
    info.house_plan = get_text(tags, 0, 4, -1)
    # 楼层
    info.floor = get_text(tags, 1, 4, -1)
    # 建筑面积
    info.area = float(get_text(tags, 2, 4, -2).strip('㎡'))
    # area_tmp = get_text(tags, 2, 4, -2).strip('㎡')
    # 朝向
    info.orientation = get_text(tags, 6, 4, -1)
    # 电梯
    info.village = get_text(tags, 9, 4, -1)
    # 供暖方式
    info.sole = get_text(tags, 10, 4, -1)
    # 装修情况
    info.build_year = get_text(tags, 8, 4, -1)
    # 小区名
    communityName_tag = soup.find('div', class_='communityName').find('a', class_='info')
    info.communityName = communityName_tag.get_text()

    tag_tmp = tag.find('div', class_='transaction')
    tag_tmp = tag_tmp.find('div', class_='content')
    tags = tag_tmp.find_all('li')

    # 发布日期
    str_date = get_text(tags, 0, 4, -1)
    # 可能存在乱码，忽略该记录
    try:
        str_date = format_date(str_date)
        info.date = int(str_date)
    except Exception as e:
        logger.warning('get_detail: "%s" : ' % url + str(e))
        # print('get_detail: "%s" : ' % url, e)
        return 2
    # # 判断日期是否超过最大
    # if (max_date > info.date):
    #     print("小于当天日期，不再继续")
    #     print('max_date=%d date=%d' % (max_date, info.date))
    #     return -1
    # TODO 可能存在重复下载的情况

    # 房本年限
    # info.room_year = get_text(tags, 4, 4, -1)
    # 小区
    # info.village = get_text(tags, 0, 5, -1)
    # 建筑年代
    # info.build_year = get_text(tags, 6, 5, -1)
    # 唯一住房
    # info.sole = get_text(tags, 17, 5, -1)

    """
        2021-08-07
        [
        00<li><span class="label">房屋户型</span>3室1厅1厨1卫</li>, 
        01<li><span class="label">所在楼层</span>中楼层 (共17层)</li>, 
        02<li><span class="label">建筑面积</span>111.72㎡</li>, 
        03<li><span class="label">户型结构</span>平层</li>, 
        04<li><span class="label">套内面积</span>暂无数据</li>, 
        05<li><span class="label">建筑类型</span>暂无数据</li>, 
        06<li><span class="label">房屋朝向</span>南 北</li>, 
        07<li><span class="label">建筑结构</span>钢混结构</li>, 
        08<li><span class="label">装修情况</span>毛坯</li>, 
        09<li><span class="label">梯户比例</span>一梯两户</li>, 
        10<li><span class="label">供暖方式</span>集中供暖</li>, 
        11<li><span class="label">配备电梯</span>暂无数据</li>
        ]
    """

    # 下载房源图片
    # img_list = []
    # tag = soup.find('div', class_='thumbnail')
    #
    # tags = tag.find('ul', class_='smallpic').find_all('li')
    # for tag in tags:
    #     if tag is None:
    #         continue
    #     img_src = tag.find('img').attrs['src']
    #
    #     if img_src.endswith('.jpg'):
    #         img_desc = tag.attrs['data-desc']
    #         img_list.append(img_src)
    #         download_img_lianjia(img_list, os.path.join('img/lianjia', info.id), img_desc)
    return 0


# 解析房屋概览
# return:
#   -1: 反爬虫  -2: 已存在  -3: 详情页错误
#   0:  正常    
def get_general(url, id_list, max_date, info, db, local_date):
    global warning_num
    html_text = get_html_list(url)
    soup = BeautifulSoup(html_text, "html.parser")
    # write_file('index.html', html_text.encode('utf-8'))
    # 调试版本
    # soup = BeautifulSoup(open('html/lianjia_list.html'), "html.parser")

    tag = soup.find('div', class_='bigImgList')
    # 链家有反爬虫限制
    if tag is None:
        logger.warning('warning: %s' % url + '反爬虫')
        warning_num = warning_num + 1
        # print('warning: %s' % url)
        # print("反爬虫")
        return -1
    tags = tag.find_all('div', class_='item')
    for tag in tags:
        # 价格
        tag_tmp = tag.find('div', class_='price')
        info.price = float(tag_tmp.get_text().strip('万'))
        # price_tmp = tag_tmp.get_text().strip('万')

        # 标题
        tag_tmp = tag.find('a', class_='title')
        info.title = tag_tmp.get_text()
        logger.info('正在爬取：' + info.title)
        # print('正在爬取：', info.title)

        # 唯一ID
        text = tag.a['href']
        begin = text.find('ershoufang/')
        end = text.find('.html')
        info.id = text[begin + 11:end]
        # 详情页网址
        info.detail_web = text

        if info.id not in id_list:
            id_list.append(info.id)
            # 解析详情页
            result = get_detail(text, max_date, info)
            if result == 0:
                # 可能存在重复
                db.insert(info, local_date)
                logger.info('%s已入库：' % info.title + str(result))
                # print('%s已入库：' % info.title, result)
                # 格式化成2016-03-20 11:45:39形式
                # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            elif result == 1:
                logger.info('未入库：' + str(result))
                # print('未入库：', result)
                continue
            else:
                logger.info('未入库：' + str(result))
                # print('未入库：', result)
                # return -2
                continue
        else:
            # 如果发布频率快，可能导致有id重复。不使用id判断
            # return -3
            logger.info("%s已存在" % info.id)
            # print("%s已存在" % info.id)
            continue

        # 降低频率，防止被反爬虫
        time.sleep(random.randint(5, 30))
    return len(tags)


def main():
    global warning_num
    # 当前日期
    local_date = time.strftime("%Y%m%d", time.localtime())
    db = house_info_db(db_name, local_date)
    id_list = []
    max_date = get_info_from_db(db, TYPE_LIANJIA, id_list, local_date)

    info = house_info()
    info.type = TYPE_LIANJIA

    # 循环监控页面
    page = 1
    while True:
        try:
            """
            https://tj.lianjia.com/ershoufang/wuqing/pg1co32/
            https://tj.lianjia.com/ershoufang/wuqing/pg2co32/                                                      
            https://tj.lianjia.com/ershoufang/wuqing/pg3co32/
            
            2021-08-07
            https://tj.lianjia.com/ershoufang/yangcun/pg2/
            https://tj.lianjia.com/ershoufang/yangcun/pg3/
            """

            if warning_num >= 10:
                break
            url = '%spg%d' % (base_url, page)
            logger.info('#' * 10)
            # print('#' * 10)
            logger.info('#' * 10 + "正在爬取第%d页" % page)
            # print('#' * 10, "正在爬取第%d页" % page, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            result = get_general(url, id_list, max_date, info, db, local_date)
            logger.info('#' * 10 + "%d页爬取完成" % page)
            # print('#' * 10, "%d页爬取完成" % page, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            if result > 1:
                page = page + 1
                time.sleep(random.randint(5, 30))
            elif result == -1:
                # 反爬虫，休息10min-30min
                time.sleep(random.randint(600, 1800))
            else:
                # 报错后 重置爬取页数，休息100min，从第一页开始重新爬取
                page = 1
                time.sleep(sleep_time)
        except Exception as e:
            print("main: ", e)
            pass


# 定时任务，每天00:01开始爬虫
def start_crawler():
    logger.info('#'*20 + "开始爬虫")
    main()


if __name__ == '__main__':
    main()
    # BlockingScheduler：在进程中运行单个任务，调度器是唯一运行的东西
    scheduler = BlockingScheduler()
    # 采用阻塞的方式

    # 采用固定时间间隔（interval）的方式，每隔60*60*24秒钟（1天）执行一次
    # scheduler.add_job(start_crawler, 'interval', seconds=60*60*24)

    # 每天0：01执行任务
    # misfire_grace_time=3600 任务的超时容错配置，给executor 一个超时时间，这个时间范围内要是该跑的还没跑完，就别再跑了
    scheduler.add_job(start_crawler, 'cron', hour=18, minute=00, misfire_grace_time=60*60*24)
    # 采用固定时间间隔（interval）的方式，每隔60*60*24秒钟(24h)执行一次
    # scheduler.add_job(start_crawler, 'interval', seconds=60*60*24)
    # 这是一个独立的线程
    scheduler.start()


