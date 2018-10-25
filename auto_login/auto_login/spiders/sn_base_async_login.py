# -*- coding: utf-8 -*-
import re
import scrapy
import datetime
import requests
import redis
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from ..spiders.auto_spider import AutoBaseSpider
from selenium.webdriver import ActionChains
from auto_login.settings import MINT_SN_SHOP_PROXY,judge_driver_path,DEV,CHROME_DOCKER_URL,MINT_SN_BRAND_PROXY
import json
import random


class SnBaseSpider(AutoBaseSpider):
    """
    苏宁易道品牌商自动登录，选择一个合适的时间轮询获取cookie
    目前来看，有两种触发场景:
    1）按照调度表达式轮询触发
    2）失效由cookie需求方(脚本)触发
    """
    start_urls = ['https://mpassport.suning.com/ids/login']
    account_cache = list()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.args_cfg = self.crawl_redis.get("args#{}".format(self.name))
        if self.args_cfg:
            self.args_cfg_json = json.loads(self.args_cfg.decode("utf-8"))
            # 这里获取账号与平台，渠道关联关系

        options = webdriver.ChromeOptions()
        execute_path = judge_driver_path()
        # options.add_argument('headless')
        options.add_argument('no-sandbox')
        options.add_argument('disable-gpu')
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('window-size=1200x600')

        self.account_name = ''
        if 'platform_id' in kwargs and 'account_name' in kwargs:
            self.platform_id = kwargs["platform_id"]
            self.account_name = kwargs["account_name"]

        options.add_argument('--proxy-server={}'.format(MINT_SN_PROXY))
        if DEV:
            self.driver = webdriver.Chrome(execute_path, chrome_options=options)
        else:
            options.add_argument('headless')
            self.driver = webdriver.Remote(
                command_executor=CHROME_DOCKER_URL,
                desired_capabilities=webdriver.DesiredCapabilities.CHROME, options=options)

        self.driver = webdriver.Chrome(execute_path, chrome_options=options)
        self.wait = WebDriverWait(self.driver, 100)

    def start_requests(self):

        relation_key = "admin#{}#{}".format(self.channel_id, self.platform_id)
        act_list_json = self.crawl_redis.get(relation_key)
        if not act_list_json:
            self.logger.warn("易道自动登录没有合适的账号")
            return

        account_list = json.loads(act_list_json.decode("utf-8"))
        # 以账号维度来自动登录，而非店铺
        if self.account_name:
            # 指定账号登录
            for account in account_list:
                account_name = account["account_name"]
                if account_name == self.account_name:
                    account_list.clear()
                    account_list.append(account)
                    break

        for account in account_list:
            if "[不要猜]@163.com" == account["account_name"]:
                yield scrapy.Request("https://mpassport.suning.com/ids/login?name={}".format(account["account_name"]),
                                     meta=account, callback=self.process_account_login, dont_filter=True)

    def process_account_login(self, response):
        """

        """

        try:
            self.logger.info("苏宁易道自动登录开始")
            self.driver.set_window_size(width=1400, height=800)
            self.driver.get("https://www.suning.com/")
            # self.remain_cookies()

            self.driver.get("https://mpassport.suning.com/ids/login?service=https%3A%2F%2Fedao.suning.com%2Fauth%3"
                            "FtargetUrl%3Dhttps%253A%252F%252Fedao.suning.com%252F&loginTheme=sdas")

            self.driver.refresh()

            account = response.meta

            account_name = account["account_name"]
            shop_id = account["shop_id"]
            account_pwd = account["account_pwd"]
            if account_name in self.account_cache:
                self.logger.warn("该账号已经自动登录且cookie凭证有效！")
                return

            job_cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
            job_cookie = self.crawl_redis.get(job_cookie_key)
            if job_cookie:
                # 如果设置过手工cookie，这里无需自动登录获取cookie
                self.logger.warn("该cookie[{}]存在，不做自动登录".format(account_name))
                # cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                # self.crawl_redis.set(cookie_key, job_cookie)
                # continue

            if not account_name or not account_pwd:
                self.logger.warn("账号非法或者为空")
                return

            time.sleep(1)
            self.account_cache.append(account_name)

            login_name_input = self.wait.until(EC.presence_of_element_located((By.ID, 'userName')))
            login_name_input.clear()
            login_name_input.send_keys(account_name)

            pwd_input = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
            pwd_input.send_keys(account_pwd)

            entry_ctrl = self.wait.until(EC.presence_of_element_located((By.ID, 'siller')))
            attr = entry_ctrl.get_attribute("style")

            for i in range(5):
                if "display: block;" in attr:
                    side_bar = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dt_child_content_knob')))
                    ActionChains(self.driver).click_and_hold(side_bar).perform()
                    # 模拟移动滑块
                    tracks = self.get_track(302)
                    while tracks:
                        x = random.choice(tracks)
                        ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
                        tracks.remove(x)
                    time.sleep(0.5)
                    ActionChains(self.driver).release().perform()

                login_btn = self.wait.until(EC.presence_of_element_located((By.ID, 'loginButton')))
                login_btn.click()
                time.sleep(2)
                if "https://mpassport.suning.com/ids/login" not in self.driver.current_url:
                    break

            time.sleep(300)

            # 判断是否需要再次进行手机号码验证
            redirect_url = self.driver.current_url
            if "https://masc.suning.com/masc/" in redirect_url:
                active_code = self.wait.until(EC.presence_of_element_located((By.ID, 'getPhoneValCode')))
                active_code.click()

                message = "请点击链接输入手机验证码，有效期5分钟，（苏宁易道品牌商，登录账号:{}）".format(account_name)
                self.send_alert(message, account_name)

                # 这里定义最多等待5分钟
                sleep_max = 10*5*60
                while sleep_max:
                    # 循环等待
                    sleep_max = sleep_max - 10
                    time.sleep(1)
                    sns_code = self.crawl_redis.get("code#{}#{}#{}".format(self.channel_id, self.platform_id,
                                                                           self.account_name))
                    if sns_code:
                        v_code = self.wait.until(EC.presence_of_element_located((By.ID, 'validateCode')))
                        v_code.send_keys(sns_code)
                        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'activeOrg'))).click()
                        break

            cookies = self.driver.get_cookies()
            if cookies:
                join_cookies_kvs = list()
                for cookie_item in cookies:
                    join_cookies_kvs.append("{}={};".format(cookie_item["name"], cookie_item["value"]))
                join_cookies = " ".join(join_cookies_kvs)
                cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                self.crawl_redis.set(cookie_key, join_cookies)
        except Exception as ex:
            import traceback
            self.logger.error("-> occur a error", ex)
            self.logger.error("-> occur a error, error = {}".format(traceback.format_exc()))
        finally:
            self.driver.close()

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 2
            else:
                # 加速度为负3
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def remain_cookies(self):
        job_cookie = "_portoData=766ebd00-178a-49ab-8b72-2031ab1e8449; _fp_t_=123,1539244293286; _snmc=1; _snsr=direct%7Cdirect%7C%7C%7C; _snvd=1533801932921qyEbbEMOkkz; route=ef60b7aa446005b442e9b019f94f1118; _device_session_id=p_9e4934a4-1b83-4c57-b212-b25bafb88d3f; _cp_dt=d9972fc4-c7d9-4b95-8500-45f981e71787-75762; idsLoginUserIdLastTime=[不要猜]%40163.com; custno=6221302998; sop_user_biz=C; sopSecureToken=4D49AC71C9063FEC5C80C4BD9EBFD60A; _snma=1%7C153924040241298778%7C1539240402412%7C1539243254338%7C1539243337292%7C12%7C1; _snmp=153924333718090966; _snmb=153924040242084846%7C1539243337356%7C1539243337300%7C12"
        job_cookies = job_cookie.split("; ")
        for jc in job_cookies:
            name = jc.split("=")[0]
            value = jc.split("=")[1]
            self.driver.add_cookie({'name': name, 'value': value})



