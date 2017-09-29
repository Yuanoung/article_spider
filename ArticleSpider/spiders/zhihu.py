# -*- coding: utf-8 -*-
import scrapy
import json
import re
from PIL import Image


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/61.0.3163.100 Safari/537.36"
    }

    def parse(self, response):
        pass

    def start_requests(self):  # 入口
        return [scrapy.Request("https://www.zhihu.com/#signin", headers=self.headers, callback=self.login)]  # 异步

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
        if not match_obj:
            return
        xsrf = match_obj.group(1)  # 这里视频中有括号
        post_data = {
            "_xsrf": xsrf,
            "phone_num": "your phone numbers",
            "password": "password",
            "captcha": "",
        }
        import time
        t = str(int(time.time() * 1000))
        captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
        yield scrapy.Request(captcha_url, headers=self.headers,
                             meta={"post_data": post_data}, callback=self.login_after_captcha)  # 回调函数cookie是相同的

    def login_after_captcha(self, response):
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)  # 不是在content中,

        try:
            im = Image.open("captcha.jpg")
            im.show()
            im.close()
        except:
            pass
        captcha = input("输入验证码:\n>>> ")

        post_data = response.meta.get("post_data", {})
        post_data["captcha"] = captcha
        return [scrapy.FormRequest(
            url="https://www.zhihu.com/login/phone_num",
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login,
        )]

    def check_login(self, response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if text_json.get("msg") == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)
