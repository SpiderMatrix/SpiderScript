# -*- coding: utf-8 -*-
import json
import time
from urllib.request import unquote

import requests
from auto_login.settings import MINT_TB_PROXY, judge_driver_path, DEV, CHROME_DOCKER_URL
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.spider import RedisSpider


class TmBaseSpider(RedisSpider):
    """
    淘宝-代理伪造自动登录爬虫脚本
    """
    allowed_domains = ["taobao.com"]
    start_urls = ['https://www.taobao.com/']
    account_cache = list()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        options = webdriver.ChromeOptions()

        options.add_argument('no-sandbox')
        options.add_argument('disable-gpu')
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('window-size=1800x700')

        self.account_name = ''
        if 'platform_id' in kwargs and 'account_name' in kwargs:
            self.platform_id = kwargs["platform_id"]
            self.account_name = kwargs["account_name"]

        execute_path = judge_driver_path()
        options.add_argument('--proxy-server={}'.format(MINT_TB_PROXY))

        lock = self.dlm.lock("{}#{}".format(self.platform_id, self.account_name), 60000)
        if not lock:
            self.logger.warn("该账号{}正在登陆！".format(self.account_name))
            return

        if DEV:
            self.driver = webdriver.Chrome(execute_path, chrome_options=options)
        else:
            options.add_argument('headless')
            self.driver = webdriver.Remote(
                command_executor=CHROME_DOCKER_URL,
                desired_capabilities=DesiredCapabilities.CHROME, options=options)
        self.wait = WebDriverWait(self.driver, 100)

    def parse(self, response):
        """

        """
        try:
            relation_key = "admin#{}#{}".format(self.channel_id, self.platform_id)
            act_list_json = self.crawl_redis.get(relation_key)
            if not act_list_json:
                self.logger.warn("请设置账号关联关系！")
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
                account_name = account["account_name"]
                if account_name in self.account_cache:
                    self.logger.warn("该账号已经自动登录且cookie凭证有效！")
                    continue

                self.account_cache.append(account_name)
                account_pwd = account["account_pwd"]
                shop_id = account["shop_id"]

                job_cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                job_cookie = self.crawl_redis.get(job_cookie_key)
                if job_cookie:
                    # 如果设置过手工cookie，这里无需自动登录获取cookie
                    self.logger.warn("该cookie[{}]存在，不做自动登录".format(account_name))
                    # cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                    # self.crawl_redis.set(cookie_key, job_cookie)
                    # continue

                if not account_name or not account_pwd:
                    self.logger.warn("账号或者密码为空")
                    continue

                self.driver.set_window_size(width=1500, height=800)
                self.driver.get("https://www.taobao.com/")
                go_login = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'h')))
                go_login.click()
                pc_login = self.wait.until(EC.presence_of_element_located((By.ID, 'J_Quick2Static')))
                pc_login.click()
                username_input = self.driver.find_element_by_id('TPL_username_1')
                time.sleep(2)
                password_input = self.driver.find_element_by_id('TPL_password_1')
                username_input.send_keys(account_name)
                time.sleep(2)
                password_input.send_keys(account_pwd)
                submit_btn = self.wait.until(EC.presence_of_element_located((By.ID, 'J_SubmitStatic')))
                submit_btn.click()

                time.sleep(2)
                self.driver.get('https://sycm.taobao.com/portal/home.htm')
                judge_url = self.driver.current_url

                if "member/login_unusual.htm" in judge_url:
                    # 发送验证码通知
                    self.send_alert(account_name)

                    # 点击发送验证码
                    get_btn = self.wait.until(EC.presence_of_element_located((By.ID, 'J_GetCode')))
                    get_btn.click()

                    time_counter = 100
                    while time_counter:
                        time.sleep(3)
                        time_counter = time_counter - 1
                        sns_code = self.crawl_redis.get("code#{}#{}#{}".format(self.channel_id,
                                                                               self.platform_id,
                                                                               account_name))
                        if sns_code:
                            self.crawl_redis.delete(["code#{}#{}#{}".format(self.channel_id,
                                                                            self.platform_id,
                                                                            account_name)])
                            code_input = self.wait.until(EC.presence_of_element_located((By.ID,
                                                                                         'J_Phone_Checkcode')))
                            code_input.send_keys(sns_code)
                            submit_btn_2 = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                                           'J_Submit')))
                            submit_btn_2.click()

                cookies = self.driver.get_cookies()

                join_cookies_kvs = list()
                for cookie_item in cookies:
                    join_cookies_kvs.append("{}={};".format(cookie_item["name"], cookie_item["value"]))

                # 简单判断cookie是否有效
                join_cookies = " ".join(join_cookies_kvs)
                cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                self.crawl_redis.set(cookie_key, join_cookies)
        except Exception as ex:
            self.logger.warn("代理淘宝账号自动登录异常", ex)
        finally:
            self.logger.warn("代理淘宝账号自动登录，关闭浏览器")
            self.driver.close()
            # if self.account_name:
            #     self.dlm.unlock(lock)

    def send_alert(self, account_name):
        """
        发送微信告警，提示回填短信验证码
        :param account_name:
        :return:
        """
        try:
            alert_url = self.crawl_redis.get("cfg#alert_url")
            alert_sns_url = self.crawl_redis.get("cfg#alert_sns_url")
            if not alert_url:
                self.logger.warn("请先配置告警url!!!")
                return

            if alert_url:
                alert_url = alert_url.decode("utf-8")

            alert_content = '请点击链接输入手机验证码，有效期5分钟'.format(account_name)
            alert_sns_url = alert_sns_url + "?channel_id={}&platform_id={}&account_name={}". \
                format(self.channel_id, self.platform_id, account_name)
            alert_json = {
                "alert_id": 3,
                "alert_content": alert_content,
                "url": unquote(alert_sns_url)
            }
            r = requests.post(url=alert_url, json=alert_json)
        except Exception as ex:
            import traceback
            self.logger.error("->send_alert , {}".format(traceback.format_exc()))
