# -*- coding: utf-8 -*-
from auto_login.settings import MINT_SN_BRAND_PROXY

from ..spiders.sn_base_login import SnBaseSpider


class BrandMPassportSpider(SnBaseSpider):
    """
    苏宁易道品牌商自动登录，选择一个合适的时间轮询获取cookie
    目前来看，有两种触发场景:
    1）按照调度表达式轮询触发
    2）失效由cookie需求方(脚本)触发
    """
    name = "ydbrand_login"
    start_urls = ['https://mpassport.suning.com/ids/login']
    account_cache = list()

    def __init__(self, *args, **kwargs):
        self.channel_id = "sn"
        self.platform_id = "ydbrand"
        self.remote_proxy = MINT_SN_BRAND_PROXY
        super().__init__(*args, **kwargs)



