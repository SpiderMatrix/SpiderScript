# -*- coding: utf-8 -*-


class RequestCounterMiddleware(object):
    """
    请求计数器
    """
    def __init__(self, crawler):
        super(RequestCounterMiddleware, self).__init__()
        self.crawl_redis = None
        self.proxy_cache = dict()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        # 统计请求数
        spider.request_cnt = spider.request_cnt + 1

