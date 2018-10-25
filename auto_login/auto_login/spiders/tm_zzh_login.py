# -*- coding: utf-8 -*-
from ..spiders.tm_base_login import TmBaseSpider


class ZzhLoginSpider(TmBaseSpider):
    """
    子账号平台
    """
    name = "zzh_login"

    def __init__(self, *args, **kwargs):
        self.platform_id = "zzh"
        self.channel_id = "tm"
        super().__init__(*args, **kwargs)
