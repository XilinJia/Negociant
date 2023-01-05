'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

# encoding: UTF-8

import copy
import numpy as np
from collections import OrderedDict

from negociant.trader.vtObject import VtOrderData, VtTradeData
from negociant.trader.vtConstant import DIRECTION_LONG

class TradeResults(object) :
    def __init__(self) :
        self.tradeDict = OrderedDict()

        self.capital = 1000000      # 回测时的起始本金（默认100万）
        self.slippage = 0           # 回测时假设的滑点
        self.rate = 0               # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = 1               # 合约大小，默认为1    

        self.bar = None
        self.dt = None      # 最新的时间

        self.capital = 0             # 资金
        self.maxCapital = 0          # 资金最高净值
        self.drawdown = 0            # 回撤        
        self.totalResult = 0         # 总成交数量
        self.totalTurnover = 0       # 总成交金额（合约面值）
        self.totalCommission = 0     # 总手续费
        self.totalSlippage = 0       # 总滑点        
        self.timeList = []           # 时间序列
        self.pnlList = []            # 每笔盈亏序列
        self.capitalList = []        # 盈亏汇总的时间序列
        self.drawdownList = []       # 回撤的时间序列
        self.winningResult = 0       # 盈利次数
        self.losingResult = 0        # 亏损次数		
        self.totalWinning = 0        # 总盈利金额		
        self.totalLosing = 0         # 总亏损金额    

        self.resultList = []             # 交易结果列表
        self.longTrade = []              # 未平仓的多头交易
        self.shortTrade = []             # 未平仓的空头交易
        self.tradeTimeList = []          # 每笔成交时间戳
        self.posList = [0]               # 每笔成交后的持仓情况        

        self.winningRate = 0
        self.averageWinning = 0                                  # 这里把数据都初始化为0
        self.averageLosing = 0
        self.profitLossRatio = 0

    def calculateTradeResults(self):
        """
        compute trade results
        """        
        if not self.tradeDict:
            return
        
        # 首先基于回测后的成交记录，计算每笔交易的盈亏

        for trade in self.tradeDict.values():
            # 复制成交对象，因为下面的开平仓交易配对涉及到对成交数量的修改
            # 若不进行复制直接操作，则计算完后所有成交的数量会变成0
            trade = copy.copy(trade)
            
            # 多头交易
            if trade.direction == DIRECTION_LONG:
                # 如果尚无空头交易
                if not self.shortTrade:
                    self.longTrade.append(trade)
                # 当前多头交易为平空
                else:
                    while True:
                        entryTrade = self.shortTrade[0]
                        exitTrade = trade
                        
                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt, 
                                               exitTrade.price, exitTrade.dt,
                                               -closedVolume, self.rate, self.slippage, self.size)
                        self.resultList.append(result)
                        
                        self.posList.extend([-1,0])
                        self.tradeTimeList.extend([result.entryDt, result.exitDt])
                        
                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume
                        
                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            self.shortTrade.pop(0)
                        
                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break
                        
                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not self.shortTrade:
                                self.longTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass
                        
            # 空头交易        
            else:
                # 如果尚无多头交易
                if not self.longTrade:
                    self.shortTrade.append(trade)
                # 当前空头交易为平多
                else:                    
                    while True:
                        entryTrade = self.longTrade[0]
                        exitTrade = trade
                        
                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt, 
                                               exitTrade.price, exitTrade.dt,
                                               closedVolume, self.rate, self.slippage, self.size)
                        self.resultList.append(result)
                        
                        self.posList.extend([1,0])
                        self.tradeTimeList.extend([result.entryDt, result.exitDt])

                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume
                        
                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            self.longTrade.pop(0)
                        
                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break
                        
                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not self.longTrade:
                                self.shortTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass                    
        
        # 到最后交易日尚未平仓的交易，则以最后价格平仓
        # if self.mode == self.BAR_MODE:
        #     endPrice = self.bar.close
        # else:
        #     endPrice = self.tick.lastPrice
                   
        for trade in self.longTrade:
            result = TradingResult(trade.price, trade.dt, self.bar.close, self.dt, 
                                   trade.volume, self.rate, self.slippage, self.size)
            self.resultList.append(result)
            
        for trade in self.shortTrade:
            result = TradingResult(trade.price, trade.dt, self.bar.close, self.dt, 
                                   -trade.volume, self.rate, self.slippage, self.size)
            self.resultList.append(result)            
        
        # 检查是否有交易
        if not self.resultList:
            return 
        
        # 然后基于每笔交易的结果，我们可以计算具体的盈亏曲线和最大回撤等        
        
        for result in self.resultList:
            self.capital += result.pnl
            self.maxCapital = max(self.capital, self.maxCapital)
            self.drawdown = self.capital - self.maxCapital
            
            self.pnlList.append(result.pnl)
            self.timeList.append(result.exitDt)      # 交易的时间戳使用平仓时间
            self.capitalList.append(self.capital)
            self.drawdownList.append(self.drawdown)
            
            self.totalResult += 1
            self.totalTurnover += result.turnover
            self.totalCommission += result.commission
            self.totalSlippage += result.slippage
            
            if result.pnl >= 0:
                self.winningResult += 1
                self.totalWinning += result.pnl
            else:
                self.losingResult += 1
                self.totalLosing += result.pnl
                
        # 计算盈亏相关数据
        self.winningRate = self.winningResult/self.totalResult*100         # 胜率
                
        if self.winningResult:
            self.averageWinning = self.totalWinning/self.winningResult     # 平均每笔盈利
        if self.losingResult:
            self.averageLosing = self.totalLosing/self.losingResult        # 平均每笔亏损
        if self.averageLosing:
            self.profitLossRatio = -self.averageWinning/self.averageLosing # 盈亏比


class DailyResults(object) :
    def __init__(self) :
        self.tradeDict = OrderedDict()
        self.dailyResultDict = OrderedDict()

        self.capital = 1000000      # 回测时的起始本金（默认100万）
        self.slippage = 0           # 回测时假设的滑点
        self.rate = 0               # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = 1               # 合约大小，默认为1    

        self.startDate = None
        self.endDate = None 
        self.totalDays = 0

        self.profitDays = 0
        self.lossDays = 0
        self.endBalance = self.capital
        self.highlevel = self.capital
        self.totalNetPnl = 0
        self.totalTurnover = 0
        self.totalCommission = 0
        self.totalSlippage = 0
        self.totalTradeCount = 0
        
        self.netPnlList = []
        self.balanceList = []
        self.highlevelList = []
        self.drawdownList = []
        self.ddPercentList = []
        self.returnList = []

        self.maxDrawdown = 0
        self.maxDdPercent = 0
        self.totalReturn = 0
        self.dailyReturn = 0
        self.annualizedReturn = 0
        self.returnStd = 0
        self.sharpeRatio = 0

    #----------------------------------------------------------------------
    def updateDailyClose(self, dt, price) :
        """更新每日收盘价"""
        date = dt.date()
        
        if date not in self.dailyResultDict:
            self.dailyResultDict[date] = DailyResult(date, price)
        else:
            self.dailyResultDict[date].closePrice = price


    #----------------------------------------------------------------------
    def calculateDailyResult(self):
        """计算按日统计的交易结果"""
        
        # 检查成交记录
        if not self.tradeDict:
            return 
        
        # 将成交添加到每日交易结果中
        for trade in self.tradeDict.values():
            date = trade.dt.date()
            dailyResult = self.dailyResultDict[date]
            dailyResult.addTrade(trade)
            
        # 遍历计算每日结果
        previousClose = 0
        openPosition = 0
        for dailyResult in self.dailyResultDict.values():
            dailyResult.previousClose = previousClose
            previousClose = dailyResult.closePrice
            
            dailyResult.calculatePnl(openPosition, self.size, self.rate, self.slippage )
            openPosition = dailyResult.closePosition
    
    #----------------------------------------------------------------------
    def calculateDailyStatistics(self, annualDays=240):
        """计算按日统计的结果"""
        dateList = self.dailyResultDict.keys()
        resultList = self.dailyResultDict.values()
        
        self.startDate = dateList[0]
        self.endDate = dateList[-1]  
        self.totalDays = len(dateList)
        
        for result in resultList:
            if result.netPnl > 0:
                self.profitDays += 1
            elif result.netPnl < 0:
                self.lossDays += 1
            self.netPnlList.append(result.netPnl)
            
            prevBalance = self.endBalance
            self.endBalance += result.netPnl
            self.balanceList.append(self.endBalance)
            self.returnList.append(self.endBalance/prevBalance - 1)
            
            self.highlevel = max(self.highlevel, self.endBalance)
            self.highlevelList.append(self.highlevel)
            
            drawdown = self.endBalance - self.highlevel
            self.drawdownList.append(drawdown)
            self.ddPercentList.append(drawdown/self.highlevel*100)
            
            self.totalTurnover += result.turnover
            self.totalCommission += result.commission
            self.totalSlippage += result.slippage
            self.totalTradeCount += result.tradeCount
            self.totalNetPnl += result.netPnl
        
        self.maxDrawdown = min(self.drawdownList)
        self.maxDdPercent = min(self.ddPercentList)
        self.totalReturn = (self.endBalance / self.capital - 1) * 100
        self.dailyReturn = np.mean(self.returnList) * 100
        self.annualizedReturn = self.dailyReturn * annualDays
        self.returnStd = np.std(self.returnList) * 100
        
        if self.returnStd:
            self.sharpeRatio = self.dailyReturn / self.returnStd * np.sqrt(annualDays)
        else:
            self.sharpeRatio = 0
        

########################################################################
class TradingResult(object):
    """每笔交易的结果"""

    #----------------------------------------------------------------------
    def __init__(self, entryPrice, entryDt, exitPrice, 
                 exitDt, volume, rate, slippage, size):
        """Constructor"""
        self.entryPrice = entryPrice    # 开仓价格
        self.exitPrice = exitPrice      # 平仓价格
        
        self.entryDt = entryDt          # 开仓时间datetime    
        self.exitDt = exitDt            # 平仓时间
        
        self.volume = volume    # 交易数量（+/-代表方向）
        
        self.turnover = (self.entryPrice+self.exitPrice)*size*abs(volume)   # 成交金额
        self.commission = self.turnover*rate                                # 手续费成本
        self.slippage = slippage*2*size*abs(volume)                         # 滑点成本
        self.pnl = ((self.exitPrice - self.entryPrice) * volume * size 
                    - self.commission - self.slippage)                      # 净盈亏


########################################################################
class DailyResult(object):
    """每日交易的结果"""

    #----------------------------------------------------------------------
    def __init__(self, date, closePrice):
        """Constructor"""
        self.date = date                # 日期
        self.closePrice = closePrice    # 当日收盘价
        self.previousClose = 0          # 昨日收盘价
        
        self.tradeList = []             # 成交列表
        self.tradeCount = 0             # 成交数量
        
        self.openPosition = 0           # 开盘时的持仓
        self.closePosition = 0          # 收盘时的持仓
        
        self.tradingPnl = 0             # 交易盈亏
        self.positionPnl = 0            # 持仓盈亏
        self.totalPnl = 0               # 总盈亏
        
        self.turnover = 0               # 成交量
        self.commission = 0             # 手续费
        self.slippage = 0               # 滑点
        self.netPnl = 0                 # 净盈亏
        
    #----------------------------------------------------------------------
    def addTrade(self, trade):
        """添加交易"""
        self.tradeList.append(trade)

    #----------------------------------------------------------------------
    def calculatePnl(self, openPosition=0, size=1, rate=0, slippage=0):
        """
        计算盈亏
        size: 合约乘数
        rate：手续费率
        slippage：滑点点数
        """
        # 持仓部分
        self.openPosition = openPosition
        self.positionPnl = self.openPosition * (self.closePrice - self.previousClose) * size
        self.closePosition = self.openPosition
        
        # 交易部分
        self.tradeCount = len(self.tradeList)
        
        for trade in self.tradeList:
            if trade.direction == DIRECTION_LONG:
                posChange = trade.volume
            else:
                posChange = -trade.volume
                
            self.tradingPnl += posChange * (self.closePrice - trade.price) * size
            self.closePosition += posChange
            self.turnover += trade.price * trade.volume * size
            self.commission += trade.price * trade.volume * size * rate
            self.slippage += trade.volume * size * slippage
            # print("DailyPnL: ", self.date, posChange, trade.price, self.closePrice)
        
        # 汇总
        self.totalPnl = self.tradingPnl + self.positionPnl
        self.netPnl = self.totalPnl - self.commission - self.slippage
