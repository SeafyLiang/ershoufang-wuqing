#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   eda_report.py
@Modify Time      @Author    @Version    @Description
------------      -------    --------    -----------
2021/8/18 20:28   SeafyLiang   1.0       eda报告
"""
# import pandas_profiling
import sqlalchemy
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import time, datetime
import os

from apscheduler.schedulers.blocking import BlockingScheduler

warnings.filterwarnings(action='once')

large = 22;
med = 16;
small = 12
params = {'axes.titlesize': large,
          'legend.fontsize': med,
          'figure.figsize': (16, 10),
          'axes.labelsize': med,
          'axes.titlesize': med,
          'xtick.labelsize': med,
          'ytick.labelsize': med,
          'figure.titlesize': large}
plt.rcParams.update(params)
plt.style.use('seaborn-whitegrid')

# 解决 plt 中文显示的问题 mymac
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# win10
plt.rcParams['font.sans-serif'] = ['SimHei']
# 忽略版本问题
import warnings

warnings.filterwarnings("ignore")


# 面积-价格分布散点图
def pic1(df, date):
    fig, ax = plt.subplots()
    x, y = df['area'].values, df['price'].values
    ax.scatter(x, y, alpha=0.3, edgecolors='none')

    plt.title("%s_面积-价格分布散点图" % date, fontsize=16)  # 图形标题
    plt.xlabel("面积（单位：米²）", fontsize=12)  # x轴名称
    plt.ylabel("价格（单位：万）", fontsize=12)  # y轴名称
    ax.legend()
    ax.grid(True)
    return plt


# 不同小区价格均价柱状图
def pic2(communityName_list, communityNum_list, communityPrice2m_list, date):
    x = communityName_list
    y = communityNum_list
    y2 = communityPrice2m_list
    # 画图
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # 左轴
    ax1.bar(x, y, label="小区房屋数量")
    ax1.set_xlabel('小区名')
    ax1.set_ylabel('房屋数量')
    # ax1.legend(loc='center right')
    # 显示数据标签
    for a, b in zip(x, y):
        plt.text(a, b,
                 b,
                 ha='center',
                 va='bottom',
                 )
    # 右轴
    ax2 = ax1.twinx()
    ax2.plot(x, y2, '-or', label='小区均价')
    ax2.set_ylabel('小区均价')
    ax2.legend(loc='upper right')
    # 显示数据标签
    for a, b in zip(x, y2):
        plt.text(a, b,
                 b,
                 ha='center',
                 va='bottom',
                 )
    # 标题
    plt.title('%s_小区房屋数量Top5均价柱状图' % date)
    plt.xticks([])
    plt.yticks([])
    return plt


condition_sql = "WHERE price>50 AND price<200 AND area >90 AND area<150 "

# 邮件内容str
mail_str = ""


# 查询房屋总数，单位平米均价
def cal_info(engine, date):
    # 筛选条件：价格50-200W, 面积90-150平
    global condition_sql
    sql = "SELECT title,date,village,house_plan,area,price,build_year,orientation,floor,sole,detail_web,communityName FROM house_info_%s " % date + condition_sql
    # 使用 sub 进行数据替换
    df = pd.read_sql(sql, engine)
    df['m2price'] = df['price'] / df['area']
    # 均价
    print(df['m2price'].mean())
    # 房屋统计信息
    house_describe = df.describe()
    global mail_str
    mail_str = mail_str + "\n你好，昨日：%s的房屋信息已统计完毕，" \
                          "\n筛选条件：价格50-200W, 面积90-150平" \
                          "\n房屋均价为：%f米²/万" \
                          "\n房屋统计信息为：" \
                          "\n%s" \
                          "\n\n" % (date, df['m2price'].mean(), house_describe)
    # 面积-价格分布散点图
    pic1_plt = pic1(df, date)
    pic1_plt.savefig("./house_cal_pic/0all.jpg")
    # pfr = pandas_profiling.ProfileReport(df)
    eda_report_file_path = "./eda/%s_EDA.html" % date
    # pfr.to_file(eda_report_file_path)
    # return house_info_str, eda_report_file_path


# 查询房屋数量Top5的小区
def get_communityList(engine, date):
    # 筛选条件：价格50-200W, 面积90-150平
    global condition_sql
    sql = "SELECT COUNT(id) as communityNum, communityName FROM house_info_%s " % date + condition_sql + " GROUP BY communityName ORDER BY communityNum DESC LIMIT 5 "
    # 使用 sub 进行数据替换
    df = pd.read_sql(sql, engine)
    communityName_list = df.communityName.tolist()  # ['福苑小区', '广厦南里东区', '广厦南里西区', '和平里小区南区', '广厦西里']
    communityNum_list = df.communityNum.tolist()  # [70, 65, 50, 50, 44]
    communityPrice2m_list = []
    for communityName in communityName_list:
        df_community = get_detail_from_community(engine, date, communityName)
        df_community['m2price'] = df_community['price'] / df_community['area']
        # 小区均价
        communityPrice2m_list.append(df_community['m2price'].mean())  # 1.5414622079622249
    global mail_str
    mail_str = mail_str + "\n\n近5天小区房价统计:\n"
    mail_str = mail_str + "日期：%s_小区统计信息" % date
    mail_str = mail_str + '\n小区名：' + str(communityName_list)
    mail_str = mail_str + '\n房屋数量：' + str(communityNum_list)
    mail_str = mail_str + '\n小区均价：' + str(communityPrice2m_list)
    plc2_plt = pic2(communityName_list, communityNum_list, communityPrice2m_list, date)
    return plc2_plt


# 查询指定小区房屋信息
def get_detail_from_community(engine, date, communityName):
    # 筛选条件：价格50-200W, 面积90-150平
    global condition_sql
    sql = "SELECT title,date,village,house_plan,area,price,build_year,orientation,floor,sole,detail_web,communityName FROM house_info_%s " % date + condition_sql + " AND communityName = \"%s\" " % communityName
    # 使用 sub 进行数据替换
    df = pd.read_sql(sql, engine)
    return df


# 带eda.html发邮件
def send_email(mail_title, mail_content, filePath):
    fromaddr = '894700104@163.com'
    password = 'CXPNQDEQQKVYDQZM'
    toaddrs = ['<seafyliang@icloud.com>', '<1165885015@qq.com>']

    content = mail_content
    textApart = MIMEText(content)

    htmlFile = filePath
    htmlApart = MIMEApplication(open(htmlFile, 'rb').read())
    htmlApart.add_header('Content-Disposition', 'attachment', filename=mail_title + '.html')

    m = MIMEMultipart()
    m.attach(textApart)
    m.attach(htmlApart)
    m['Subject'] = mail_title
    m['From'] = fromaddr

    try:
        server = smtplib.SMTP('smtp.163.com')
        server.login(fromaddr, password)
        for toaddr in toaddrs:
            m['To'] = toaddr
            server.sendmail(fromaddr, toaddr, m.as_string())
        print('发送邮件成功')
        server.quit()
    except smtplib.SMTPException as e:
        print('error:', e)  # 打印错误


# 小区信息图片发邮件
def send_email_jpg(mail_title, mail_content):
    fromaddr = ''
    password = ''
    toaddrs = []

    content = mail_content
    textApart = MIMEText(content)
    m = MIMEMultipart()
    m.attach(textApart)

    pic_file_list = os.listdir('./house_cal_pic')
    for pic_file in pic_file_list:
        imageFile = 'D:\Code_projects\ershoufang-master\src\house_cal_pic\%s' % pic_file
        imageApart = MIMEImage(open(imageFile, 'rb').read(), imageFile.split('.')[-1])
        imageApart.add_header('Content-Disposition', 'attachment', filename=imageFile)
        m.attach(imageApart)

    m['Subject'] = mail_title
    m['From'] = fromaddr

    try:
        server = smtplib.SMTP('smtp.163.com')
        server.login(fromaddr, password)
        for toaddr in toaddrs:
            m['To'] = toaddr
            server.sendmail(fromaddr, toaddr, m.as_string())
        print('发送邮件成功')
        server.quit()
    except smtplib.SMTPException as e:
        print('error:', e)  # 打印错误


# 获取当前时间前1天或N天的日期，beforeOfDay=1：前1天；beforeOfDay=N：前N天
def getdate(beforeOfDay):
    today = datetime.datetime.now()
    # 计算偏移量
    offset = datetime.timedelta(days=-beforeOfDay)
    # 获取想要的日期的时间
    re_date = (today + offset).strftime('%Y%m%d')
    return re_date


def start_eda():
    today = datetime.datetime.now()
    today_str = today.strftime('%Y%m%d')
    # 创建数据库连接，这里使用的是pymysql
    engine = sqlalchemy.create_engine("mysql+pymysql://root:@127.0.0.1:3306/ershoufang")
    # 昨日房价总情况
    before_date = getdate(1)
    cal_info(engine, before_date)
    # 获取前n天日期字符串
    # 1-5
    for i in range(5):
        i = i + 1
        before_date = getdate(i)
        print(before_date)
        plc2_plt = get_communityList(engine, before_date)
        plc2_plt.savefig('./house_cal_pic/%s.jpg' % str(i))
    print(mail_str)
    send_email_jpg("%s_天津武清杨村房屋数据分析" % today_str, mail_str)


if __name__ == '__main__':
    # BlockingScheduler：在进程中运行单个任务，调度器是唯一运行的东西
    scheduler = BlockingScheduler()
    # 采用阻塞的方式

    # 采用固定时间间隔（interval）的方式，每隔60*60*24秒钟（1天）执行一次
    # scheduler.add_job(start_crawler, 'interval', seconds=60*60*24)

    # 每天0：01执行任务
    scheduler.add_job(start_eda, 'cron', hour=14, minute=30)

    scheduler.start()
