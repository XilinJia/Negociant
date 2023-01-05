# encoding: UTF-8

import json
import os

# 默认设置
from .chinese import text, constant
# import chinese.text as text
# import chinese.constant as constant

# 是否要使用英文
from negociant.trader.vtGlobal import globalSetting
if globalSetting['language'] == 'english':
    from .english import text, constant
    # import english.text as text
    # import english.constant as constant