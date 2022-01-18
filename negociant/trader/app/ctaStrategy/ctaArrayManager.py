# encoding: UTF-8

import numpy as np
import talib

########################################################################
class ArrayManager(object):
    """
    K线序列管理工具，负责：
    1. K线时间序列的维护
    2. 常用技术指标的计算
    """

    #----------------------------------------------------------------------
    def __init__(self, size=100):
        """Constructor"""
        self.count = 0                      # 缓存计数
        self.size = size                    # 缓存大小
        self.inited = False                 # True if count>=size
        
        self.openArray = []     # OHLC
        self.highArray = []
        self.lowArray = []
        self.closeArray = []
        self.volumeArray = []

        self.setSize(self.size)


    def setSize(self, size) :
        if size>0 :
            self.openArray = np.zeros(size)     # OHLC
            self.highArray = np.zeros(size)
            self.lowArray = np.zeros(size)
            self.closeArray = np.zeros(size)
            self.volumeArray = np.zeros(size)
        else :
            print("array size should be > 0")
        

    def updateCurBar(self, bar) :
        self.openArray[-1] = bar.open
        self.highArray[-1] = max(self.highArray[-1], bar.high)
        self.lowArray[-1] = min(self.lowArray[-1], bar.low)     
        self.closeArray[-1] = bar.close
        self.volumeArray[-1] += bar.volume

    def setCurBar(self, bar) :
        self.openArray[-1] = bar.open
        self.highArray[-1] = bar.high
        self.lowArray[-1] = bar.low        
        self.closeArray[-1] = bar.close
        self.volumeArray[-1] = bar.volume

    def allocNewBar(self) :
        self.openArray[:-1] = self.openArray[1:]
        self.highArray[:-1] = self.highArray[1:]
        self.lowArray[:-1] = self.lowArray[1:]
        self.closeArray[:-1] = self.closeArray[1:]
        self.volumeArray[:-1] = self.volumeArray[1:]
        self.lowArray[-1] = 10000000
        self.volumeArray[-1] = 0

    #----------------------------------------------------------------------
    def updateBar(self, bar):
        """更新K线"""
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True
        
        self.allocNewBar()
        self.setCurBar(bar)
        
    #----------------------------------------------------------------------
    @property
    def op(self):
        """获取开盘价序列"""
        return self.openArray
        
    #----------------------------------------------------------------------
    @property
    def hi(self):
        """获取最高价序列"""
        return self.highArray
    
    #----------------------------------------------------------------------
    @property
    def lo(self):
        """获取最低价序列"""
        return self.lowArray
    
    #----------------------------------------------------------------------
    @property
    def cl(self):
        """获取收盘价序列"""
        return self.closeArray
    
    #----------------------------------------------------------------------
    @property    
    def volume(self):
        """获取成交量序列"""
        return self.volumeArray
    
    #----------------------------------------------------------------------
    def sma(self, n, array=False):
        """简单均线"""
        result = talib.SMA(self.cl, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def std(self, n, array=False):
        """标准差"""
        result = talib.STDDEV(self.cl, n)
        if array:
            return result
        return result[-1]
    
    #----------------------------------------------------------------------
    def cci(self, n, array=False):
        """CCI指标"""
        result = talib.CCI(self.hi, self.lo, self.cl, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def atr(self, n, array=False):
        """ATR指标"""
        result = talib.ATR(self.hi, self.lo, self.cl, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def rsi(self, n, array=False):
        """RSI指标"""
        result = talib.RSI(self.cl, n)
        if array:
            return result
        return result[-1]
    
    #----------------------------------------------------------------------
    def macd(self, fastPeriod, slowPeriod, signalPeriod, array=False):
        """MACD指标"""
        macd, signal, hist = talib.MACD(self.cl, fastPeriod,
                                        slowPeriod, signalPeriod)
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]
    
    #----------------------------------------------------------------------
    def adx(self, n, array=False):
        """ADX指标"""
        result = talib.ADX(self.hi, self.lo, self.cl, n)
        if array:
            return result
        return result[-1]
    
    #----------------------------------------------------------------------
    def boll(self, n, dev, array=False):
        """布林通道"""
        mid = self.sma(n, array)
        std = self.std(n, array)
        
        up = mid + std * dev
        down = mid - std * dev
        
        return up, down    
    
    #----------------------------------------------------------------------
    def keltner(self, n, dev, array=False):
        """肯特纳通道"""
        mid = self.sma(n, array)
        atr = self.atr(n, array)
        
        up = mid + atr * dev
        down = mid - atr * dev
        
        return up, down
    
    #----------------------------------------------------------------------
    def donchian(self, n, array=False):
        """唐奇安通道"""
        up = talib.MAX(self.hi, n)
        down = talib.MIN(self.lo, n)
        
        if array:
            return up, down
        return up[-1], down[-1]
