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
from elasticsearch_dsl import Search



class StatsPlayers(scrapy.Spider):
    es = Elasticsearch(['localhost'],
                       scheme="http",
                       port=9200)
    statsPage = []
    doc = {
        'size': 10000,
        'query': {
            'match_all': {}
        }
    }
    res = es.search(index="csgo", body=doc, scroll='1m')

    for hit in res['hits']['hits']:
        player_stats_url = hit['_source']['player_stats_url']
        try:
            print(hit['_source']['player_stats_url'])
            print(hit['_source']['stats'])

        except Exception as e:
            print (e)
            statsPage.append(player_stats_url)

    print(statsPage)
        # start_urls.append(player_stats_url)




    name = "statsPlayers"
    allowed_domains = ["hltv.org/"]
    start_urls = statsPage #["https://www.hltv.org/stats/players/8521/daps"] #

    #players = []



    def parse(self, response):


        print('main_url: ' + response.url)

        item = {}
        #item = TeamsItem()
        playerName = response.xpath(".//div[@class='summaryShortInfo']/h1/text()").extract()[0]
        print(playerName)

        item["total_kills"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[1]
        item["headshot"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[3]
        item["total_deaths"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[5]
        item["kd_ratio"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[7]
        item["damage_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[9]
        item["grenade_dmg_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[11]
        item["maps_played"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[13]
        item["rounds_played"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[15]
        item["kiils_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[17]
        item["assists_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[19]
        item["death_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[21]
        item["saved_by_teammates_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[23]
        item["saved_teammates_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[25]
        item["rating_1"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[27]



        doc = self.es.get(index="csgo",
                     doc_type="players",
                     id=playerName)

        doc["_source"]["stats"] = item
        #print( json.dumps(doc["_source"]))


        res = self.es.index(index='csgo',
                       doc_type='players',
                       id=playerName,
                        body=json.dumps(doc["_source"]))
        print(res)
        time.sleep(60)
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
