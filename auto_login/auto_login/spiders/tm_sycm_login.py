# -*- coding: utf-8 -*-
from ..spiders.tm_base_login import TmBaseSpider


class TBLoginProxySpider(TmBaseSpider):
    """
    生意参谋
    """
    name = "sycm_login"

    def __init__(self, *args, **kwargs):
        self.platform_id = "sycm"
        self.channel_id = "tm"
        super().__init__(*args, **kwargs)
