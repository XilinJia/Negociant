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
        self.name = 'SCCP1'
        self.ls = -1
        self.tech.require_HCR()
        self.tech.require_OCR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC2(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC2, self).__init__(boss, effCapital)
        self.name = 'SCCP2'
        self.ls = -1
        self.tech.require_C2CR()
        self.tech.require_MCR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC3(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC3, self).__init__(boss, effCapital)
        self.name = 'SCCP3'
        self.ls = -1
        self.tech.require_a2CCR()
        self.tech.require_M0CR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC4(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC4, self).__init__(boss, effCapital)
        self.name = 'SCCP4'
        self.ls = 1
        self.tech.require_d3H1CR()
        self.tech.require_a2CCR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC5(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC5, self).__init__(boss, effCapital)
        self.name = 'SCCP5'
        self.ls = -1
        self.tech.require_d3MoCR()
        self.tech.require_M0CR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


class SCC6(SCCSignal):
    def __init__(self, boss, effCapital=0.):
        super(SCC6, self).__init__(boss, effCapital)
        self.name = 'SCCP6'
        self.ls = -1
        self.tech.require_OCR()
        self.tech.require_LCR()


    def pravesh(self) :
        pass


    def nikaas(self) :
        pass


