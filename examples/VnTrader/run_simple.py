# encoding: UTF-8

# 重载sys模块，设置默认字符串编码方式为utf8
import sys

try:
    reload(sys)  # Python 2
    sys.setdefaultencoding('utf8')
except NameError:
    pass         # Python 3

# 判断操作系统
import platform

system = platform.system()

# vn.trader模块
from negociant.event import EventEngine
from negociant.trader.vtEngine import MainEngine
from negociant.trader.uiQt import createQApp
from negociant.trader.uiMainWindow import MainWindow

# 加载底层接口
from negociant.trader.gateway import ctpGateway

# 加载上层应用
from negociant.trader.app import (riskManager, ctaStrategy, spreadTrading)


# ----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 创建Qt应用对象
    qApp = createQApp()

    # 创建事件引擎
    ee = EventEngine()

    # 创建主引擎
    me = MainEngine(ee)

    # 添加交易接口
    me.addGateway(ctpGateway)

    # 添加上层应用
    # me.addApp(riskManager)
    me.addApp(ctaStrategy)
    # me.addApp(spreadTrading)

    # 创建主窗口
    mw = MainWindow(me, ee)
    mw.showMaximized()

    # 在主线程中启动Qt事件循环
    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
