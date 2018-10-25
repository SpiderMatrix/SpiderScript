# -*- coding: utf-8 -*-
__author__ = 'freelancher'

import os
import sys

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

execute(
    ["scrapy", "crawl", "xxxxx", "-aredis="'{"host":"xxxxx","port": 6379,"db":1,"password":"xxxxxx"}'])
