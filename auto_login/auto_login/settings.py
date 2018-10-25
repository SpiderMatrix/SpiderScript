# -*- coding: utf-8 -*-

import os
import platform
import sys
from os.path import join

BOT_NAME = 'auto_login'

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'auto_login'))

SPIDER_MODULES = ['auto_login.spiders']
NEWSPIDER_MODULE = 'auto_login.spiders'

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 0.5

COOKIES_ENABLED = False

MINT_JD_PROXY = "http://127.0.0.1:9800"

MINT_TB_PROXY = "http://127.0.0.1:9801"

MINT_SN_SHOP_PROXY = "http://127.0.0.1:9802"

MINT_SN_BRAND_PROXY = "http://127.0.0.1:9803"

DEV = True

# DRIVER_PATH = "C:\\Users\\Administrator\\Downloads\\DtCrawlScript\\auto_login"
# DRIVER_PATH = os.path.join('C:\\Users\\Administrator\\Downloads\\DtCrawlScript\\auto_login')
DRIVER_PATH = "C:\\Users\\Administrator\\Downloads\\DtCrawlScript\\auto_login"
IMG_PATH = 'C:\\Users\\Administrator\\Downloads\\DtCrawlScript\\auto_login\\snap_shoot'


CHROME_DOCKER_URL = "http://xxxxxx:4444/wd/hub"


def judge_driver_path():
    if os.path.exists(DRIVER_PATH):
        # return DRIVER_PATH + '\\chromedriver.exe'
        return DRIVER_PATH + '\\chromedriver.exe'
    else:
        sys_name = platform.system()
        if "windows" in sys_name.lower():
            execute_path = os.path.abspath(join(os.getcwd(), "chromedriver.exe"))
        else:
            execute_path = os.path.abspath(join(os.getcwd(), "chromedriver"))
        return execute_path
