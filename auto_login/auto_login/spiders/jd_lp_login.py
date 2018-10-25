# -*- coding: utf-8 -*-
from ..spiders.jd_base_login import JdBaseSpider


class JDLpSpider(JdBaseSpider):
    """
    京东罗盘-模拟登录爬虫脚本
    """
    name = "jdlp_login"
    start_urls = ['https://passport.jd.com/new/login.aspx?ReturnUrl='
                  'https://pop.jd.com/userLoginAction.action?time=1490252084798']

    def __init__(self, *args, **kwargs):
        self.platform_id = "jdlp"
        self.channel_id = "jd"
        self.login_url = "https://passport.jd.com/uc/login?" \
                         "ReturnUrl=http%3A%2F%2Ftvdc.jd.com/vdc/item/realTime/overview.html"
        self.return_url = 'https://tvdc.jd.com/vdc/item/realTime/overview.html'
        super().__init__(*args, **kwargs)
