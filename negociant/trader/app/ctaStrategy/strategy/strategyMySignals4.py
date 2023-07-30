'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

# encoding: UTF-8

"""
一个多信号组合策略，基于的信号包括：
RSI（1分钟）：大于70为多头、低于30为空头
CCI（1分钟）：大于10为多头、低于-10为空头
MA（5分钟）：快速大于慢速为多头、低于慢速为空头
"""

from datetime import datetime, time

from negociant.trader.vtObject import VtBarData
from negociant.trader.vtConstant import EMPTY_STRING
from negociant.trader.app.ctaStrategy.lkCtaTemplate import LKTargetPos, LKCtaSignal, SCCSignal
from negociant.trader.lkBarsEngine import BarGenerator
from negociant.trader.app.ctaStrategy.ctaArrayManager import ArrayManager
from negociant.trader.app.ctaStrategy.ctaBase import DAILY_DB_NAME

from .SCC.PortSCC import SCC1, SCC2

########################################################################
class RsiSignal(LKCtaSignal):
    """RSI信号"""

    #----------------------------------------------------------------------
    def __init__(self, boss, effCapital=0.):
        """Constructor"""
        super(RsiSignal, self).__init__(boss, effCapital)
        self.name = "Rsi"

        self.rsiWindow = 14
        self.rsiLevel = 20
        self.rsiLong = 50 + self.rsiLevel
        self.rsiShort = 50 - self.rsiLevel

        self.am = ArrayManager()
        self.barGen.requireMinBar(self.am.updateBar)
        self.barGen.requireDayBar(self.onDayBar)

        self.barGen.requireMinBar(self.onBar)
                
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线更新"""
        
        if not self.am.inited:
            self.setSignalPos(0, bar.close)
            
        self.dailyReturn += self.signalPos * (self.am.close[-1] - self.am.close[-2])

        # print("onBar: ", bar.time, self.name, self.vtSymbol, " ", bar.close)
        rsiValue = self.am.rsi(self.rsiWindow)
        
        if rsiValue > self.rsiLong:
            lots = self.getLots(bar.close)
            # print(self.name, " lots: ", lots)
            self.setSignalPos(lots, bar.close)
        elif rsiValue < self.rsiShort:
            lots = self.getLots(bar.close)
            self.setSignalPos(-lots, bar.close)
        else:
            self.setSignalPos(0, bar.close)
    

########################################################################
class SMASignal(LKCtaSignal):
    """双均线信号"""
    
    #----------------------------------------------------------------------
    def __init__(self, boss, effCapital=0.):
        """Constructor"""
        super(SMASignal, self).__init__(boss, effCapital)
        self.name = "SMA10-60"
        
        self.fastWindow = 10
        self.slowWindow = 60
        
        self.am = ArrayManager()
        self.barGen.requireMinBar(self.am.updateBar)
        self.barGen.requireMinBar(self.onBar)
        self.barGen.requireDayBar(self.onDayBar)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线更新"""

        self.dailyReturn += self.signalPos * (self.am.close[-1] - self.am.close[-2])

        # 计算快慢均线
        # print("onBar: ", bar.time, self.name, self.vtSymbol, " ", bar.close)
        fastMa = self.am.sma(self.fastWindow, array=True)        
        slowMa = self.am.sma(self.slowWindow, array=True)

        # 金叉和死叉的条件是互斥
        # 所有的委托均以K线收盘价委托（这里有一个实盘中无法成交的风险，考虑添加对模拟市价单类型的支持）
        if fastMa[-1] >= slowMa[-1] :
            lots = self.getLots(bar.close)
            self.setSignalPos(lots, bar.close)
        # 死叉和金叉相反
        elif fastMa[-1] < slowMa[-1]:
            lots = self.getLots(bar.close)
            self.setSignalPos(-lots, bar.close)
                  

########################################################################
class MySignals4Strategy(LKTargetPos):
    """跨时间周期交易策略"""
    className = 'MySignals4Strategy'
    author = 'XJia'

    # 策略参数
    initDays = 10           # 初始化数据所用的天数

    # 变量列表，保存了变量的名称
    varList = LKTargetPos.varList

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(MySignals4Strategy, self).__init__(ctaEngine, setting)

        self.barGen.requireMinBar(self.onBar)

        self.signals = []

        self.signals.append(RsiSignal(self))
        self.signals.append(SMASignal(self))
        self.signals.append(SCC1(self))
        self.signals.append(SCC2(self))

        capitalAlloc = self.effCapital / len(self.signals) * 1.2
        # print("__init__ cap: ", capitalAlloc, " ", len(self.signals))
        for i in range(len(self.signals)) :
            self.signals[i].setCapital(capitalAlloc)
            # print(self.signals[i].name, " Cap: ", self.signals[i].effCapital)

        # self.barGen.requireMinBar(self.onBar)
                
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog('%s策略初始化' %self.name)

        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        self.barGen.fillMinuteBars(initData, True)

        initData = self.ctaEngine.loadBar(DAILY_DB_NAME, self.hotSymbol, self.initDays)
        self.barGen.fillDayBars(initData)

        self.barGen.setDayBarResample(True)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog('%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog('%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        super(MySignals4Strategy, self).onTick(tick)
        self.barGen.updateTick(tick)
        
        # print("onTick: ", self.vtSymbol, " ", len(self.signals))
        # for i in range(len(self.signals)) :
        #     self.signals[i].onTick(tick)
        
        self.calculateTargetPos()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):   
        """收到Bar推送（必须由用户继承实现）"""
        super(MySignals4Strategy, self).onBar(bar)
        # self.barGen.updateBar(bar)
        # print(bar.datetime)
        # self.barGen.updateWithMinuteBar(bar)
        # print("Main onBar: ", bar.time, self.vtSymbol, " ", bar.close)
        # for i in range(len(self.signals)) :
        #     print("onBar ", bar.time, self.vtSymbol, bar.close, self.signals[i].name, self.signals[i].getSignalPos(),
        #         self.signals[i].dailyReturn, self.signals[i].cumReturn)

        self.calculateTargetPos()
        
    def onBacktestBar(self, bar) :
        """ same as onBar but for backtests """
        super(MySignals4Strategy, self).onBar(bar)
        # self.barGen.updateBar(bar)
        # print(bar.datetime)
        self.barGen.updateWithMinuteBar(bar)
        # print("Main onBar: ", bar.time, self.vtSymbol, " ", bar.close)
        # for i in range(len(self.signals)) :
        #     print("onBar ", bar.time, self.vtSymbol, bar.close, self.signals[i].name, self.signals[i].getSignalPos(),
        #         self.signals[i].dailyReturn, self.signals[i].cumReturn)

        self.calculateTargetPos()
       
    def recPosChange(self, price) :
        for i in range(len(self.signals)) :
            print(("recPosCh ", self.vtSymbol, self.signals[i].name, datetime.now().replace(second=0, microsecond=0),
                self.signals[i].getSignalPos(), price))

    #----------------------------------------------------------------------
    def calculateTargetPos(self):
        """计算目标仓位"""
        targetPos = 0
        for i in range(len(self.signals)) :
            targetPos += self.signals[i].getSignalPos()
        
        self.setTargetPos(targetPos)
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        super(MySignals4Strategy, self).onOrder(order)
        # for i in range(len(self.signals)) :
        #     print("onOrder ", self.vtSymbol, self.signals[i].name, self.signals[i].getSignalPos())

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        for i in range(len(self.signals)) :
            print(("onTrade ", self.vtSymbol, self.signals[i].name, self.signals[i].getSignalPos()))
       
        self.putEvent()
