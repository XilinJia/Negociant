'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

import json
from datetime import datetime, timedelta, time
from negociant.trader.vtFunction import getJsonPath

class MarketOpenings(object):
    """ records market operating time """

    def __init__(self, marketName, marketTimes):
        """ Constructor
        marketName is a string,
        marketTimes is a dict in the following format: 
        {
            "SymbolsIncluded": ["P1901", "y1901"],  
            "MORNING_START": "09:00",
            "MORNING_BREAK": "10:15",
            "MORNING_RESTART": "10:30",
            "MORNING_END": "11:30",
            "AFTERNOON_START": "13:30",
            "AFTERNOON_END": "15:00",
            "NIGHT_START": "21:00",
            "NIGHT_END": "02:30"
        }
        you may add as many symbols as you want, after 'SymbolsIncluded',
        it's better to define market hours based on symbols due to the different policies of exchanges,
        if you add symbols, the symbols must be the same as defined by the exchange,
        if the symbol is periodic, such as in futures contracts, you can add only its base symbol, ("y" instead of "y1901"),
        if you add symbols, you may define the exchange name arbitrarily,
        the system checks by the symbols first, and if not found, it checks by the exchange names,
        you may define or leave out any of these time points, if that makes sense,
        but you must define 'MORNING_START' for non-24-hour sessions,
        if you leave out 'MORNING_START', then the system assumes it being a 24-hour session,
        the order of these time points can be arbitrary,
        the format of the time points must be 'HH:MM',
        'NIGHT_END' does not equal the end of a day bar, which is defined elsewhere,
        """

        self.market = marketName
        self.sessions = []

        self.morningStart = None
        self.morningBreak = None
        self.morningRestart = None
        self.morningEnd = None
        self.aftStart = None
        self.aftEnd = None
        self.nightStart = None
        self.nightEnd = None

        session = [0, 0]
        id = 0
        if "MORNING_START" in marketTimes:
            self.morningStart = datetime.strptime(marketTimes["MORNING_START"], '%H:%M').time()
            session[id] = self.morningStart
            id = 1
        else :
            session[0] = time(0, 0)
            session[1] = time(0, 0)
            self.sessions.append(session)
            return

        if "MORNING_BREAK" in marketTimes:
            self.morningBreak = datetime.strptime(marketTimes["MORNING_BREAK"], '%H:%M').time()
            session[id] = self.morningBreak
            self.sessions.append(session)
            session = [0, 0]
            id = 0

        if "MORNING_RESTART" in marketTimes and id == 0:
            self.morningRestart = datetime.strptime(marketTimes["MORNING_RESTART"], '%H:%M').time()
            session[id] = self.morningRestart
            id = 1

        if "MORNING_END" in marketTimes and id == 1:
            self.morningEnd = datetime.strptime(marketTimes["MORNING_END"], '%H:%M').time()
            session[id] = self.morningEnd
            self.sessions.append(session)
            session = [0, 0]
            id = 0

        if "AFTERNOON_START" in marketTimes and id == 0:
            self.aftStart = datetime.strptime(marketTimes["AFTERNOON_START"], '%H:%M').time()
            session[id] = self.aftStart
            id = 1

        if "AFTERNOON_END" in marketTimes and id == 1:
            self.aftEnd = datetime.strptime(marketTimes["AFTERNOON_END"], '%H:%M').time()
            session[id] = self.aftEnd
            self.sessions.append(session)
            session = [0, 0]
            id = 0

        if "NIGHT_START" in marketTimes and id == 0:
            self.nightStart = datetime.strptime(marketTimes["NIGHT_START"], '%H:%M').time()
            session[id] = self.nightStart
            id = 1

        if "NIGHT_END" in marketTimes and id == 1:
            self.nightEnd = datetime.strptime(marketTimes["NIGHT_END"], '%H:%M').time()
            session[id] = self.nightEnd
            self.sessions.append(session)

    # TODO, need to add a self.looseSessions
    def isMarketOpen(self, curTime, looseTerm=False) :
        """ checks if market is open """
        # not include closing time
        for session in self.sessions :
            if session[0] == session[1] :
                return True
            elif session[0] < session[1] :
                if session[0] <= curTime < session[1] :
                    return True
            else:
                if session[0] <= curTime or curTime < session[1] :
                    return True

        return False                        


    def isAtMarketOpen(self, curTime, looseTerm=False) :
        """ checks if the time is at market opening """
        return curTime == self.morningStart   

    def isAtMarketClose(self, curTime, looseTerm=False) :
        """ checks if the time is at market closing """
        return curTime == self.aftEnd

    def isMarketDayFinished(self, curTime, looseTerm=False) :
        """ checks if the time is at market closing """
        return self.aftEnd < curTime < self.nightStart

    def isMarketJustClose(self, curTime) :
        """ 5 minutes after session is closed """
        endSlot = (datetime(1,1,1, self.aftEnd.hour, self.aftEnd.minute) + timedelta(minutes=5)).time()   # 5 minutes after session close
        if self.aftEnd < curTime <= endSlot :
            return True
        return False

    def isAtSessionOpen(self, curTime, looseTerm=False) :
        """ checks if the time is at session opening """           
        for session in self.sessions :
            if session[0] == curTime :
                return True
        return False

    def isAtSessionClose(self, curTime, looseTerm=False) :
        """ checks if the time is at session closing """           
        for session in self.sessions :
            if session[1] == curTime :
                return True
        return False

    def isSessionClosingBar(self, curTime, looseTerm=False) :
        """ checks if the time is at session's closing bar """           
        for session in self.sessions :
            endSlot = (datetime(1,1,1, session[1].hour, session[1].minute) - timedelta(minutes=1)).time()  
            if endSlot == curTime :
                return True
        return False

    def isSessionJustClose(self, curTime) :
        """ 5 minutes after session is closed """
        for session in self.sessions :
            endSlot = (datetime(1,1,1, session[1].hour, session[1].minute) + timedelta(minutes=5)).time()   # 5 minutes after session close
            if session[1] < curTime <= endSlot :
                return True
        return False

    # def isMarketClosingBar(self, curTime, looseTerm=False) :
    #     """ checks if the time is at session's closing bar """           
    #     for session in self.sessions :
    #         endSlot = (datetime(1,1,1, self.aftEnd.hour, self.aftEnd.minute) - timedelta(minutes=1)).time()  
    #         if endSlot == curTime or self.aftEnd == curTime:
    #             return True
    #     return False

    def isMarketClosingBar(self, curTime, looseTerm=False) :
        """ checks if the time is at session's closing bar """           
        endSlot = (datetime(1,1,1, self.aftEnd.hour, self.aftEnd.minute) - timedelta(minutes=1)).time()  
        return (endSlot == curTime or self.aftEnd == curTime)


class MarketsOpHours(object):
    """ records market hours that is defined in file 'MarketHours.json' """

    settingFileName = 'MarketHours.json'
    settingFilePath = getJsonPath(settingFileName, __file__)  

    weekdayOffset = (3, 1, 1, 1, 1, 1, 2)

    def __init__(self):
        """Constructor"""
        self.markettimes = dict()
        self.loadSetting()


    def loadSetting(self):
        """ load market operating times from file """
        with open(self.settingFilePath) as f:
            markets = json.load(f)
            for ex in markets:
                mts = MarketOpenings(ex, markets[ex])
                self.markettimes[ex] = mts
                if "SymbolsIncluded" in markets[ex] :
                    for symbol in markets[ex]["SymbolsIncluded"] :
                        self.markettimes[symbol] = mts


    def _formatCurTime(self, curTime=None) :
        if curTime and type(curTime) == time:
            return curTime.replace(second=0, microsecond=0)

        if curTime :
            cTime = datetime.strptime(curTime, '%H:%M:%S.%f').replace(second=0, microsecond=0).time()
        else :
            cTime = datetime.now().replace(second=0, microsecond=0).time()

        return cTime   

    def isMarketOpen(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if market is open at 'curTime'
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isMarketOpen(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isMarketOpen(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isMarketOpen(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False


    def isAtMarketOpen(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if 'curTime' is at market opening time
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isAtMarketOpen(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isAtMarketOpen(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isAtMarketOpen(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False

    def isAtMarketClose(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if 'curTime' is at market's closing time
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isAtMarketClose(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isAtMarketClose(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isAtMarketClose(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False

    def isMarketDayFinished(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if 'curTime' is after market day's finish
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isMarketDayFinished(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isMarketDayFinished(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isMarketDayFinished(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False


    def isAtSessionOpen(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if 'curTime' is at a session's opening time
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isAtSessionOpen(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isAtSessionOpen(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isAtSessionOpen(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False


    def isAtSessionClose(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if 'curTime' is at a session's closing time
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isAtSessionClose(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isAtSessionClose(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isAtSessionClose(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False

    def isSessionClosingBar(self, symbol, exchange=None, barTime=None, looseTerm=False) :
        """ 
        checks if 'barTime' is a session's closing bar
        """
        cTime = self._formatCurTime(barTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isSessionClosingBar(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isSessionClosingBar(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isSessionClosingBar(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False


    def isSessionJustClose(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if market is open at 'curTime'
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        # print(symbol, aSym)
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isSessionJustClose(cTime) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isSessionJustClose(cTime) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isSessionJustClose(cTime) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False


    def isMarketJustClose(self, symbol, exchange=None, curTime=None, looseTerm=False) :
        """ 
        checks if market is open at 'curTime'
        """
        cTime = self._formatCurTime(curTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        # print(symbol, aSym)
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isMarketJustClose(cTime) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isMarketJustClose(cTime) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isMarketJustClose(cTime) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False


    def isMarketClosingBar(self, symbol, exchange=None, barTime=None, looseTerm=False) :
        """ 
        checks if 'barTime' is a session's closing bar
        """
        cTime = self._formatCurTime(barTime)

        aSym = filter(str.isalpha, symbol.encode('ascii', 'ignore'))
        if aSym and aSym in self.markettimes :
            if self.markettimes[aSym].isMarketClosingBar(cTime, looseTerm) :
                return True
            else :
                return False
        elif symbol in self.markettimes :
            if self.markettimes[symbol].isMarketClosingBar(cTime, looseTerm) :
                return True
            else :
                return False
        else :
            if exchange and exchange in self.markettimes :
                if self.markettimes[exchange].isMarketClosingBar(cTime, looseTerm) : 
                    return True
            else :
                # if exchange is not specified, assume open
                return True

        return False
