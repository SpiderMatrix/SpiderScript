# -*- coding: utf-8 -*-
from auto_login.settings import MINT_SN_SHOP_PROXY

from ..spiders.sn_base_login import SnBaseSpider


class ShopMPassportSpider(SnBaseSpider):
    """
    苏宁易道店铺版
    """
    name = "ydshop_login"
    start_urls = ['https://mpassport.suning.com/ids/login']
    account_cache = list()

    def __init__(self, *args, **kwargs):
        self.channel_id = "sn"
        self.platform_id = "ydshop"
        self.remote_proxy = MINT_SN_SHOP_PROXY
        super().__init__(*args, **kwargs)



