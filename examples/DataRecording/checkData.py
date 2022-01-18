# encoding: utf-8

import json
from datetime import datetime, timedelta, time
from pymongo import MongoClient, ASCENDING
from negociant.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME, TICK_DB_NAME, DAILY_DB_NAME
# from negociant.trader.markets.lkMarketHours import MarketsOpHours
from shcifcoDataService import marketHours, downMinuteBarBySymbol

# marketHours = MarketsOpHours()
mc = MongoClient('localhost', 27017)    # 创建MongoClient
drConfig = open("DR_setting.json")
drSetting = json.load(drConfig)

def isMinBarInSeccession(lastBar, bar) :
    if not marketHours.isMarketOpen(bar['symbol'], curTime=bar['datetime'].time()) :
        print("minute bar out of market hours: ", bar['symbol'], str(bar['datetime']))
        return False

    if not lastBar :
        # print("First bar", bar['datetime'].time())
        return True

    lastBarTime = lastBar['datetime']

    if (marketHours.isAtSessionOpen(bar['symbol'], curTime=bar['datetime'].time()) and 
        marketHours.isSessionClosingBar(bar['symbol'], barTime=lastBarTime.time())) :
        return True

    if bar['datetime'] == lastBarTime + timedelta(minutes=1) :
        return True

    print("minute bars not in seccession: ", bar['symbol'], str(lastBarTime), str(bar['datetime']))
    return False


def isBarDataOK(bar) :
    if bar['open'] <= 0.  or bar['high'] <= 0. or bar['low'] <= 0. or bar['close'] <= 0. :
        print("bar data <= 0: ", bar)
        return False

    if abs(bar['high'] - bar['low']) > 0.1 * bar['low'] or abs(bar['close'] - bar['open']) > 0.1 * bar['open'] :
        print("bar data invalid: ", bar)
        return False

    return True


def isDayBarFinished(bar) :
    if marketHours.isMarketClosingBar(bar['symbol'], barTime=bar['time']) :
        return True
    return False


def removeDuplicates(cl) :
    """ Ensure no duplicates in DB """
    cursor = cl.aggregate(
        [
            {"$group": {"_id": "$datetime", "unique_ids": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": { "$gte": 2 }}}
        ]
    )
    response = []
    for doc in cursor:
        del doc["unique_ids"][0]
        for id in doc["unique_ids"]:
            print("Found duplicate entry: ", id, " will remove")
            response.append(id)
    cl.remove({"_id": {"$in": response}})


def checkData(dbName, collectionName, start):
    
    cl = mc[dbName][collectionName]         # 获取数据集合
    removeDuplicates(cl)

    d = {'datetime':{'$gte':start}}         # 只过滤从start开始的数据
    cl.create_index([('datetime', 1)], unique=True)
    cx = list(cl.find(d).sort('datetime', ASCENDING))

    # print("checkData: ", dbName, collectionName, " checking num of data: ", cx)
    dataIsOK = True
    lastBar = None
    if len(cx) < 1 :
        print("Previous day has no data", dbName, collectionName)
        return False
        
    if dbName == MINUTE_DB_NAME :
        for data in cx:
            if (not isMinBarInSeccession(lastBar, data)) or (not isBarDataOK(data)) :
                dataIsOK = False
            lastBar = data
    elif dbName == DAILY_DB_NAME :
        for data in cx:
            if (not isBarDataOK(data)) or (not isDayBarFinished(data)) :
                dataIsOK = False
            
    print(u'DB：%s, Collection：%s, from：%s is %s' %(dbName, collectionName, start, dataIsOK))
    
    return dataIsOK

def checkNFillData(daysBack=None) :
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if not daysBack :
        daysBack = marketHours.weekdayOffset[datetime.today().weekday()]
    start = (today-timedelta(daysBack)).replace(hour=20, minute=58)            
    print("checking data from days abck: ", daysBack, start)

    for l in drSetting['bar']:
        dataIsOK = True
        symbol = l[0]
        if not checkData(MINUTE_DB_NAME, symbol, start) :
            print("past minute data has problem: ", symbol, str(start))
            dataIsOK = False
        if not checkData(DAILY_DB_NAME, symbol, start) :
            print("past daily data has problem: ", symbol, str(start))
            dataIsOK = False

        if not dataIsOK :
            downMinuteBarBySymbol(symbol, 1000, start)

    for l in drSetting['active']:
        dataIsOK = True
        hotSymbol = l
        symbol = drSetting['active'][hotSymbol]
        if not checkData(MINUTE_DB_NAME, hotSymbol, start) :
            print("past minute data has problem: ", symbol, str(start))
            dataIsOK = False
        if not checkData(DAILY_DB_NAME, hotSymbol, start) :
            print("past daily data has problem: ", symbol, str(start))
            dataIsOK = False
            
        if not dataIsOK :
            downMinuteBarBySymbol(symbol, 1000, start, hotSymbol=hotSymbol)
