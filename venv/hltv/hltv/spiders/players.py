import scrapy
from scrapy.spiders import Spider
from scrapy.selector import Selector
from hltv.items import TeamsItem
from scrapy.http import HtmlResponse
from scrapy import Request
#from scrapy.selector import HtmlXPathSelector
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from scrapy.loader import ItemLoader

from datetime import datetime
#from dateutil.parser import parse
import re
import unicodedata

import time

import json


from elasticsearch import Elasticsearch



class Players(scrapy.Spider):
    name = "players"
    allowed_domains = ["hltv.org/"]
    start_urls = ["https://www.hltv.org/stats/players"]

    #players = []

    es = Elasticsearch(['localhost'],
                       scheme="http",
                       port=9200)

    def parse(self, response):
        print('main_url: ' + response.url)

        playersStatslinks = response.xpath(".//tr/td[@class='playerCol ']/a/@href").extract()
        i = 0  # counter pages entries
        data = {}



        for playersStats in playersStatslinks:
            item = data
            #item = TeamsItem()


            statspage = "https://www.hltv.org"+ playersStats
            print(statspage)
            item["player_stats_url"] = statspage

            item["teams_played"] = response.xpath(".//div[@class='stats-section']/table[@class='stats-table player-ratings-table']/tbody/tr["+str(i+1)+"]/td[@class='teamCol']//img/@title").extract()

            item["teamurl"] = []
            for link in response.xpath(".//div[@class='stats-section']/table[@class='stats-table player-ratings-table']/tbody/tr["+str(i+1)+"]/td[@class='teamCol']//@href").extract():
                item["teamurl"].append("https://www.hltv.org" + link)

            nick_player = response.xpath(".//tr/td[@class='playerCol ']/a/text()").extract()[i]
            print (nick_player)

            item["nick_player"] = response.xpath(".//tr/td[@class='playerCol ']/a/text()").extract()[i]

            #item["name_team"] = response.xpath(".//tr/td[@class='teamCol']//@alt").extract()[i]
            item["nationality"] = response.xpath(".//tr/td[@class='playerCol ']/img/@title").extract()[i]
            item["last_updated"] = str(datetime.now())







            #callback to event page
            # request = scrapy.Request(url=statspage,
            #                          callback=self.parse_statsPlayerPage,
            #                          errback=self.errback_httpbin,
            #                          dont_filter=True)
            # request.meta['item'] = item

            i = i + 1

            res = self.es.index(index="csgo", doc_type='players', id=nick_player, body=json.dumps(item))
            print(res['result'])

            yield item


#catch exceptions in request processing
    def parse_httpbin(self, response):
        self.logger.info('Got successful response from {}'.format(response.url))
        # do something useful here...

    def errback_httpbin(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
