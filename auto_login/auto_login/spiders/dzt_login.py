# -*- coding: utf-8 -*-
import re
import scrapy
import datetime
import requests
from selenium import webdriver
from os.path import join, exists, dirname
import os


class RtSpider(scrapy.Spider):
    """
    店侦探-模拟登录爬虫脚本
    """
    name = "dzt_login"
    allowed_domains = ["https://login.taobao.com/"]
    start_urls = ['https://login.taobao.com/']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Start Driver ...")
        options = webdriver.ChromeOptions()

        execute_path = os.path.abspath(join(os.getcwd(), "chromedriver"))
        # options.add_argument('headless')
        options.add_argument('no-sandbox')
        options.add_argument('disable-gpu')
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('window-size=1200x600')
        self.driver = webdriver.Chrome(execute_path, chrome_options=options)

    def parse(self, response):
        """

        """
        # 1. 预留通用的参数，比如时间，
        # 2. 鉴权的请求接口可以设置cookie
        # 3. 最终数据写入到oss上

        self.logger.error("调试日志:" + response.url)
        self.driver.get("https://login.taobao.com/")

        print(self.driver.title)
        # yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)


