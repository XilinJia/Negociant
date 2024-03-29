# encoding: UTF-8

# 重载sys模块，设置默认字符串编码方式为utf8
import sys
import importlib
try:
    importlib.reload(sys)  # Python 2
    sys.setdefaultencoding('utf8')
except NameError:
    pass         # Python 3

# 判断操作系统
import platform
system = platform.system()

# vn.trader模块
from negociant.event import EventEngine
from negociant.trader.uiQt import createQApp
from negociant.trader.uiMainWindow import MainWindow
from negociant.trader.app.rpcService.rsClient import MainEngineProxy

#----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 创建Qt应用对象
    qApp = createQApp()
    
    # 创建事件引擎
    ee = EventEngine()
    
    # 创建主引擎
    reqAddress = 'tcp://localhost:2014'
    subAddress = 'tcp://localhost:0602'    
    me = MainEngineProxy(ee)
    me.init(reqAddress, subAddress)
    
    # 创建主窗口
    mw = MainWindow(me, ee)
    mw.showMaximized()
    
    # 在主线程中启动Qt事件循环
    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
