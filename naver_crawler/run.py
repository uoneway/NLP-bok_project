##scrapy 실행하기

import os
from scrapy.cmdline import execute

os.chdir(os.path.dirname(os.path.realpath(__file__)))

try:
    execute(['scrapy','crawl','naver_news'])
except SystemExit:
    pass
    