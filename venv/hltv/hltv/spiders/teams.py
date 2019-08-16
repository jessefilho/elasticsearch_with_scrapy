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



class Teams(scrapy.Spider):
    name = "teams"
    allowed_domains = ["hltv.org/"]
    start_urls = ["https://www.hltv.org/ranking/teams/2019/august/12"]

    #players = []

    def parse(self, response):
        print('main_url: ' + response.url)

        teamslinks = response.xpath(".//div[@class='ranking']//div[@class='more']/a[@class='moreLink']/@href").extract()
        i = 0  # counter pages entries


        for teamurl in teamslinks:
            item = TeamsItem()


            teampage = "https://www.hltv.org"+ teamurl
            item["teamurl"] = teampage
            item["ranking"] = response.xpath(".//div[@class='ranking-header']/span[@class='position']/text()").extract()[i]
            item["name_team"] = response.xpath(".//div[@class='ranking']//div[@class='relative']//span[@class='name']/text()").extract()[i]
            item["team_points"] = response.xpath(".//div[@class='ranking']//div[@class='relative']//span[@class='points']/text()").extract()[i]



            # callback to event page
            request = scrapy.Request(url=teampage,
                                     callback=self.parse_teamPage,
                                     errback=self.errback_httpbin,
                                     dont_filter=True)
            request.meta['item'] = item

            i = i + 1


            yield request



    def parse_teamPage(self, response):
        item = response.meta['item']

        #within teams page
        item["country"] = response.xpath(".//div[@class='profile-team-info']/div[@class='team-country text-ellipsis']/text()").extract()[0]
        item["weeks_in_top30"] =response.xpath(".//div[@class='profile-team-stats-container']/div[@class='profile-team-stat'][2]//span[@class='right']//text()").extract()[0]
        item["average_player_age"] =response.xpath(".//div[@class='profile-team-stats-container']/div[@class='profile-team-stat'][3]//span[@class='right']//text()").extract()[0]
        urlplayers = response.xpath(".//div[@class='teamProfile']//a[@class='col-custom']/@href").extract()

        item["players"] = []
        arrayPlayers = []

        count_players = 0
        for pagePlayer in urlplayers:
            # Wait for 5 seconds
            # time.sleep(5)
            player = {}
            urlplayer = "https://www.hltv.org" + pagePlayer
            urlplayer_stats = "https://www.hltv.org/stats" + pagePlayer
            player["url_player"] = urlplayer
            player["urlplayer_stats"] = urlplayer_stats.replace('player','players')




            request = scrapy.Request(url=urlplayer,
                                     callback=self.parse_playerPage,
                                     errback=self.errback_httpbin,
                                     dont_filter=True)
            request.meta['item'] = item
            request.meta['player'] = player



            #arrayPlayers.append(player)

            #item["players_url"] = arrayPlayers


            yield request





        #return request


    def parse_playerPage(self, response):
        item = response.meta['item']
        player = response.meta['player']
        #time.sleep(15)
        #player = {}

        player["nick_player"] = response.xpath(".//div[@class='playerName']/h1/text()").extract()[0]
        player["real_name"] = response.xpath(".//div[@class='playerRealname']/text()").extract()[0]
        player["nationality"] = response.xpath(".//div[@class='playerRealname']//@alt").extract()[0]
        player["social_midias"] = response.xpath(".//div[@class='playerSocial']/a/@href").extract()
        player["age"] = response.xpath(".//div[@class='playerAge']/span[@class='listRight']/text()").extract()[0]
        player["trophies"] = response.xpath(".//div[@class='trophyHolder']/span/@title").extract()



        # print("@@@@@@@@@")
        # print(player["urlplayer_stats"])
        # request = scrapy.Request(url=player["urlplayer_stats"],
        #                          callback=self.parse_statsPlayerPage,
        #                          errback=self.errback_httpbin,
        #                          dont_filter=True)
        # request.meta['item'] = item
        # request.meta['player'] = player

        #yield item

        item["players"].append(player)
        yield item

    def parse_statsPlayerPage(self, response):

        item = response.meta['item']
        player = response.meta['player']
        print ("############## >>>>>>>>>>>>>>>>>>>>>>>")

        player["total_kills"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[1]
        player["headshot"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[3]
        player["total_deaths"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[5]
        player["kd_ratio"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[7]
        player["damage_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[9]
        player["grenade_dmg_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[11]
        player["maps_played"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[13]
        player["rounds_played"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[15]
        player["kiils_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[17]
        player["assists_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[19]
        player["death_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[21]
        player["saved_by_teammates_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[23]
        player["saved_teammates_per_round"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[25]
        player["rating_1"] = response.xpath(".//div[@class='statistics']//div[@class='stats-row']/span/text()").extract()[27]

        item["players"].append(player)

        return item


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
