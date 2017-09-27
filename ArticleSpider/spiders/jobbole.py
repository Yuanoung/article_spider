# -*- coding: utf-8 -*-
import scrapy
import re


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/112499/']

    def parse(self, response: object):
        title = response.xpath('//div[@class="entry-header"]//h1/text()').extract_first()
        create_date = response.xpath(
            '//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first().strip().replace("·", "").strip()
        praise_nums = int(response.xpath('//span[contains(@class, "vote-post-up")]/h10/text()').extract_first())
        fav_nums = response.xpath('//span[contains(@class, "bookmark-btn")]/text()').extract_first()
        match_re = re.match(".*(\d+).*", fav_nums)
        if match_re:
            fav_nums = match_re.group(1)

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first()
        match_re = re.match(".*(\d+).*", comment_nums)
        if match_re:
            comment_nums = match_re.group(1)

        content = response.xpath("//div[@class='entry']").extract_first()
        tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        tag_list = ", ".join([element for element in tag_list if not element.strip().endswith("评论")])
        pass
