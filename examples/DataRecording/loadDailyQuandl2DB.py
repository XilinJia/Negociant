import os
from negociant.trader.app.ctaStrategy.ctaBacktesting import DAILY_DB_NAME
from negociant.trader.app.ctaStrategy.ctaHistoryData import loadDailyQuandlCsv

loadDailyQuandlCsv(os.path.join('.', 'PAdjM.csv'), DAILY_DB_NAME, 'p.HOT')
loadDailyQuandlCsv(os.path.join('.', 'SRAdjM.csv'), DAILY_DB_NAME, 'SR.HOT')