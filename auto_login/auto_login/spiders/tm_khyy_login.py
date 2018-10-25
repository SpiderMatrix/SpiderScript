# -*- coding: utf-8 -*-
from ..spiders.tm_base_login import TmBaseSpider


class KhyyLoginSpider(TmBaseSpider):
    """
    客户运营平台
    """
    name = "khyy_login"

    def __init__(self, *args, **kwargs):
        self.platform_id = "khyy"
        self.channel_id = "tm"
        super().__init__(*args, **kwargs)