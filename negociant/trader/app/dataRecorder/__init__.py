# encoding: UTF-8


from .lkDrEngine import DrEngine
from .uiDrWidget import DrEngineManager

appName = 'DataRecorder'
appDisplayName = '行情记录'
appEngine = DrEngine
appWidget = DrEngineManager
appIco = 'dr.ico'