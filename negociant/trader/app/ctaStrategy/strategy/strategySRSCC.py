'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

import sys, inspect

from negociant.trader.app.ctaStrategy.lkCtaTemplate import LKSCC
from SCC import PortSRSCC

########################################################################
class SRSCCStrategy(LKSCC):
    className = 'SRSCCStrategy'
    author = 'XJia'

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(SRSCCStrategy, self).__init__(ctaEngine, setting)

        strats = inspect.getmembers(sys.modules['negociant.trader.app.ctaStrategy.strategy.SCC.PortSRSCC'], inspect.isclass)
        for strat in strats :
            if strat[0] != 'SCCSignal' :
                print("Attach strat: " + strat[0] )
                self.signals.append(strat[1](self))

        self.setSignalCapitals(boostR=1.8)                