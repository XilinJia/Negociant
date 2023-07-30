#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().magic('matplotlib inline')

from negociant.trader.app.ctaStrategy.lkBacktesting import BacktestingEngine, OptimizationSetting, MINUTE_DB_NAME
from negociant.trader.app.ctaStrategy.strategy.strategyBollChannel import BollChannelStrategy


# In[2]:


# 创建回测引擎对象
engine = BacktestingEngine()


# In[3]:


# 设置回测使用的数据
engine.setBacktestingMode(engine.BAR_MODE)    # 设置引擎的回测模式为K线
engine.setDatabase(MINUTE_DB_NAME, 'rb0000')  # 设置使用的历史数据库
engine.setStartDate('20110101')               # 设置回测用的数据起始日期


# In[4]:


# 配置回测引擎参数
engine.setSlippage(1)      # 设置滑点为1跳
engine.setRate(1/10000)    # 设置手续费万1
engine.setSize(10)         # 设置合约大小 
engine.setPriceTick(1)     # 设置最小价格变动   
engine.setCapital(30000)   # 设置回测本金


# In[5]:


# 在引擎中创建策略对象
d = {}                                         # 策略参数配置
engine.initStrategy(BollChannelStrategy, d)    # 创建策略对象


# In[6]:


# 运行回测
engine.runBacktesting()


# In[ ]:


# 显示逐日回测结果
engine.showDailyResult()


# In[ ]:


# 显示逐笔回测结果
engine.showBacktestingResult()


# In[ ]:


# 显示前10条成交记录
for i in range(10):
    d = engine.tradeDict[str(i+1)].__dict__
    print('TradeID: %s, Time: %s, Direction: %s, Price: %s, Volume: %s' %(d['tradeID'], d['dt'], d['direction'], d['price'], d['volume']))

