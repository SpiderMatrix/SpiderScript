# -*- coding: utf-8 -*-
from common.spider import RedisSpider
import requests
from urllib.request import unquote


class AutoBaseSpider(RedisSpider):
    """
    自动登录基类
    """

    def send_alert(self, message, account_name):
        """
        发送微信告警，提示回填短信验证码
        :param account_name:
        :param message
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

            alert_sns_url = alert_sns_url.decode("utf-8")+"?channel_id={}&platform_id={}&account_name={}".\
                format(self.channel_id, self.platform_id, account_name)
            alert_json = {
                "alert_id": 2,
                "alert_content": message,
                "url": unquote(alert_sns_url)
            }
            r = requests.post(url=alert_url, json=alert_json)
        except Exception as ex:
            import traceback
            self.logger.error("->send_alert , {}".format(traceback.format_exc()))