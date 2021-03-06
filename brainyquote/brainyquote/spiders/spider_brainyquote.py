# -*- coding: utf-8 -*-
import scrapy, urlparse, re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from brainyquote.items import BrainyquoteItem
from scrapy.shell import inspect_response

class SpiderBrainyquoteSpider(CrawlSpider):
    name            = 'spider_brainyquote'
    allowed_domains = ['brainyquote.com']
    start_url       = 'http://www.brainyquote.com'
    # start_urls      = ['http://www.brainyquote.com']

    rules = (
        Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
    )

    def start_requests(self):
        return [scrapy.Request(url=self.start_url, callback=self.first_quotes)]
    ## End start_requests

    def first_quotes(self, response):        
        for individual_author in response.xpath('//div[contains(@class, "bq_s")]//div[contains(@class, "bq_fl")]//div[contains(@class, "bqLn")]'):
            author_name      = individual_author.xpath('./a/text()').extract_first()
            author_link      = individual_author.xpath('./a/@href').extract_first()
            full_author_link = urlparse.urljoin(response.url, author_link)

            item                = BrainyquoteItem()
            item['author_name'] = author_name.lower().strip()

            yield scrapy.Request(url=full_author_link, callback=self.parse_author, meta={'item': item})
            # break
        ## End for loop individual author
    ## End first_quotes

    def parse_author(self, response):
        # We are going to search the author in amazon
        amazon_link = response.xpath('//a[contains(@href, "amazon.com")]/@href').extract_first()
        self.logger.info(amazon_link)

        for i, individual_quote in enumerate(response.xpath('//div[contains(@id, "quotesList")]/div')):
            # Define the item
            item = BrainyquoteItem(response.request.meta['item'])

            img_path   = individual_quote.xpath('./a/img/@src').extract_first()
            quote      = individual_quote.xpath('.//a[starts-with(@class, "qt")]/text()').extract_first()
            
            categories     = individual_quote.xpath('./div[contains(@class, "bq_q_nav")]//a/text()').extract()
            new_categories = []

            for individual_category in categories:
                individual_category = re.sub(r'\s+', '', individual_category)
                
                if individual_category:
                    new_categories.append(individual_category.lower().strip())
                ## End if individual_category
            ## End for loop categories

            full_img_path = None

            if img_path:                
                full_img_path = urlparse.urljoin(response.url, img_path)            

            item['quote_image']   = full_img_path
            item['quote']         = quote.lower().strip()
            item['amazon_source'] = amazon_link
            item['categories']    = new_categories
            yield item
        ## End for loop i

        yield None
    ## End parse_author