# -*- coding: utf-8 -*-
from ..spiders.jd_base_login import JdBaseSpider


class JDKfSpider(JdBaseSpider):
    """
    京东-模拟登录爬虫脚本
    """
    name = "jdkf_login"
    start_urls = ['https://passport.jd.com/new/login.aspx?ReturnUrl='
                  'https://pop.jd.com/userLoginAction.action?time=1490252084798']

    def __init__(self, *args, **kwargs):
        self.platform_id = "jdkf"
        self.channel_id = "jd"
        self.login_url = "https://passport.jd.com/uc/login?" \
                         "ReturnUrl=http%3A%2F%2Fkf.jd.com/"
        self.return_url = 'http://kf.jd.com/'
        super().__init__(*args, **kwargs)
