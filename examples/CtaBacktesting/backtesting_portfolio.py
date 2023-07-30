#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().magic('matplotlib inline')

from negociant.trader.app.ctaStrategy.lkBacktesting import BacktestingEngine, MINUTE_DB_NAME

def runBacktesting(strategyClass, settingDict, symbol, 
                   startDate, endDate, slippage, 
                   rate, size, priceTick):
    """运行单标的回测"""
    engine = BacktestingEngine()
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase(MINUTE_DB_NAME, symbol)
    engine.setStartDate(startDate)
    engine.setEndDate(endDate)
    engine.setSlippage(slippage)
    engine.setRate(rate)   
    engine.setSize(size)         
    engine.setPriceTick(priceTick)
    
    engine.initStrategy(strategyClass, settingDict)
    engine.runBacktesting()
    df = engine.calculateDailyResult()
    return df


# In[2]:


# 运行IF回测，交易1手
from negociant.trader.app.ctaStrategy.strategy.strategyAtrRsi import AtrRsiStrategy
df1 = runBacktesting(AtrRsiStrategy, {}, 'IF0000', 
                     '20120101', '20170630', 0.2, 
                     0.3/10000, 300, 0.2)


# In[3]:


# 运行rb回测，交易16手
from negociant.trader.app.ctaStrategy.strategy.strategyBollChannel import BollChannelStrategy
settingDict = {'fixedSize': 16}
df2 = runBacktesting(BollChannelStrategy, settingDict, 'rb0000', 
                     '20120101', '20170630', 1, 
                     1/10000, 10, 1)


# In[4]:


# 合并获得组合回测结果
dfp = df1 + df2

# 注意如果被抛弃的交易日位于回测的前后，即两者不重合的日期中，则不会影响组合曲线正确性
# 但是如果被抛弃的交易日位于回测的中部，即两者重合的日期中，组合曲线会出现错误（丢失交易日）
dfp = dfp.dropna()   

# 创建回测引擎，并设置组合回测初始资金后，显示结果
engine = BacktestingEngine()
engine.setCapital(1000000)
dfp, result = engine.calculateDailyStatistics(dfp)
engine.showDailyResult(dfp, result)


# In[5]:


engine = BacktestingEngine()
engine.setCapital(1000000)
df1, result = engine.calculateDailyStatistics(df1)
engine.showDailyResult(df1, result)


# In[ ]:




