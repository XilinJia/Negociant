'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

# encoding: utf-8

'''
本文件包含了CTA引擎中的策略开发用模板，开发策略时需要继承CtaTemplate类。
'''

from datetime import datetime, timedelta, time
import numpy as np
import math

from negociant.trader.vtObject import VtBarData
from negociant.trader.vtFunction import getTempPath
from negociant.trader.vtConstant import *
from negociant.trader.lkTrades import TradeRecord
from negociant.trader.markets.lkMarketHours import MarketsOpHours
from negociant.trader.lkBarsEngine import BarGenerator

from .lkTechnicals import Technicals
from .ctaArrayManager import ArrayManager
from .ctaBase import *


########################################################################
class LKCtaTemplate(object):
    """CTA策略模板"""
    
    # 策略类的名称和作者
    className = 'LKCtaTemplate'
    author = 'XJia'
    
    # MongoDB数据库的名称，K线数据库默认为1分钟
    tickDbName = TICK_DB_NAME
    barDbName = MINUTE_DB_NAME
    
    # 策略的基本参数
    name = EMPTY_UNICODE           # 策略实例名称
    vtSymbol = EMPTY_STRING        # 交易的合约vt系统代码    
    hotSymbol = EMPTY_STRING
    productClass = EMPTY_STRING    # 产品类型（只有IB接口需要）
    currency = EMPTY_STRING        # 货币（只有IB接口需要）
    
    # 策略的基本变量，由引擎管理
    inited = False                 # 是否进行了初始化
    trading = False                # 是否启动交易，由引擎管理
    pos = 0                        # 持仓情况
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'useCapital',
                 'vtSymbol',
                 'hotSymbol',
                 'useCapital',
                 'contractSize',
                 'margin']
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine
        # print(ctaEngine, " ", setting)

        # self.barGen = BarGenerator(self.onBar)
        self.barGen = BarGenerator()

        # load market hours to be used as time filters
        self.marketHours = MarketsOpHours()

        self.useCapital = 100000.
        self.margin = 1.
        self.contractSize = 1

        # 设置策略的参数
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
                    print("read CTA_Setting: ", key, setting[key])

            if "useCapital" in d :
                self.useCapital = float(d["useCapital"])
            if "margin" in d :
                self.margin = float(d["margin"])
            if "contractSize" in d :
                self.contractSize = int(d["contractSize"])
            if 'hotSymbol' in d :
                self.hotSymbol = d['hotSymbol']

        self.effCapital = self.useCapital / self.contractSize / self.margin

        self.tradeRec = TradeRecord(self.vtSymbol)

        logFilePath = getTempPath(self.name + '-' + self.vtSymbol + '-' + str(datetime.today().date()) + '.log')
        self.logFile = open(logFilePath, 'a')

        # print(self.name, ' Capital: ', self.useCapital, self.vtSymbol, self.hotSymbol, ' contractSize: ', 
        #         self.contractSize, ' margin: ', self.margin, ' effCapital: ', int(self.effCapital))     

        self.logFile.write(self.name + ' Capital: ' + str(self.useCapital) + ' ' + self.vtSymbol + ' ' + self.hotSymbol + 
                ' contractSize: ' + str(self.contractSize) + ' margin: ' + str(self.margin) + ' effCapital: ' + 
                str(int(self.effCapital)) + '\n')
    
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        raise NotImplementedError

    def getLots(self, price):
        return int(self.effCapital / price)

    def getLotsPermission(self, price, newLots, dumpLots) :
        """ 
        this function is only for single strategy, not appropriate for portfolio. 
        class LKSCC implemented a finer one 
        """
        affordLots = int(self.effCapital / price)
        availLots = affordLots - abs(self.pos) + dumpLots
        if self.pos == 0 or newLots != math.copysign(newLots, self.pos) :
            return min(abs(newLots), affordLots)
        # print(self.vtSymbol, "affordLots: ", affordLots, " curLots: ", abs(self.pos), " dumpLots: ", dumpLots, " availLots: ", availLots)
        return min(abs(newLots), availLots)

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """收到停止单推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    def goLong(self, price) :
        lots = self.getLots(price)
        self.logFile.write("Going long " + self.vtSymbol + " lots:" + str(lots) + " " + str(self.pos) + " at price: " + 
            str(price) + '\n')
        if self.pos < 0:
            self.cover(price, abs(self.pos))
        if lots>0 :
            self.buy(price, lots)
            

    def goShort(self, price) :
        lots = self.getLots(price)
        self.logFile.write("Going short " + self.vtSymbol + " lots:" + str(lots) + " " + str(self.pos) + " at price: " + 
            str(price) + '\n')
        if self.pos > 0:
            self.sell(price, self.pos)
        if lots>0 :
            self.short(price, lots)


    #----------------------------------------------------------------------
    def buy(self, price, volume, stop=False):
        """买开"""
        return self.sendOrder(CTAORDER_BUY, price, volume, stop)
    
    #----------------------------------------------------------------------
    def sell(self, price, volume, stop=False):
        """卖平"""
        return self.sendOrder(CTAORDER_SELL, price, volume, stop)       

    #----------------------------------------------------------------------
    def short(self, price, volume, stop=False):
        """卖开"""
        return self.sendOrder(CTAORDER_SHORT, price, volume, stop)          
 
    #----------------------------------------------------------------------
    def cover(self, price, volume, stop=False):
        """买平"""
        return self.sendOrder(CTAORDER_COVER, price, volume, stop)
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderType, price, volume, stop=False):
        """发送委托"""
        if self.trading and self.marketHours.isMarketOpen(self.vtSymbol) :
            # 如果stop为True，则意味着发本地停止单
            if stop:
                vtOrderIDList = self.ctaEngine.sendStopOrder(self.vtSymbol, orderType, price, volume, self)
            else:
                vtOrderIDList = self.ctaEngine.sendOrder(self.vtSymbol, orderType, price, volume, self) 
            return vtOrderIDList
        else:
            # 交易停止时发单返回空字符串
            return []
        
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        # 如果发单号为空字符串，则不进行后续操作
        if not vtOrderID:
            return
        
        if STOPORDERPREFIX in vtOrderID:
            self.ctaEngine.cancelStopOrder(vtOrderID)
        else:
            self.ctaEngine.cancelOrder(vtOrderID)
            
    #----------------------------------------------------------------------
    def cancelAll(self):
        """全部撤单"""
        self.ctaEngine.cancelAll(self.name)
    
    #----------------------------------------------------------------------
    def insertTick(self, tick):
        """向数据库中插入tick数据"""
        self.ctaEngine.insertData(self.tickDbName, self.vtSymbol, tick)
    
    #----------------------------------------------------------------------
    def insertBar(self, bar):
        """向数据库中插入bar数据"""
        self.ctaEngine.insertData(self.barDbName, self.vtSymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days):
        """读取tick数据"""
        return self.ctaEngine.loadTick(self.tickDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def loadBar(self, days):
        """读取bar数据"""
        return self.ctaEngine.loadBar(self.barDbName, self.hotSymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录CTA日志"""
        content = self.name + ':' + content
        self.ctaEngine.writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def putEvent(self):
        """发出策略状态变化事件"""
        self.ctaEngine.putStrategyEvent(self.name)
        
    #----------------------------------------------------------------------
    def getEngineType(self):
        """查询当前运行的环境"""
        return self.ctaEngine.engineType
    
    #----------------------------------------------------------------------
    def saveSyncData(self):
        """保存同步数据到数据库"""
        if self.trading:
            self.ctaEngine.saveSyncData(self)
    
    #----------------------------------------------------------------------
    def getPriceTick(self):
        """查询最小价格变动"""
        return self.ctaEngine.getPriceTick(self)
        


########################################################################
class LKTargetPos(LKCtaTemplate):
    """
    允许直接通过修改目标持仓来实现交易的策略模板
    
    开发策略时，无需再调用buy/sell/cover/short这些具体的委托指令，
    只需在策略逻辑运行完成后调用setTargetPos设置目标持仓，底层算法
    会自动完成相关交易，适合不擅长管理交易挂撤单细节的用户。    
    
    使用该模板开发策略时，请在以下回调方法中先调用母类的方法：
    onTick
    onBar
    onOrder
    
    假设策略名为TestStrategy，请在onTick回调中加上：
    super(TestStrategy, self).onTick(tick)
    
    其他方法类同。
    """
    
    className = 'LKTargetPos'
    author = 'XJia'
    
    # 目标持仓模板的基本变量
    tickAdd = 1             # 委托时相对基准价格的超价
    lastTick = None         # 最新tick数据
    lastBar = None          # 最新bar数据
    targetPos = EMPTY_INT   # 目标持仓
    orderList = []          # 委托号列表

    # 变量列表，保存了变量的名称
    varList = LKCtaTemplate.varList + ['targetPos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(LKTargetPos, self).__init__(ctaEngine, setting)
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情推送"""
        self.lastTick = tick
        
        # 实盘模式下，启动交易后，需要根据tick的实时推送执行自动开平仓操作
        # if self.trading:
        #     self.trade()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到K线推送"""
        self.lastBar = bar
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托推送"""
        if order.status == STATUS_ALLTRADED or order.status == STATUS_CANCELLED:
            if order.vtOrderID in self.orderList:
                self.orderList.remove(order.vtOrderID)
    
    #----------------------------------------------------------------------
    def setTargetPos(self, targetPos):
        """设置目标仓位"""
        self.targetPos = targetPos
        
        self.trade()

    #----------------------------------------------------------------------
    def trade(self):
        """执行交易"""
        # 先撤销之前的委托
        self.cancelAll()
        
        # 如果目标仓位和实际仓位一致，则不进行任何操作
        posChange = self.targetPos - self.pos
        # print("posChange: ", self.vtSymbol, posChange, self.pos, self.targetPos)
        if not posChange:
            return
        
        # 确定委托基准价格，有tick数据时优先使用，否则使用bar
        longPrice = 0
        shortPrice = 0
        
        if self.lastTick:
            if posChange > 0:
                longPrice = self.lastTick.askPrice1 + self.tickAdd
                if self.lastTick.upperLimit:
                    longPrice = min(longPrice, self.lastTick.upperLimit)         # 涨停价检查
            else:
                shortPrice = self.lastTick.bidPrice1 - self.tickAdd
                if self.lastTick.lowerLimit:
                    shortPrice = max(shortPrice, self.lastTick.lowerLimit)       # 跌停价检查
        else:
            if posChange > 0:
                longPrice = self.lastBar.close + self.tickAdd
            else:
                shortPrice = self.lastBar.close - self.tickAdd
        
        # 回测模式下，采用合并平仓和反向开仓委托的方式
        if self.getEngineType() == ENGINETYPE_BACKTESTING:
            if posChange > 0:
                l = self.buy(longPrice, abs(posChange))
            else:
                l = self.short(shortPrice, abs(posChange))
            self.orderList.extend(l)
        
        # 实盘模式下，首先确保之前的委托都已经结束（全成、撤销）
        # 然后先发平仓委托，等待成交后，再发送新的开仓委托
        else:
            # 检查之前委托都已结束
            if self.orderList:
                return
            
            # 买入
            if posChange > 0:
                # 若当前有空头持仓
                if self.pos < 0:
                    # 若买入量小于空头持仓，则直接平空买入量
                    if posChange < abs(self.pos):
                        l = self.cover(longPrice, posChange)
                    # 否则先平所有的空头仓位
                    else:
                        l = self.cover(longPrice, abs(self.pos))
                # 若没有空头持仓，则执行开仓操作
                else:
                    l = self.buy(longPrice, abs(posChange))
            # 卖出和以上相反
            else:
                if self.pos > 0:
                    if abs(posChange) < self.pos:
                        l = self.sell(shortPrice, abs(posChange))
                    else:
                        l = self.sell(shortPrice, abs(self.pos))
                else:
                    l = self.short(shortPrice, abs(posChange))
            self.orderList.extend(l)    


class LKSCC(LKTargetPos):
    className = 'LKSCC'
    author = 'XJia'

    # 策略参数
    initDays = 200           # 初始化数据所用的天数

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(LKSCC, self).__init__(ctaEngine, setting)
        self.doneInit = False

        techLogPath = getTempPath(self.name + '-' + self.vtSymbol + '-' + str(datetime.today().date()) + '.csv')
        self.techLog = open(techLogPath, 'a')

        self.barGen.requireMinBar(self.onBar)
        self.barGen.requireDayBar(self.onDayBar)
        self.tech = Technicals(size=40)        

        self.signals = []
        # subclass needs to populate self.signals

                
    def setSignalCapitals(self, boostR=1.) :
        capitalAlloc = self.effCapital / len(self.signals) * boostR
        for i in range(len(self.signals)) :
            self.signals[i].setCapital(capitalAlloc)


    def getLotsPermission(self, price, newLots, dumpLots) :
        affordLots = int(self.effCapital / price)
        availLots = affordLots - abs(self.pos) + dumpLots
        if self.pos == 0 or newLots != math.copysign(newLots, self.pos) :
            return min(abs(newLots), affordLots)

        # print(self.vtSymbol, "affordLots: ", affordLots, " curLots: ", abs(self.pos), " dumpLots: ", dumpLots, " availLots: ", availLots)
        if availLots < abs(newLots) :
            print("availLots not enough for newLots: ", newLots, affordLots, self.pos, dumpLots, availLots, " reallocating")
            effStrats = 0
            for i in range(len(self.signals)) :
                lotsi = self.signals[i].getSignalPos()
                if lotsi != 0 and lotsi == math.copysign(lotsi, self.pos) :
                    effStrats += 1
            lotsRealloc = int(affordLots / (effStrats+1))
            for i in range(len(self.signals)) :
                lotsi = self.signals[i].getSignalPos()
                if lotsi != 0 :
                    self.signals[i].setSignalPos(math.copysign(lotsRealloc, lotsi), price)
                # print("Reset signal position: ", self.vtSymbol, self.signals[i].name, 
                #     str(datetime.now().replace(second=0, microsecond=0)), lotsi, self.signals[i].getSignalPos())
                self.logFile.write("Reset signal position: " + self.vtSymbol + ' ' + self.signals[i].name + ' ' +
                    str(datetime.now().replace(second=0, microsecond=0)) + ' ' + str(lotsi) + ' ' + 
                    str(self.signals[i].getSignalPos()) + '\n')
            
            return lotsRealloc
            
        return min(abs(newLots), availLots)

    #----------------------------------------------------------------------
    def onInit(self):
        self.writeCtaLog(u'%s策略初始化' %self.name)

        for tech in self.tech.memList :
            self.techLog.write(tech + ',')
        self.techLog.write('\n')       

        self.doneInit = True
        initDayData = self.ctaEngine.loadBar(DAILY_DB_NAME, self.hotSymbol, self.initDays)
        self.barGen.fillDayBars(initDayData)

        startTime = datetime.today().replace(hour=20, minute=58)
        todayDate = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        if datetime.now().time() < time(15,0) :     # TODO if in day session, load previous day
            daysBack = self.marketHours.weekdayOffset[datetime.today().weekday()]
            startTime = (todayDate-timedelta(daysBack)).replace(hour=20, minute=58)
            # print("init for day bar from : ", daysBack, startTime)
            self.logFile.write("init for day bar from : " + str(daysBack) + str(startTime) )
        elif datetime.now().time() > time(15, 30) :  # TODO if in night session, load just the current night session
            startTime = datetime.today().replace(hour=20, minute=58)
            # print("init for day bar from : ", startTime)
            self.logFile.write("init for day bar from : " + str(startTime) + '\n')

        initData = []
        d = {'datetime':{'$gte':startTime}}
        barData = self.ctaEngine.mainEngine.dbQuery(MINUTE_DB_NAME, self.vtSymbol, d, 'datetime')
        for d in barData:
            bar = VtBarData()
            bar.__dict__ = d
            initData.append(bar)
        numMinBars = 0    
        startFilling =  False
        for bar in initData :
            if (not startFilling) and bar.datetime.replace(second=0, microsecond=0).time()>time(15, 5) :
                startFilling =  True
            if startFilling :
                numMinBars += 1
                self.barGen.updateWithMinuteBar(bar)
        self.logFile.write("finished filling day bar with minutes: " + str(numMinBars) + '\n')
        self.logFile.write("daybar array " + str(self.tech.dt[-1]) + ' ' + str(self.tech.dt[-2]) + '\n')   
        self.logFile.write("Combined position: " + str(self.pos) + '\n')
        for i in range(len(self.signals)) :
            self.logFile.write("onInit individual positions: " + self.vtSymbol + ' ' + self.signals[i].name + ' ' +
                str(self.signals[i].getSignalPos()) + '\n')

        self.barGen.setDayBarResample(True)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        super(LKSCC, self).onTick(tick)
        self.barGen.updateTick(tick)
                
        if self.doneInit :
            self.calculateTargetPos()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):   
        super(LKSCC, self).onBar(bar)

        if not self.tech.inited:
            return
        if bar.time == '' :
            self.logFile.write("**Wrong bar time" + str(bar) + '\n')
            return

        self.tech.updateCurBar(bar)
        # print("onBar: ", bar.time[0:7], self.vtSymbol, 
        #     self.tech.op[-1], self.tech.hi[-1], self.tech.lo[-1], bar.close, ' [-2] ', 
        #     self.tech.op[-2], self.tech.hi[-2], self.tech.lo[-2], self.tech.cl[-2], + '\n') 

        for tech in self.tech.memList :
            techStr = str(self.tech.memList[tech][-1])
            if type(self.tech.memList[tech][-1]) == np.float64 :
                techStr = str(round(self.tech.memList[tech][-1], 4))
            self.techLog.write(techStr + ',')
        self.techLog.write('\n')
        self.techLog.flush()

        barTime = bar.datetime.time()
        if barTime > time(14, 57) and barTime < time(15, 1):
            for i in range(len(self.signals)) :
                self.signals[i].onBar(bar)

        # for i in range(len(self.signals)) :
        #     print("onBar ", bar.time, self.vtSymbol, bar.close, self.signals[i].name, self.signals[i].getSignalPos(),
        #         self.signals[i].dailyReturn, self.signals[i].cumReturn, '\n')

        self.logFile.flush()
        if self.doneInit :
            self.calculateTargetPos()
        
    def onBacktestBar(self, bar) :
        """ same as onBar but for backtests """
        super(LKSCC, self).onBar(bar)
        self.barGen.updateWithMinuteBar(bar)
        self.tech.updateCurBar(bar)
        for i in range(len(self.signals)) :
            self.signals[i].onBar()

        self.calculateTargetPos()

    def onDayBar(self, bar) :

        self.tech.setCurBar(bar)  
        self.logFile.write("onDayBar: " + str(bar.date) + ' ' + str(bar.time[0:7]) + ' ' + self.vtSymbol + ' ' +
            str(self.tech.op[-1]) + ' ' + str(self.tech.hi[-1]) + ' ' + str(self.tech.lo[-1]) + ' ' + str(bar.close) + ' [-2] ' + 
            str(self.tech.op[-2]) + ' ' + str(self.tech.hi[-2]) + ' ' + str(self.tech.lo[-2]) + ' ' + str(self.tech.cl[-2]) + '\n') 
        self.logFile.flush()
        for i in range(-1, 0) :
            for tech in self.tech.memList :
                techStr = str(self.tech.memList[tech][i])
                # print(tech, type(self.tech.memList[tech][i]))
                if type(self.tech.memList[tech][i]) == np.float64 :
                    techStr = str(round(self.tech.memList[tech][i], 4))
                self.techLog.write(techStr + ',')
            self.techLog.write('\n')
        self.techLog.flush()

        if self.tech.inited:
            for i in range(len(self.signals)) :
                self.signals[i].onDayBar(bar)
                # print("onDayBar ", self.vtSymbol, self.signals[i].name, self.signals[i].getSignalPos(), '\n')
        # print("before allocNewBar: " + str(self.tech.dt[-1]) + ' ' + str(self.tech.dt[-2]) + ' ' + 
        #     str(self.tech.cl[-1]) + ' ' + str(self.tech.cl[-2]))
        self.tech.allocNewBar()

    def recPosChange(self, price) :
        # for i in range(len(self.signals)) :
        #     print("recPosCh ", self.vtSymbol, self.signals[i].name, datetime.now().replace(second=0, microsecond=0),
        #         self.signals[i].getSignalPos(), price, self.tech.cl[-2], '\n')
        pass

    #----------------------------------------------------------------------
    def calculateTargetPos(self):
        targetPos = 0
        for i in range(len(self.signals)) :
            targetPos += self.signals[i].getSignalPos()
        
        self.setTargetPos(targetPos)
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        super(LKSCC, self).onOrder(order)
        # for i in range(len(self.signals)) :
        #     print("onOrder ", self.vtSymbol, self.signals[i].name, self.signals[i].getSignalPos(), '\n')

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        for i in range(len(self.signals)) :
            self.logFile.write("onTrade " + self.vtSymbol + self.signals[i].name + ' ' + str(self.signals[i].getSignalPos()) + '\n')
        self.logFile.flush()
       
        self.putEvent()

########################################################################
class LKCtaSignal(object):
    """
    CTA策略信号，负责纯粹的信号生成（目标仓位），不参与具体交易管理
    """

    name = EMPTY_UNICODE           # 策略实例名称

    #----------------------------------------------------------------------
    def __init__(self, boss, effCapital=0.):
        """Constructor"""
        self.boss = boss
        self.barGen = boss.barGen
        self.vtSymbol = boss.vtSymbol
        self.tradeRec = TradeRecord(self.vtSymbol)
        self.effCapital = effCapital
        self.logFile = boss.logFile
        self.lastPos = 0
        self.signalPos = 0      # 信号仓位

        self.dailyReturn = 0.
        self.histDReturn = []
        self.cumReturn = 0.
    
    def getLots(self, price, ls) :
        tentLots = int(self.effCapital / price)
        return self.boss.getLotsPermission(price, ls*tentLots, abs(self.signalPos))

    def setCapital(self, effCapital) :
        self.effCapital = effCapital

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线推送"""
        pass
    
    #----------------------------------------------------------------------
    def onDayBar(self, bar):
        self.histDReturn.append(self.dailyReturn)
        self.cumReturn += self.dailyReturn
        self.logFile.write("dailyReturn: " +  str(bar.datetime.date()) + ' ' + self.name + ' ' + self.vtSymbol + ' ' + 
            str(self.signalPos) + ' ' + str(self.dailyReturn) + ' ' + str(self.cumReturn) + '\n')
        self.dailyReturn = 0.

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick推送"""
        pass
        
    #----------------------------------------------------------------------
    def setSignalPos(self, pos, price):
        """设置信号仓位"""
        self.signalPos = pos
        if self.signalPos != self.lastPos :
            self.boss.recPosChange(price)
            self.lastPos = self.signalPos
        
    #----------------------------------------------------------------------
    def getSignalPos(self):
        """获取信号仓位"""
        return self.signalPos
        
        
class SCCSignal(LKCtaSignal):
    """ day signal """
    
    #----------------------------------------------------------------------
    def __init__(self, boss, effCapital=0.):
        """Constructor"""
        super(SCCSignal, self).__init__(boss, effCapital)
        self.ls = 1
        self.tech = boss.tech
        self.entryExitDay = 0
        self.entryPrice = 0.
        self.numEntrydays = 0  

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线更新"""

        self.logFile.write("SCCSignal onBar: " + str(bar.time[0:7]) + ' ' + self.name + ' ' + self.vtSymbol + ' ' + str(self.signalPos) + '\n') 
        self.updatePos()

    def _doNikaas(self) :
        self.dailyReturn = self.signalPos * (self.tech.cl[-1] - self.tech.cl[-2])

        tradeReturn = self.signalPos * (self.tech.cl[-1] - self.entryPrice)
        self.logFile.write("Nikaas: " +  ' ' + self.name + ' ' + self.vtSymbol + ' ' + 
            str(self.signalPos) + ' ' + str(tradeReturn) + '\n')
            
        self.setSignalPos(0, self.tech.cl[-1])
        self.entryExitDay = -1
        self.numEntrydays = 0 
        self.entryPrice = 0.

    def _doPravesh(self) :
        lots = self.getLots(self.tech.cl[-1], self.ls)
        self.setSignalPos(self.ls * lots, self.tech.cl[-1])
        self.entryExitDay = 1
        self.numEntrydays = 0 
        self.entryPrice = self.tech.cl[-1]

    def updatePos(self) :
        if self.signalPos != 0 and self.nikaas() :
            self._doNikaas()

        if self.signalPos == 0 and self.pravesh() :
            self._doPravesh()


    def pravesh(self) :
        pass
        
    def nikaas(self) :
        pass

    #----------------------------------------------------------------------
    def onDayBar(self, bar):
        """dayK线更新"""
        self.updatePos()
        # self.boss.logFile.write("SCCSignal onDayBar: ", self.vtSymbol, self.signalPos, self.tech.dt[-1], self.tech.dt[-2], '\n')
        if self.entryExitDay == 0 :
            self.dailyReturn = self.signalPos * (self.tech.cl[-1] - self.tech.cl[-2])
        self.entryExitDay = 0

        if self.signalPos != 0 :
            self.numEntrydays += 1
        
        super(SCCSignal, self).onDayBar(bar)


class SCCNSignal(SCCSignal) :

    #----------------------------------------------------------------------
    def __init__(self, nDays, boss, effCapital=0.):
        """Constructor"""
        super(SCCNSignal, self).__init__(boss, effCapital)
        self.nDays = nDays

    def updatePos(self) :
        if self.signalPos != 0 and (self.numEntrydays>=self.nDays or self.nikaas()) :
            self._doNikaas()

        if self.signalPos == 0 and self.pravesh() :
            self._doPravesh()
