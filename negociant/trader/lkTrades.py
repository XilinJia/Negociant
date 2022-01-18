'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

from negociant.trader.vtConstant import *

class OneTrade(object) :
    """ holds info on one round trade """
    def __init__(self):
        """Constructor"""
        self.entryTime = EMPTY_STRING
        self.entryPrice = EMPTY_FLOAT
        self.lots = EMPTY_INT
        self.exitTime = EMPTY_STRING
        self.exitPrice = EMPTY_FLOAT

class TradeRecord(object) :
    """ holds a series of round trades  """
    def __init__(self, vtSymbol):
        """Constructor"""
        self.vtSymbol = vtSymbol
        self.curTrade = None
        self.trades = []
        self.cumReturn = 0.
        
    def addEntry(self, entryTime, entryPrice, lots) :
        self.curTrade = OneTrade()
        self.curTrade.entryTime = entryTime
        self.curTrade.entryPrice = entryPrice
        self.curTrade.lots = lots

    def addExit(self, exitTime, exitPrice) :
        self.curTrade.exitTime = exitTime
        self.curTrade.exitPrice = exitPrice
        self.trades.append(self.curTrade)
        self.cumReturn += self.curTrade.lots * (self.curTrade.exitPrice - self.curTrade.entryPrice)
        
        self.curTrade = None
    