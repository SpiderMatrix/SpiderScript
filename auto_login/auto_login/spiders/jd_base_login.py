# -*- coding: utf-8 -*-
import re
import base64
import hashlib
import math
import requests
from selenium import webdriver
from os.path import join
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from common.spider import RedisSpider
import time
import os
import cv2
import numpy as np
import random
import json
from auto_login.settings import MINT_JD_PROXY, judge_driver_path, DEV, CHROME_DOCKER_URL,IMG_PATH


class JdBaseSpider(RedisSpider):
    """
    京东品牌纵横-模拟登录爬虫脚本
    """
    start_urls = ['https://passport.jd.com/new/login.aspx?ReturnUrl='
                  'https://pop.jd.com/userLoginAction.action?time=1490252084798']

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.args_cfg = self.crawl_redis.get("args#{}".format(self.name))
        if self.args_cfg:
            self.args_cfg_json = json.loads(self.args_cfg.decode("utf-8"))
            # 支持外部设置cookie超时时间

        options = webdriver.ChromeOptions()
        execute_path = judge_driver_path()

        options.add_argument('no-sandbox')
        options.add_argument('disable-gpu')
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('window-size=1200x600')

        self.account_name = ''
        if 'platform_id' in kwargs and 'account_name' in kwargs:
            self.platform_id = kwargs["platform_id"]
            self.account_name = kwargs["account_name"]

        # options.add_argument('--proxy-server={}'.format(MINT_JD_PROXY))
        if DEV:
            self.driver = webdriver.Chrome(execute_path, chrome_options=options)
        else:
            options.add_argument('headless')

            desired_capabilities = webdriver.DesiredCapabilities.CHROME.copy()
            self.driver = webdriver.Remote(
                command_executor=CHROME_DOCKER_URL,
                desired_capabilities=webdriver.DesiredCapabilities.CHROME, options=options)

        self.wait = WebDriverWait(self.driver, 100)

    def parse(self, response):
        """
        模拟自动化登录操作
        """
        self.logger.warn("京东[{}]自动登录开始".format(self.platform_id))

        relation_key = "admin#{}#{}".format(self.channel_id, self.platform_id)
        act_list_json = self.crawl_redis.get(relation_key)
        if not act_list_json:
            self.logger.warn("京东[{}]自动登录没有合适的账号".format(self.platform_id))
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

        try:
            # 同一数据多账号
            for account in account_list:
                account_name = account["account_name"]
                shop_id = account["shop_id"]
                job_cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                job_cookie = self.crawl_redis.get(job_cookie_key)
                if job_cookie:
                    self.logger.warn("该cookie[{}]存在，不做自动登录".format(account_name))
                    # continue

                account_pwd = account["account_pwd"]
                if account_name and account_pwd:

                    mock_result = self.mock_slider(account_name, account_pwd)
                    if mock_result:
                        cookies = self.driver.get_cookies()
                        join_cookies_kvs = list()
                        for cookie_item in cookies:
                            join_cookies_kvs.append("{}={};".format(cookie_item["name"], cookie_item["value"]))

                        # 判断cookie是否有效
                        join_cookies = " ".join(join_cookies_kvs)
                        cookie_key = "cookie#{}#{}#{}".format(self.channel_id, self.platform_id, account_name)
                        self.crawl_redis.set(cookie_key, join_cookies)
                        self.logger.warn("成功获取{}-{}-{}".format(self.channel_id, self.platform_id, account_name))
                else:
                    self.logger.warn("没有设置关联账号~~~~~")

        except Exception as ex:
            import traceback
            self.logger.warn("->occur a error,", ex)
            self.logger.warn("->occur a error = {}".format(traceback.format_exc()))

        finally:
            self.driver.close()
            self.logger.warn("京东{}自动登录结束，关闭浏览器".format(self.platform_id))

    def mock_slider(self, account_name, account_pwd):

        self.driver.get(self.login_url)
        time.sleep(1)

        # if self.platform_id == "jdsz":
        #     login_btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-btn')))
        #     login_btn.click()
        #     time.sleep(3)
        #     self.driver.switch_to.frame("dialogIframe")

        pc_login = self.driver.find_element_by_partial_link_text('账户登录')
        pc_login.click()

        login_name_input = self.wait.until(EC.presence_of_element_located((By.ID, 'loginname')))
        login_name_input.clear()
        login_name_input.send_keys(account_name)
        pwd_input = self.wait.until(EC.presence_of_element_located((By.ID, 'nloginpwd')))
        pwd_input.clear()
        pwd_input.send_keys(account_pwd)
        login_btn = self.wait.until(EC.presence_of_element_located((By.ID, 'loginsubmit')))
        login_btn.click()

        login_submit_elm = self.wait.until(EC.presence_of_element_located((By.ID, 'JDJRV-wrap-loginsubmit')))
        if login_submit_elm:
            sha_md5 = hash_md5(account_name)
            path = os.path.abspath(join(os.getcwd(), "auto_login/snap_shoot"))
            # path = IMG_PATH
            bkg_file = os.path.join(path, "%s.png" % sha_md5)
            block_file = os.path.join(path, "block_%s.png" % sha_md5)
            retry = 0
            while login_submit_elm and login_submit_elm.is_displayed():
                retry += 1
                if retry > 10:
                    return
                time.sleep(2)
                big_img_elm = self.driver.find_element_by_css_selector("#JDJRV-wrap-loginsubmit .JDJRV-bigimg img")
                small_img_elm = self.driver.find_element_by_css_selector("#JDJRV-wrap-loginsubmit .JDJRV-smallimg img")
                # 获取拼图图片
                save_image(big_img_elm.get_attribute("src"), bkg_file)
                save_image(small_img_elm.get_attribute("src"), block_file)
                # 分析拼图图片位置
                x, y = analysis_loction(bkg_file, block_file)
                _x = math.floor(x * 278 / 360)
                # 获取移动轨迹
                tracks = get_track_v2(_x)
                # 按照轨迹拖动，完成验证
                button = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'JDJRV-slide-btn')))
                ActionChains(self.driver).click_and_hold(button).perform()

                for track in tracks:
                    ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()
                time.sleep(random.randint(1, 2))
                ActionChains(self.driver).release().perform()

                time.sleep(15)
                # 检查是否验证成功  获取登陆标签

                if self.login_url not in self.driver.current_url:
                    return True

            os.remove(bkg_file)
            os.remove(block_file)


def save_image(src, file_path):
    """
    保存图片
    :param src:
    :param file_path:
    """
    if str(src).startswith('data:image'):
        save_base64_to_image(src, file_path)
    else:
        req = requests.get(src)
        with open(file_path, 'wb') as f:
            f.write(req.content)
            f.close()


def save_base64_to_image(data, file_path):
    """
    base64转图片文件
    :param data:
    :param file_path:
    :return:
    """
    image_data = base64.b64decode(data.split('base64,')[1])
    with open(file_path, 'wb') as f:
        f.write(image_data)
        f.close()


def analysis_loction(bkg_file, block_file):
    """
    解析图片位置
    :param bkg_file:
    :param block_file:
    :return:
    """
    bkg_image = cv2.imread(bkg_file, 0)  # 读取背景图片
    block_image = cv2.imread(block_file, 0)  # 读取块图片
    temp_image = abs(255 - block_image)
    # cv2.Sobel(temp_image, temp_image, 1, 0, 3)
    # cv2.Sobel(bkg_image, bkg_image, 1, 0, 3)
    result = cv2.matchTemplate(temp_image, bkg_image, cv2.TM_CCOEFF_NORMED)
    y, x = np.unravel_index(result.argmax(), result.shape)
    return x, y


def detect_coordinate(bkg_file, block_file):
    """
    解析图片位置
    :param bkg_file:
    :param block_file:
    :return:
    """
    bkg_image = cv2.imread(bkg_file, 0)  # 读取背景图片

    img_gray = cv2.cvtColor(bkg_image, cv2.COLOR_BGR2GRAY)

    template_image = cv2.imread(block_file, 0)  # 读取块图片
    result = cv2.matchTemplate(img_gray, template_image, cv2.TM_CCOEFF_NORMED)
    y, x = np.unravel_index(result.argmax(), result.shape)
    return x, y


def get_tracks(distance):
    """
    拿到移动轨迹，模仿人的滑动行为，先匀加速后匀减速
    匀变速运动基本公式：
    ①v=v0+at
    ②s=v0t+½at²
    ③v²-v0²=2as
    :param distance: 需要移动的距离
    :return: 存放每0.3秒移动的距离
    """
    v = 0
    t = 0.3
    tracks = []
    current = 0
    extra_distance = random.randint(-10, 20)  # 额外距离
    _distance = distance + extra_distance
    mid = _distance * 4 / 5

    while current < _distance:
        if current < mid:
            # 加速度越小，单位时间的位移越小,模拟的轨迹就越多越详细
            a = 2
        else:
            a = -3
        v0 = v
        s = round(v0 * t + 0.5 * a * (t ** 2))
        current += s
        tracks.append(s)
        v = v0 + a * t

    while current != distance:
        s = 0
        _distance = abs(distance - current)
        if _distance > 10:
            _distance = 10
        elif _distance > 5:
            _distance = 5
        if distance > current:
            s = random.randint(0, _distance)
        else:
            s = - random.randint(0, _distance)
        current += s
        tracks.append(s)
    return tracks


def get_track_v2(distance):
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


def hash_md5(data, encoding='utf-8'):
    """
    md5 加密
    :param data: 数据
    :param encoding:  字符编码
    :return:
    """
    if isinstance(data, str):
        data = data.encode(encoding=encoding)
    hash = hashlib.md5()
    hash.update(data)
    v = hash.hexdigest()
    return v
