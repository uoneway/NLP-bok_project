import scrapy
import re
from naver_crawler.items import NaverCrawlerItem
from datetime import datetime, timedelta
#from dateutil.relativedelta import  relativedelta


class NaverSpider(scrapy.Spider):
    name = "naver"

    def start_requests(self):
        # 네이버 뉴스에서 '금리'라는 키워드 검색결과 페이지 리턴하기
        # 2005.1 ~ 2017.12 기간동안 
        start_date = datetime.strptime("2005-01-01", "%Y-%m-%d") #시작 날짜
        end_date = datetime.strptime("2017-12-31", "%Y-%m-%d") #끝 날짜
        date_list = [start_date + timedelta(days=x) for x in range(0, (end_date-start_date).days+1)]
        # 쿠키의 news_office_checked에 해당하는 연합뉴스, 연합인포맥스, 이데일리 
        news_office_checked_list = ['1001', '1018', '2227']  # str로 넣어줘야 함 

        #해당 날짜에 해당하는 뉴스 기사 URL 리스트
        for news_office in news_office_checked_list:
            for date in date_list:
                date_str1 = date.strftime("%Y.%m.%d")
                #date_str2 = date.strftime("%Y%m%d")
                #url = f"https://search.naver.com/p/crd/rd?m=1&px=674&py=653&sx=674&sy=653&p=U02Falp0YiRssvdkRGVssssssXw-216803&q=%EA%B8%88%EB%A6%AC&ie=utf8&rev=1&ssc=tab.news.all&f=news&w=news&s=Lvkf0XM%2BBaoGIzBQJ%2F2%2BBA%3D%3D&date=1598924644539&bt=10&a=fno.journalapply&u=https%3A%2F%2Fsearch.naver.com%2Fsearch.naver%3Fwhere%3Dnews%26query%3D%25EA%25B8%2588%25EB%25A6%25AC%26sm%3Dtab_opt%26sort%3D1%26photo%3D0%26field%3D0%26reporter_article%3D%26pd%3D3%26ds%3D2017.12.31%26de%3D2017.12.31%26docid%3D%26nso%3Dso%253Add%252Cp%253Afrom20171230to20171231%252Ca%253Aall%26mynews%3D1%26refresh_start%3D0%26related%3D0"
                url_org = f'https://search.naver.com/search.naver?where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_opt&sort=2&mynews=1&pd=3&ds={date_str1}&de={date_str1}'

                yield scrapy.Request(url=url_org,
                                    cookies={'news_office_checked': news_office}, #request에 cookie 추가
                                    callback=self.search_page_requests)


    def search_page_requests(self, response):
        # 검색된 총 뉴스 수
        # 만약 하나도 없으면 첫번째 줄에서 None이 리턴되면서 두번째 줄에서 오류나지만, 
        # scrapy에서 해당 건만 중단하고 다음으로 넘어가기에 오류 없이  진행되는듯?
        article_total_num = response.xpath('//*[@id="main_pack"]/div[2]/div[1]/div[1]/span/text()').get()
        article_total_num = article_total_num.split('/')[1]  # 전체 건수만 가져오기
        article_total_num =  re.sub(',|건', '', article_total_num) # 콤마, 건 제거

        # 한 페이지 당 10개 뉴스가 검색되기에  검색된 건수를 기반으로 시작건수 정보를 넣어 모든 페이지를 가져옴
        for i in range(1, int(article_total_num), 10):
            yield scrapy.Request(url=f'{response.url}&start={i}',
                                 callback=self.news_requests)
            

    def news_requests(self, response):
        # 뉴스 개별건에 대해
        for section in response.xpath('//*[@id="main_pack"]/div/ul/li'):
            media = section.xpath('//span[@class="_sp_each_source"]/text()').extract()[0]#media 어디인지 파싱한것
            date = section.xpath('dl/dd[1]/text()').getall()[1]

            # 네이버 뉴스 링크를 제공하는 경우,
            if media=='연합뉴스'or media =='이데일리':   
                url=section.xpath('dl/dd/a/@href').extract()[0]  # 제목 옆 네이버뉴스 링크 가져오기
            elif media=='연합인포맥스':
                url=section.xpath('dl/dt/a/@href').extract()[0]  # 제목 링크 가져오기

            yield scrapy.Request(url=url,
                                meta={'media':media,'date':date},
                                callback=self.parse, )


    def parse(self, response):
        item = NaverCrawlerItem()
        media = response.meta['media']
        item['media'] = media
        item['date'] = response.meta['date']

        if media == '연합뉴스' or media =='이데일리': 
            item['body'] = response.xpath('//*[@id="articleBodyContents"]/text()').getall()
        elif media == '연합인포맥스':
            item['body'] = response.xpath('//*[@id="article-view-content-div"]/text()').getall()

        yield item
