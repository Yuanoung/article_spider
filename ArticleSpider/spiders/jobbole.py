# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from urllib import parse


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response: object):
        """
        1. 获取文章列表中的文章url并交给解析函数进行具体字段的解析
        2. 获取下一页的url并交给scrapy进行下载,下载完成后交给parse
        """

        # 第一步
        post_urls = response.css("#archive .floated-thumb .post-thumb a::attr(href)").extract()
        for post_url in post_urls:
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse_detail)

        # 提取下一页的url
            next_urls = response.css(".next.page-numbers::attr(href)").extract_first("")
            if next_urls:
                yield Request(url=parse.urljoin(response.url, next_urls), callback=self.parse)

    def parse_detail(self, response):
        # 第二步
        title = response.xpath('//div[@class="entry-header"]//h1/text()').extract_first()
        create_date = response.xpath(
            '//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first().strip().replace("·", "").strip()
        praise_nums = int(response.xpath('//span[contains(@class, "vote-post-up")]/h10/text()').extract_first())
        fav_nums = response.xpath('//span[contains(@class, "bookmark-btn")]/text()').extract_first()
        match_re = re.match(".*(\d+).*", fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first()
        match_re = re.match(".*(\d+).*", comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0

        content = response.xpath("//div[@class='entry']").extract_first()
        tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        tag_list = ", ".join([element for element in tag_list if not element.strip().endswith("评论")])
        pass
