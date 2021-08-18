#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   eda_report.py
@Modify Time      @Author    @Version    @Description
------------      -------    --------    -----------
2021/8/18 20:28   SeafyLiang   1.0       eda报告
"""
import pandas_profiling
import sqlalchemy
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

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
sns.set_style("white")

# 解决 plt 中文显示的问题 mymac
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# 忽略版本问题
import warnings

warnings.filterwarnings("ignore")


# 散点图
def pic1(df):
    fig, ax = plt.subplots()
    x, y = df['area'].values, df['price'].values
    ax.scatter(x, y, alpha=0.3, edgecolors='none')

    plt.title("面积-价格分布散点图", fontsize=16)  # 图形标题
    plt.xlabel("面积（单位：米²）", fontsize=12)  # x轴名称
    plt.ylabel("价格（单位：万）", fontsize=12)  # y轴名称
    ax.legend()
    ax.grid(True)

    plt.show()


def cal_info(date):
    # 创建数据库连接，这里使用的是pymysql
    engine = sqlalchemy.create_engine("mysql+pymysql://root:root@127.0.0.1:3306/ershoufang")
    # 筛选条件：价格50-200W, 面积90-150平
    sql = "SELECT title,date,village,house_plan,area,price,build_year,orientation,floor,sole,detail_web,communityName FROM house_info_%s WHERE price>50 AND price<200 AND area >90 AND area<150;" % date
    # 使用 sub 进行数据替换
    df = pd.read_sql(sql, engine)
    df['m2price'] = df['price'] / df['area']
    # 均价
    print(df['m2price'].mean())
    # 房屋统计信息
    house_describe = df.describe()

    house_info_str = "\n你好，%s的房屋信息已统计完毕，" \
                     "\n房屋均价为：%f米²/万" \
                     "\n房屋统计信息为：" \
                     "\n%s" \
                     "\n\n" \
                     "EDA数据分析报告为附件内容，电脑浏览器打开可进行交互操作" % (date, df['m2price'].mean(), house_describe)

    pfr = pandas_profiling.ProfileReport(df)
    eda_report_file_path = "./eda/%s_EDA.html" % date
    pfr.to_file(eda_report_file_path)
    return house_info_str, eda_report_file_path


def send_email(mail_title, mail_content, filePath):
    fromaddr = '894700104@163.com'
    password = 'xxx'
    toaddrs = ['<seafyliang@icloud.com>', '<1165885015@qq.com>']

    content = mail_content
    textApart = MIMEText(content)

    htmlFile = filePath
    htmlApart = MIMEApplication(open(htmlFile, 'rb').read())
    htmlApart.add_header('Content-Disposition', 'attachment', filename=mail_title)

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


if __name__ == '__main__':
    cal_date = '20210808'
    house_str, file_path = cal_info(cal_date)
    send_email("%s房屋EDA数据分析报告" % cal_date, house_str, file_path)
