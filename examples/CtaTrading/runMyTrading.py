# encoding: UTF-8


import sys
import importlib
try:
    importlib.reload(sys)  # Python 2
    # sys.setdefaultencoding('utf8')
except NameError:
    pass         # Python 3

import multiprocessing
from time import sleep
from datetime import datetime, time

from negociant.event import EventEngine2
from negociant.trader.vtEvent import EVENT_LOG, EVENT_ERROR
from negociant.trader.vtEngine import MainEngine, LogEngine
from negociant.trader.gateway import ctpGateway
from negociant.trader.gateway.ctpGateway import CtpAccount
from negociant.trader.app import ctaStrategy
from negociant.trader.app.ctaStrategy.ctaBase import EVENT_CTA_LOG



#----------------------------------------------------------------------
def processErrorEvent(event):
    """
    处理错误事件
    错误信息在每次登陆后，会将当日所有已产生的均推送一遍，所以不适合写入日志
    """
    error = event.dict_['data']
    print('错误代码：%s，错误信息：%s' %(error.errorID, error.errorMsg))
    
#----------------------------------------------------------------------
def runChildProcess(ctpAccount):
    """子进程运行函数"""
    print('-'*20)
    
    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()
    le.addFileHandler()
    
    le.info('启动CTA策略运行子进程')
    
    ee = EventEngine2()
    le.info('事件引擎创建成功')
    
    me = MainEngine(ee)
    me.addGateway(ctpGateway, ctpAccount)
    me.addApp(ctaStrategy)
    le.info('主引擎创建成功')
    
    ee.register(EVENT_LOG, le.processLogEvent)
    ee.register(EVENT_CTA_LOG, le.processLogEvent)
    ee.register(EVENT_ERROR, processErrorEvent)
    le.info('注册日志事件监听')
    
    me.connect('CTP')
    le.info('连接CTP接口')
    
    sleep(10)                       # 等待CTP接口初始化
    me.dataEngine.saveContracts()   # 保存合约信息到文件
    
    cta = me.getApp(ctaStrategy.appName)
    
    cta.loadSetting()
    le.info('CTA策略载入成功')
    
    cta.initAll()
    le.info('CTA策略初始化成功')
    
    cta.startAll()
    le.info('CTA策略启动成功')
    
    while True:
        sleep(1)

#----------------------------------------------------------------------
def runParentProcess(CTPFile='CTP_connect'):
    """父进程运行函数"""
    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()
    
    le.info('启动CTA策略守护父进程')
    
    DAY_START = time(8, 45)         # 日盘启动和停止时间
    DAY_END = time(15, 30)
    
    NIGHT_START = time(20, 45)      # 夜盘启动和停止时间
    NIGHT_END = time(2, 45)
    
    p = None        # 子进程句柄
    
    print("Date and Time: ", datetime.today().weekday(), " ", datetime.now().time())

    ctpAccount = CtpAccount(CTPFile)

    while True:
        currentTime = datetime.now().time()
        recording = False
        
        # 判断当前处于的时间段
        if ((currentTime >= DAY_START and currentTime <= DAY_END) or
            (currentTime >= NIGHT_START) or
            (currentTime <= NIGHT_END)):
            recording = True
        
        # 过滤周末时间段：周六日盘，周一凌晨，周日全天
        if ((datetime.today().weekday() == 6) or 
            (datetime.today().weekday() == 5 and currentTime > NIGHT_END) or 
            (datetime.today().weekday() == 0 and currentTime < DAY_START)):
            recording = False

        # 记录时间则需要启动子进程
        if recording and p is None:
        # if p is None:
            le.info('启动子进程')
            p = multiprocessing.Process(target=runChildProcess, args=(ctpAccount,))
            p.start()
            le.info('子进程启动成功')
            
        # 非记录时间则退出子进程
        if not recording and p is not None:
            le.info('关闭子进程')
            p.terminate()
            p.join()
            p = None
            le.info('子进程关闭成功')
            
        sleep(5)


if __name__ == '__main__':
    runParentProcess()
    # runChildProcess(None)