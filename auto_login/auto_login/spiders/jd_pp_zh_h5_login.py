# -*- coding: utf-8 -*-
import re
import scrapy
import datetime
import requests
from selenium import webdriver
from os.path import join
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from common.spider import RedisSpider
import time
import os
import json


class JDPpZhH5Spider(RedisSpider):
    """
    京东品牌纵横-模拟登录爬虫脚本
    """
    name = "jd_pp_zh_h5_login"
    start_urls = ['https://plogin.m.jd.com/user/login.action?appid=461&returnurl=http%3A%2F%2F'
                  'home.m.jd.com%2FmyJd%2Fhome.action&ipChanged=']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.args_cfg = self.crawl_redis.get("args#{}".format(self.name))
        if self.args_cfg: 
            self.args_cfg_json = json.loads(self.args_cfg.decode("utf-8"))
            # 支持外部设置cookie超时时间

        options = webdriver.ChromeOptions()
        execute_path = os.path.abspath(join(os.getcwd(), "chromedriver"))
        # options.add_argument('headless')
        options.add_argument('no-sandbox')
        options.add_argument('disable-gpu')
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('window-size=1200x600')
        options.add_argument('--proxy-server=http://127.0.0.1:9800')
        self.driver = webdriver.Chrome(execute_path, chrome_options=options)
        self.wait = WebDriverWait(self.driver, 100)
        self.platform_id = "ppzh"
        self.channel_id = "jd"

    def parse(self, response):
        """
        模拟自动化登录操作
        """
        self.logger.warn("京东品牌纵横自动登录开始")
        self.driver.get("https://plogin.m.jd.com/user/login.action?appid=461&returnurl="
                        "http%3A%2F%2Fhome.m.jd.com%2FmyJd%2Fhome.action&ipChanged=")

        relation_key = "admin#{}#{}".format(self.channel_id, self.platform_id)
        act_list_json = self.crawl_redis.get(relation_key)
        try:
            if act_list_json:
                account_list = json.loads(act_list_json.decode("utf-8"))
                m_cookies = list()
                # 同一数据多账号
                for account in account_list:
                    account_name = account["account_name"]

                    job_cookie_key = "job#{}".format(account_name)
                    job_cookie = self.crawl_redis.get(job_cookie_key)
                    if job_cookie:
                        # 如果设置过手工cookie，这里无需自动登录获取cookie
                        self.logger.warn("发现人工设置cookie，{}".format(job_cookie_key))
                        m_cookies.append({"shop_id": shop_id, "cookies": job_cookie})
                        continue

                    account_pwd = account["account_pwd"]
                    shop_id = account["shop_id"]

                    if account_name and account_pwd:
                        time.sleep(1)

                        login_name_input = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
                        login_name_input.send_keys(account_name)
                        pwd_input = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
                        pwd_input.send_keys(account_pwd)
                        login_btn = self.wait.until(EC.presence_of_element_located((By.ID, 'loginBtn')))
                        login_btn.click()

                        try_times = 5
                        while try_times:
                            time.sleep(3)
                            if "https://plogin.m.jd.com/user" in self.driver.current_url:
                                login_btn.click()
                            else:
                                break
                            try_times = try_times - 1

                        cookies = self.driver.get_cookies()
                        join_cookies_kvs = list()
                        for cookie_item in cookies:
                            join_cookies_kvs.append("{}={};".format(cookie_item["name"], cookie_item["value"]))
                        join_cookies = " ".join(join_cookies_kvs)
                        m_cookies.append({"shop_id": shop_id, "cookies": join_cookies})
                        self.logger.warn("成功获取{}-{}-{}".format(self.channel_id, self.platform_id, account_name))

                    else:
                        self.logger.warn("没有设置关联账号~~~~~")
                cookie_key = "cookie#{}#{}".format(self.channel_id, self.platform_id)
                self.crawl_redis.set(cookie_key, json.dumps(m_cookies))
        finally:
            self.driver.close()
            self.logger.warn("京东品牌纵横自动登录结束，关闭浏览器")

