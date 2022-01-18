# encoding: utf-8

from __future__ import print_function
import json
import random

from time import sleep
from datetime import datetime, timedelta, time

from pymongo import MongoClient, ASCENDING

from negociant.data.shcifco.vnshcifco import ShcifcoApi, PERIOD_1MIN
from negociant.trader.vtObject import VtBarData
from negociant.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME, DAILY_DB_NAME
from negociant.trader.lkBarsEngine import BarGenerator
from negociant.trader.markets.lkMarketHours import MarketsOpHours

# 加载配置
config = open('shcifcoConfig.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
SHCIFCO_IP = setting['SHCIFCO_IP']
SHCIFCO_PORT  = setting['SHCIFCO_PORT']
SHCIFCO_TOKEN = setting['SHCIFCO_TOKEN']
# SYMBOLS = setting['SYMBOLS']

api = ShcifcoApi(SHCIFCO_IP, SHCIFCO_PORT, SHCIFCO_TOKEN)       # 历史行情服务API对象
mc = MongoClient(MONGO_HOST, MONGO_PORT)                        # Mongo连接
dbm = mc[MINUTE_DB_NAME]  
dbd = mc[DAILY_DB_NAME]                                    
dbSymbol = ''

marketHours = MarketsOpHours()

#----------------------------------------------------------------------
def generateVtBar(d):
    """生成K线"""
    bar = VtBarData()
    
    bar.symbol = d['symbol']
    bar.vtSymbol = d['symbol']
    bar.date = d['date']
    bar.time = ':'.join([d['time'][:2], d['time'][2:]])
    bar.open = d['open']
    bar.high = d['high']
    bar.low = d['low']
    bar.close = d['close']
    bar.volume = d['volume']
    bar.openInterest = d['openInterest']
    bar.datetime = datetime.strptime(' '.join([bar.date, bar.time]), '%Y%m%d %H:%M')    
    
    return bar

def onDayBar(bar) :
    flt = {'datetime': bar.datetime}
    cld = dbd[dbSymbol]   
    print("Filling in day bar: ", dbSymbol, flt)
    cld.replace_one(flt, bar.__dict__, True)

#----------------------------------------------------------------------
def downMinuteBarBySymbol(symbol, num, start, hotSymbol=''):
    """下载某一合约的分钟线数据"""
    
    global dbSymbol
    dbSymbol = symbol
    if hotSymbol :
        dbSymbol = hotSymbol

    cl = dbm[dbSymbol]   
    cl.ensure_index([('datetime', ASCENDING)], unique=True)         
    
    l = api.getHisBar(symbol, num, period=PERIOD_1MIN)
    if not l:
        print(symbol, ' download failed')
        return

    print("Saving downloaded data after: ", start, symbol, hotSymbol)

    for d in l:
        bar = generateVtBar(d)
        if bar.datetime > start :
            d = bar.__dict__
            flt = {'datetime': bar.datetime}
            # print("shcifco data downloaded but not put in DB: ", str(bar.datetime), symbol, hotSymbol)
            cl.replace_one(flt, d, True)    

    if marketHours.isMarketDayFinished(symbol) :
        d = {'datetime':{'$gte':start}}         # 只过滤从start开始的数据
        cx = list(cl.find(d).sort('datetime', ASCENDING))

        li = []
        for data in cx:
            bar = VtBarData()
            bar.__dict__ = data
            li.append(bar)

        bm = BarGenerator(onDayBar=onDayBar)
        bm.fillDayBarsWithMinute(li)
        bm.finalizeDay()
    else :
        print("Market day not finished, day bar left unfinalized")

    print(u'Contract %s downloaded %s - %s' %(symbol, generateVtBar(l[0]).datetime,
                                                  generateVtBar(l[-1]).datetime))

#----------------------------------------------------------------------
def downloadAllMinuteBar(num):
    """下载所有配置中的合约的分钟线数据"""
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    drConfig = open("DR_setting.json")
    drSetting = json.load(drConfig)
    
    for l in drSetting['bar']:
        symbol = l[0]
        downMinuteBarBySymbol(symbol, num)
        sleep(1)

    for l in drSetting['active']:
        hotSymbol = l
        symbol = drSetting['active'][hotSymbol]
        downMinuteBarBySymbol(symbol, num, hotSymbol)
        sleep(1)

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)


    