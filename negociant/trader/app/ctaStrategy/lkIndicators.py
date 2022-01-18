'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

import numpy as np

def trueRange(op, hi, lo, cl) :
    truehigh = hi[-1] if hi[-1]>cl[-2] else cl[-2]
    truelow = lo[-1] if lo[-1]<cl[-2] else cl[-2]
    return truehigh-truelow

def NBarHigh(a, n) :
    highest = -np.inf
    j = -1
    while j >= -n :
        if a[j]>highest :
            highest = a[j]
        j -= 1
    return highest

#  proprietary code removed