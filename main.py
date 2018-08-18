# -*- coding: utf-8 -*-
# @File : main.py

import csv
import json
import threading
import requests
import datetime
import time

lock = threading.Lock()

# 待爬取日期的集合
dateList = []
tag = 0


# 多线程爬取页面信息
def getData(date):
    """爬取页面信息"""

    url = 'https://piaofang.maoyan.com/cinema/filter?typeId=0&date=%s&offset=0&limit=6439' % date

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cookie": "_lxsdk_cuid=1646efd05fcc8-0cce803a56090f-5e4b2519-100200-1646efd05fcc8; _lxsdk=1646efd05fcc8-0cce803a56090f-5e4b2519-100200-1646efd05fcc8; _lxsdk_s=1646f3e8899-4f5-fd4-913%7C%7C1; __mta=48993817.1530870433354.1530870774835.1530874726592.4",
        "referer": "https://piaofang.maoyan.com/company/cinema",
        "uid": "cdc80d3a3878a9dec021f64fe7a2f70f5ecc622e",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    try:
        response = requests.get(url, headers=headers)
        response = response.json()
        dayData = response['data']
        detailData = dayData['list']
    except:
        global dateList
        print(date)
        with lock:
            dateList.append(date)
    else:
        allData = {}
        for dataDict in detailData:
            # 影院ID
            cinemaId = dataDict['cinemaId']
            # 影院名称
            cinemaName = dataDict['cinemaName']
            # 观影人次
            viewInfo = dataDict['viewInfo']
            # 场均人次
            avgShowView = dataDict['avgShowView']
            # 平均票价
            avgViewBox = dataDict['avgViewBox']

            allData[cinemaId] = [cinemaName, viewInfo, avgShowView, avgViewBox]
        with open('./cinemadata/%s.json' % date, mode='w+', errors='ignore') as f:
            json.dump(allData, f)
            global tag
            tag += 1
            print('%s写入完成%d' % (date, tag))


# 生成带爬日期集合
def createDateList(start, end):

    dateStart = datetime.datetime.strptime(start, '%Y-%m-%d')
    dateEnd = datetime.datetime.strptime(end, '%Y-%m-%d')

    while dateStart <= dateEnd:
        dateList.append(dateStart.date())
        dateStart += datetime.timedelta(days=1)
    return dateList


# 获取2017年的数据
def getYearData(year):

    start = f'{year}-01-01'
    end = f'{year}-12-31'

    global dateList

    dateList = createDateList(start, end)
    tlist = []
    while dateList:
        with lock:
            day = dateList.pop()
        t = threading.Thread(target=getData, args=(day,))
        t.start()
        tlist.append(t)
        time.sleep(0.3)
    for t in tlist:
        t.join()


# 对多线程爬取的json数据清洗+统计+排序保存
def dataSorting(year):

    start = f'{year}-01-01'
    end = f'{year}-12-31'

    dateList = createDateList(start, end)
    finData = {}
    for date in dateList:
        with open('./cinemadata/%s.json' % date, 'r', encoding='utf-8') as f:
            jsonData = json.load(f)
        for cid, vals in jsonData.items():
            if cid not in finData.keys():
                finData.setdefault(cid, ['#', 0, 0.0, 0.0])
                # print(finData)
            finData[cid][0] = vals[0]
            if vals[1].isdigit():
                finData[cid][1] += eval(vals[1])
            else:
                # print(vals[1])
                finData[cid][1] += eval(vals[1].replace('.', '').replace('万', '0000'))
            finData[cid][2] += eval(vals[2])
            try:
                finData[cid][3] += eval(vals[3])
            except SyntaxError:
                print(vals[3])  # 原数据为部分影院票房为0，平均票价为--
        print('%s整理完成！' % date)

    result = [[v[0], v[1], format(v[2] / 365, '.2f'), format(v[3] / 365, '.2f')] for v in finData.values()]

    with open('./findata.txt', 'w+', encoding='utf-8', errors='ignore') as f:
        for d in finData.items():
            f.write(str(d) + '\n')

    with open('./result.csv', 'w+', encoding='utf-8', errors='ignore', newline='') as f:
        writer = csv.writer(f)
        for i in result:
            writer.writerow(i)


def main():
    year = input('请输入年份：')
    getYearData(year)
    dataSorting(year)
    print('over! 数据整理为')

if __name__ == '__main__':
    main()
