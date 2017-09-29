# -*- coding: utf-8 -*-
import scrapy
import json
import re
import datetime
from PIL import Image
from scrapy.loader import ItemLoader
from ..items import ZhihuQuestionItem, ZhihuAnswerItem

try:
    import urlparse as parse
except:
    from urllib import parse


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_clos" \
                       "ed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_re" \
                       "ason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Cedit" \
                       "able_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdat" \
                       "ed_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%" \
                       "2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%" \
                       "5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={2}&limit={1}&s" \
                       "ort_by=default"
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/61.0.3163.100 Safari/537.36"
    }

    def parse(self, response):
        """
        深入优先
        提取出html页面中的所有url,并跟踪这些url进行进一步爬取
        如果提取的url中格式为/question/xxx就下载之后直接进入解析函数
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question相关页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers,
                                     meta={"question_id": question_id}, callback=self.parse_question)
            else:
                # 如果不是quest页面则直接进一步跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)  # 默认调用parse

    def parse_question(self, response):
        # 处理question页面,从页面中提取出具体的question item
        question_id = int(response.meta.get("question_id"))
        if "QuestionHeader-title" in response.text:
            # 处理新版本, 没有查看全部答案
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)  # 这里传的是实例
            item_loader.add_css("title", "h1.QuestionHeader-title::text")  # 多个,是一个list
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", int(response.meta.get("question_id")))
            item_loader.add_css("answer_num", "meta[itemprop='answerCount']::attr(content)")
            item_loader.add_css("comments_num", ".QuestionHeaderActions button::text")
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".Tag-content .Popover div::text")

            question_item = item_loader.load_item()
        else:
            # 处理老版本的item提取
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)  # 这里传的是实例
            # item_loader.add_css("title", ".zh-question-title h2 a::text")  # 多个,是一个list
            item_loader.add_xpath("title",
                                  "//*[@class='zh-question-title'/h2/a/text()|//*[@class='zh-question-title'/h2/spam/text()")  # 多个,是一个list
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            # item_loader.add_css("watch_user_num", "#zh-question-side-header-wrap::text")
            item_loader.add_css("watch_user_num",
                                "//*[@id='zh-question-side-header-wrap'/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

            question_item = item_loader.load_item()
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers,
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        # 处理answer
        ans_json = json.loads(response.text)
        is_end = ans_json.get("paging").get("is_end")
        total_answer = ans_json.get("paging").get("totals")
        next_url = ans_json["paging"]['next']

        # 提取具体的字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"].get("id")
            answer_item["content"] = answer["content"] or answer["excerpt"]
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()
            answer_item["crawl_update_time"] = datetime.datetime.now()
            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):  # 入口
        return [scrapy.Request("https://www.zhihu.com/#signin", headers=self.headers, callback=self.login)]  # 异步

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
        if not match_obj:
            return
        xsrf = match_obj.group(1)  # 这里视频中有括号
        post_data = {
            "_xsrf": xsrf,
            "phone_num": "number",
            "password": "password",
            "captcha": "",
        }
        import time
        t = str(int(time.time() * 1000))  # 将秒变成毫秒
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
