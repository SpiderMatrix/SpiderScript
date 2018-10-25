# -*- coding: utf-8 -*-
from ..spiders.jd_base_login import JdBaseSpider


class JDPpZhSpider(JdBaseSpider):
    """
    京东品牌纵横-模拟登录爬虫脚本
    """
    name = "ppzh_login"
    start_urls = ['https://passport.jd.com/new/login.aspx?ReturnUrl='
                  'https://pop.jd.com/userLoginAction.action?time=1490252084798']

    def __init__(self, *args, **kwargs):
        self.platform_id = "ppzh"
        self.channel_id = "jd"
        self.login_url = "https://passport.jd.com/uc/login?" \
                         "ReturnUrl=http%3A%2F%2Fppzh.jd.com%2Fbrand%2FrealTime%2FrealTop.html"
        self.login_success_url = "ppzh.jd.com"
        super().__init__(*args, **kwargs)
