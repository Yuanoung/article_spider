# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5


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
        post_nodes = response.xpath("//*[@id='archive']//div[@class='post-thumb']/a")
        for post_node in post_nodes:
            image_url = post_node.xpath("./img/@src").extract_first("")
            post_url = post_node.xpath("./@href").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)

        # 提取下一页的url
        next_urls = response.xpath("//a[contains(@class, 'next')]/@href").extract_first("")
        if next_urls:
            yield Request(url=parse.urljoin(response.url, next_urls), callback=self.parse)

    def parse_detail(self, response):
        # 第二步
        # article_item = JobBoleArticleItem()
        #
        # front_image_url = response.meta.get("front_image_url", "")  # 文章封面图
        # title = response.xpath('//div[@class="entry-header"]//h1/text()').extract_first()
        # create_date = response.xpath(
        #     '//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first().strip().replace("·", "").strip()
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()
        # praise_nums = int(response.xpath('//span[contains(@class, "vote-post-up")]/h10/text()').extract_first())
        # fav_nums = response.xpath('//span[contains(@class, "bookmark-btn")]/text()').extract_first()
        # match_re = re.match(".*(\d+).*", fav_nums)
        # if match_re:
        #     fav_nums = int(match_re.group(1))
        # else:
        #     fav_nums = 0
        #
        # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first()
        # match_re = re.match(".*(\d+).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        #
        # content = response.xpath("//div[@class='entry']").extract_first()
        # tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # tags = ", ".join([element for element in tag_list if not element.strip().endswith("评论")])
        #
        # article_item.update({
        #     "title": title,
        #     "url": response.url,
        #     "url_object_id": get_md5(response.url),
        #     "create_date": create_date,
        #     "front_image_url": [front_image_url],
        #     "praise_nums": praise_nums,
        #     "comment_nums": comment_nums,
        #     "fav_nums": fav_nums,
        #     "tags": tags,
        #     "content": content,
        # })

        # 通过item loader 加载item
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_xpath("title", '//div[@class="entry-header"]//h1/text()')
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_xpath("create_date", '//p[@class="entry-meta-hide-on-mobile"]/text()')
        item_loader.add_value("front_image_url", [response.meta.get("front_image_url", "")])
        item_loader.add_xpath("praise_nums", '//span[contains(@class, "vote-post-up")]/h10/text()')
        item_loader.add_xpath("comment_nums", "//a[@href='#article-comment']/span/text()")
        item_loader.add_xpath("fav_nums", '//span[contains(@class, "bookmark-btn")]/text()')
        item_loader.add_xpath("tags", '//p[@class="entry-meta-hide-on-mobile"]/a/text()')
        item_loader.add_xpath("content", "//div[@class='entry']")

        article_item = item_loader.load_item()  # 将规则进行解析
        yield article_item
