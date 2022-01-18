import os
from negociant.trader.app.ctaStrategy.ctaBacktesting import MINUTE_DB_NAME
from negociant.trader.app.ctaStrategy.ctaHistoryData import loadMcCsv

loadMcCsv(os.path.join('.', 'p.000000 1min.csv'), MINUTE_DB_NAME, 'p0000', '%Y/%m/%d')