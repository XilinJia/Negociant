'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

# encoding: UTF-8

'''
本文件中实现了行情数据记录引擎，用于汇总TICK数据，并生成K线插入数据库。

使用DR_setting.json来配置需要收集的合约，以及主力合约代码。
'''

import json
import csv
import os
import copy
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta, time
from Queue import Queue, Empty
from threading import Thread
from pymongo.errors import DuplicateKeyError

from negociant.event import Event
from negociant.trader.vtEvent import *
from negociant.trader.vtFunction import todayDate, getJsonPath
from negociant.trader.vtObject import VtSubscribeReq, VtLogData, VtBarData, VtTickData
from negociant.trader.lkBarsEngine import BarGenerator
from negociant.trader.markets.lkMarketHours import MarketsOpHours

from .drBase import *
from .language import text



########################################################################
class DrEngine(object):
    """数据记录引擎"""
    
    settingFileName = 'DR_setting.json'
    settingFilePath = getJsonPath(settingFileName, __file__)  

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # 当前日期
        self.today = todayDate()
        
        # 主力合约代码映射字典，key为具体的合约代码（如IF1604），value为主力合约代码（如IF0000）
        self.activeSymbolDict = {}
        
        # Tick对象字典
        self.tickSymbolSet = set()
        
        # K线合成器字典
        self.bgDict = {}
        
        # 配置字典
        self.settingDict = OrderedDict()
        
        # 负责执行数据库插入的单独线程相关
        self.active = False                     # 工作状态
        self.queue = Queue()                    # 队列
        self.thread = Thread(target=self.run)   # 线程

        self.lastTick = {}
        
        # 收盘相关
        self.marketCloseTime = None             # 收盘时间
        self.timerCount = 0                     # 定时器计数
        self.lastTimerTime = None               # 上一次记录时间

        # load market hours to be used as time filters
        self.marketHours = MarketsOpHours()
        
        
    def initAll(self) :
        # 载入设置，订阅行情
        self.loadSetting()

        # 启动数据插入线程
        self.start()
    
        # 注册事件监听
        self.registerEvent()  

    #----------------------------------------------------------------------
    def loadSetting(self):
        """加载配置"""
        with open(self.settingFilePath) as f:
            drSetting = json.load(f)

            # 如果working设为False则不启动行情记录功能
            working = drSetting['working']
            if not working:
                return
            
            # 加载收盘时间
            if 'marketCloseTime' in drSetting:
                timestamp = drSetting['marketCloseTime']
                self.marketCloseTime = datetime.strptime(timestamp, '%H:%M:%S').time()

            # 主力合约记录配置
            if 'active' in drSetting:
                d = drSetting['active']
                self.activeSymbolDict = {vtSymbol:activeSymbol for activeSymbol, vtSymbol in d.items()}

            # Tick记录配置
            if 'tick' in drSetting:
                l = drSetting['tick']

                for setting in l:
                    symbol = setting[0]
                    gateway = setting[1]
                    vtSymbol = symbol

                    req = VtSubscribeReq()
                    req.symbol = setting[0]

                    # 针对LTS和IB接口，订阅行情需要交易所代码
                    if len(setting)>=3:
                        req.exchange = setting[2]
                        vtSymbol = '.'.join([symbol, req.exchange])

                    # 针对IB接口，订阅行情需要货币和产品类型
                    if len(setting)>=5:
                        req.currency = setting[3]
                        req.productClass = setting[4]

                    self.mainEngine.subscribe(req, gateway)

                    #tick = VtTickData()           # 该tick实例可以用于缓存部分数据（目前未使用）
                    #self.tickDict[vtSymbol] = tick
                    self.tickSymbolSet.add(vtSymbol)
                    
                    # 保存到配置字典中
                    if vtSymbol not in self.settingDict:
                        d = {
                            'symbol': symbol,
                            'gateway': gateway,
                            'tick': True
                        }
                        self.settingDict[vtSymbol] = d
                    else:
                        d = self.settingDict[vtSymbol]
                        d['tick'] = True

            # 分钟线记录配置
            if 'bar' in drSetting:
                l = drSetting['bar']

                for setting in l:
                    symbol = setting[0]
                    gateway = setting[1]
                    vtSymbol = symbol

                    req = VtSubscribeReq()
                    req.symbol = symbol                    

                    if len(setting)>=3:
                        req.exchange = setting[2]
                        vtSymbol = '.'.join([symbol, req.exchange])

                    if len(setting)>=5:
                        req.currency = setting[3]
                        req.productClass = setting[4]                    

                    self.mainEngine.subscribe(req, gateway)  
                    
                    # 保存到配置字典中
                    if vtSymbol not in self.settingDict:
                        d = {
                            'symbol': symbol,
                            'gateway': gateway,
                            'bar': True
                        }
                        self.settingDict[vtSymbol] = d
                    else:
                        d = self.settingDict[vtSymbol]
                        d['bar'] = True     
                    
                    # 创建BarManager对象
                    self.bgDict[vtSymbol] = BarGenerator(self.onBar, onDayBar=self.onDayBar)

                    bm = self.bgDict[vtSymbol]
                    daysBack = self.marketHours.weekdayOffset[datetime.today().weekday()]
                    print("init for day bar from : ", daysBack, todayDate()-timedelta(daysBack))
                    initData = self.loadBar(MINUTE_DB_NAME, vtSymbol, daysBack)
                    bm.fillDayBarsWithMinute(initData)
                    if self.marketHours.isMarketDayFinished(vtSymbol) :
                        print("Try doing day bar finalize")
                        bm.finalizeDay()


    def loadBar(self, dbName, collectionName, days):
        """从数据库中读取Bar数据，startDate是datetime对象"""
        startDate = todayDate() - timedelta(days)
        
        d = {'datetime':{'$gte':startDate}}
        barData = self.mainEngine.dbQuery(dbName, collectionName, d, 'datetime')
        
        l = []
        for d in barData:
            bar = VtBarData()
            bar.__dict__ = d
            l.append(bar)
        return l

    #----------------------------------------------------------------------
    def getSetting(self):
        """获取配置"""
        return self.settingDict, self.activeSymbolDict

    #----------------------------------------------------------------------
    def processTickEvent(self, event):
        """处理行情事件"""
        tick = event.dict_['data']
        vtSymbol = tick.vtSymbol
        
        if self.marketHours.isMarketOpen(vtSymbol, tick.exchange, tick.time) :
            if tick.lastPrice <= 0. and self.lastTick.get(tick.vtSymbol, None) :
                tick.lastPrice = self.lastTick[tick.vtSymbol].lastPrice

            if tick.lastPrice > 0. :
                if not tick.datetime:
                    if '.' in tick.time:
                        tick.datetime = datetime.strptime(' '.join([tick.date, tick.time]), '%Y%m%d %H:%M:%S.%f')
                    else:
                        tick.datetime = datetime.strptime(' '.join([tick.date, tick.time]), '%Y%m%d %H:%M:%S')

                self.onTick(tick)
                
                bm = self.bgDict.get(vtSymbol, None)
                if bm:
                    bm.updateTick(tick)

                self.lastTick[tick.vtSymbol] = tick
            else :
                print("processTickEvent bad tick, ignored: ", tick.time, " ", tick.vtSymbol, " ", tick.lastPrice)
        else :
            print("processTickEvent off-hour, ignroed: ", tick.time, " ", tick.vtSymbol, " ", tick.lastPrice)

    
    #----------------------------------------------------------------------
    def processTimerEvent(self, event):
        """处理定时事件"""        
        # 30秒检查一次
        self.timerCount += 1
        if self.timerCount < 30:
            return
        self.timerCount = 0
        
        # 获取当前时间
        currentTime = datetime.now().time()
        
        if not self.lastTimerTime:
            self.lastTimerTime = currentTime
            return

        # print("TimeEvent: ", currentTime)
        for vtSymbol in self.bgDict :
            if (self.marketHours.isMarketOpen(vtSymbol, curTime=currentTime) and 
                (not self.marketHours.isAtSessionOpen(vtSymbol, curTime=currentTime))) :
                self._isMinBarUpdate(vtSymbol, currentTime.replace(second=0, microsecond=0))

            elif (self.marketHours.isMarketJustClose(vtSymbol, curTime=self.lastTimerTime) and 
                (not self.marketHours.isMarketJustClose(vtSymbol, curTime=currentTime))) :
                bg = self.bgDict.get(vtSymbol, None)
                print(vtSymbol, currentTime, "force finish day ")
                bg.finalizeDay()
                
            elif (self.marketHours.isSessionJustClose(vtSymbol, curTime=self.lastTimerTime) and 
                (not self.marketHours.isSessionJustClose(vtSymbol, curTime=currentTime))) :
                bg = self.bgDict.get(vtSymbol, None)
                print(vtSymbol, currentTime, "force finish session ")
                bg.generate()

        # 记录新的时间
        self.lastTimerTime = currentTime

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick更新"""
        vtSymbol = tick.vtSymbol
        
        if vtSymbol in self.tickSymbolSet :
            self.insertData(TICK_DB_NAME, vtSymbol, tick)
            
            if vtSymbol in self.activeSymbolDict:
                activeSymbol = self.activeSymbolDict[vtSymbol]
                self.insertData(TICK_DB_NAME, activeSymbol, tick)
            
            
            self.writeDrLog(text.TICK_LOGGING_MESSAGE.format(symbol=tick.vtSymbol,
                                                            time=tick.time, 
                                                            last=tick.lastPrice, 
                                                            bid=tick.bidPrice1, 
                                                            ask=tick.askPrice1))
                                                                    
    
    def _isMinBarInSeccession(self, vtSymbol, bTime) :
        bm = self.bgDict.get(vtSymbol, None)
        lastBar = bm.getLastMinuteBar()
        if not lastBar :
            print("First bar in BarsManager", bTime)
            return True
        lastBarTime = lastBar.datetime

        if (self.marketHours.isAtSessionOpen(vtSymbol, curTime=bTime.time()) and 
            self.marketHours.isSessionClosingBar(vtSymbol, barTime=lastBarTime.time())) :
            return True

        if bTime == lastBarTime + timedelta(minutes=1) :
            return True

        print("Recording minute bars not in seccession: ", vtSymbol, lastBarTime, bTime)
        return False


    def _isMinBarUpdate(self, vtSymbol, cTime) :
        bm = self.bgDict.get(vtSymbol, None)
        lastBar = bm.getLastMinuteBar()
        if not lastBar :
            print("Last bar missing in BarsManager ", vtSymbol, str(cTime))
            return True

        lastBarTime = lastBar.datetime

        if cTime == (lastBarTime + timedelta(minutes=1)).time() :
            return True

        print("** minute bars missing: ", vtSymbol, str(lastBarTime), str(cTime))
        return False

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """分钟线更新"""
        vtSymbol = bar.vtSymbol

        # print("lkDrEngine onBar ", vtSymbol, bar.time)
        self._isMinBarInSeccession(vtSymbol, bar.datetime)
        self.insertData(MINUTE_DB_NAME, vtSymbol, bar)

        if vtSymbol in self.activeSymbolDict:
            activeSymbol = self.activeSymbolDict[vtSymbol]
            self.insertData(MINUTE_DB_NAME, activeSymbol, bar)                    
        
        self.writeDrLog(text.BAR_LOGGING_MESSAGE.format(symbol=bar.vtSymbol, 
                                                        time=bar.time, 
                                                        open=bar.open, 
                                                        high=bar.high, 
                                                        low=bar.low, 
                                                        close=bar.close))        

    # update DB may be expensive, stay with insertData
    def onBar1(self, bar):
        """分钟线更新"""
        vtSymbol = bar.vtSymbol

        self._isMinBarInSeccession(vtSymbol, bar.datetime)

        flt = {'datetime': bar.datetime}
        l = self.mainEngine.dbQuery(MINUTE_DB_NAME, vtSymbol, flt)
        if l :
            print("onDayBar updating bar: ", l)
        self.mainEngine.dbUpdate(MINUTE_DB_NAME, vtSymbol, bar.__dict__, flt, True)

        if vtSymbol in self.activeSymbolDict:
            activeSymbol = self.activeSymbolDict[vtSymbol]
            self.mainEngine.dbUpdate(MINUTE_DB_NAME, activeSymbol, bar.__dict__, flt, True)
        
        self.writeDrLog(text.BAR_LOGGING_MESSAGE.format(symbol=bar.vtSymbol, 
                                                        time=bar.time, 
                                                        open=bar.open, 
                                                        high=bar.high, 
                                                        low=bar.low, 
                                                        close=bar.close))        

    def onDayBar(self, bar):
        """分钟线更新"""
        vtSymbol = bar.vtSymbol
        
        flt = {'date': bar.date}
        l = self.mainEngine.dbQuery(DAILY_DB_NAME, vtSymbol, flt)
        if l :
            print("onDayBar updating bar: ", l)
        self.mainEngine.dbUpdate(DAILY_DB_NAME, vtSymbol, bar.__dict__, flt, True)
        
        if vtSymbol in self.activeSymbolDict:
            activeSymbol = self.activeSymbolDict[vtSymbol]
            self.mainEngine.dbUpdate(DAILY_DB_NAME, activeSymbol, bar.__dict__, flt, True)
        
        self.writeDrLog(text.BAR_LOGGING_MESSAGE.format(symbol=bar.vtSymbol, 
                                                        time=bar.time, 
                                                        open=bar.open, 
                                                        high=bar.high, 
                                                        low=bar.low, 
                                                        close=bar.close))        

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.processTickEvent)
        self.eventEngine.register(EVENT_TIMER, self.processTimerEvent)
 
    #----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """插入数据到数据库（这里的data可以是VtTickData或者VtBarData）"""
        self.queue.put((dbName, collectionName, data.__dict__))
        
    #----------------------------------------------------------------------
    def run(self):
        """运行插入线程"""
        while self.active:
            try:
                dbName, collectionName, d = self.queue.get(block=True, timeout=1)
                
                # 这里采用MongoDB的update模式更新数据，在记录tick数据时会由于查询
                # 过于频繁，导致CPU占用和硬盘读写过高后系统卡死，因此不建议使用
                #flt = {'datetime': d['datetime']}
                #self.mainEngine.dbUpdate(dbName, collectionName, d, flt, True)
                
                # 使用insert模式更新数据，可能存在时间戳重复的情况，需要用户自行清洗
                try:
                    self.mainEngine.dbInsert(dbName, collectionName, d)
                except DuplicateKeyError:
                    self.writeDrLog(u'键值重复插入失败，报错信息：%s' %traceback.format_exc())
            except Empty:
                pass
            
    #----------------------------------------------------------------------
    def start(self):
        """启动"""
        self.active = True
        self.thread.start()
        
    #----------------------------------------------------------------------
    def stop(self):
        """退出"""
        if self.active:
            self.active = False
            self.thread.join()
        
    #----------------------------------------------------------------------
    def writeDrLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_DATARECORDER_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)   
    