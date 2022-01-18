'''
Project: Negociant
Copyright (c) 2017 Xilin Jia <https://github.com/XilinJia>
This software is released under the MIT license
https://opensource.org/licenses/MIT
'''

# encoding: UTF-8


import os
from setuptools import setup

import negociant


def getSubpackages(name):
    """获取该模块下所有的子模块名称"""
    splist = []

    for dirpath, _dirnames, _filenames in os.walk(name):
        if os.path.isfile(os.path.join(dirpath, '__init__.py')):
            splist.append(".".join(dirpath.split(os.sep)))
    
    return splist


setup(
    name='negociant',
    version=negociant.__version__,
    author=negociant.__author__,
    author_email='',
    license='MIT',
    url='',
    description='A framework for developing Quantitative Trading programmes',
    long_description = __doc__,    
    keywords='quant quantitative investment trading algotrading',
    classifiers=['Development Status :: 4 - Beta',
                 'Operating System :: Ubuntu :: Server :: 20.04',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Office/Business :: Financial :: Investment',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'License :: OSI Approved :: MIT License'],
    packages=getSubpackages('negociant'),
    package_data={'': ['*.json', '*.md', '*.ico',
                       '*.h', '*.cpp', '*.bash', '*.txt',
                       '*.dll', '*.lib', '*.so', '*.pyd',
                       '*.dat', '*.ini', '*.pfx', '*.scc', '*.crt', '*.key']},
    extras_require={
        'tq': ["tornado>=4.5.1", "sortedcontainers>=1.5.7"],
    }
)
