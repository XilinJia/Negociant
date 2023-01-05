'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

from negociant.trader.app.ctaStrategy.lkCtaTemplate import SCCSignal
from negociant.trader.app.ctaStrategy.lkIndicators import *


class SCC1(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC1, self).__init__(boss, effCapital)
        self.name = 'SCCSR1'
        self.ls = 1
        self.tech.require_HCR()
        self.tech.require_CCR()
        self.tech.require_MOR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC2(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC2, self).__init__(boss, effCapital)
        self.name = 'SCCSR2'
        self.ls = -1
        self.tech.require_L1CR()
        self.tech.require_H2CR()
        self.tech.require_a2MMR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC3(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC3, self).__init__(boss, effCapital)
        self.name = 'SCCSR3'
        self.ls = -1
        self.tech.require_LCRR()
        self.tech.require_HCR()
        self.tech.require_HOR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC4(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC4, self).__init__(boss, effCapital)
        self.name = 'SCCSR4'
        self.ls = 1
        self.tech.require_d3LCR()
        self.tech.require_LCRR()
        self.tech.require_HLR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


