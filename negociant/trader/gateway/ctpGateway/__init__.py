# encoding: UTF-8


from negociant.trader import vtConstant
from .lkCtpGateway import CtpGateway, CtpAccount

gatewayClass = CtpGateway
gatewayName = 'CTP'
gatewayDisplayName = 'CTP'
gatewayType = vtConstant.GATEWAYTYPE_FUTURES
gatewayQryEnabled = True
