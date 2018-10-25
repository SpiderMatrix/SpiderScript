# -*- coding: utf-8 -*-

from ..spiders.jd_base_login import JdBaseSpider


class JDSzSpider(JdBaseSpider):
    """
    京东商智-模拟登录爬虫脚本
    """
    name = "jdsz_login"
    start_urls = ['https://sz.jd.com/login.html?ReturnUrl=http://sz.jd.com/index.html']

    def __init__(self, *args, **kwargs):
        self.platform_id = "jdsz"
        self.channel_id = "jd"
        self.login_url = "https://passport.jd.com/uc/login?" \
                         "ReturnUrl=http%3A%2F%2Fsz.jd.com/index.html"
        self.login_success_url = "sz.jd.com/index.html"
        super().__init__(*args, **kwargs)



