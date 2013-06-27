import MySQLdb as mdb
import re
import threading
import Queue
from misc import *
from lxml import html
from lxml import etree

class Ads:
  '''
  This class contains informationing pertaining to ads, i.e. their urls, text,
  etc. It also contains many functions that can be applied to ad data.
  Functions:
    fetch_ad_urls() - fetches urls for job ads
    read_ads() - reads the urls and cleans up the text
  '''
  def __init__(self, name, n_ad):
    self.n_ad = n_ad
    self.name = name
    self.urls = []
    self.ads = []

  def kill(self):
    self.ads = []
    self.urls = []

  def fetch_ad_urls(self):
    """
    This function queries the api for the job title and scrapes the urls of the 
    job ads. 
    Result:
      self.urls - list of job ad urls for job_name
    """
    job_name = self.name
    job_name = job_name.split()
    job_name = '+'.join(job_name)  
    urls = []
    jread = 0
    pp = 0
    home = "http://api.indeed.com/ads/apisearch?publisher=3385380486177907&v=2"
    while(jread < self.n_ad):
      list_url = home+'&q=\"'+job_name+'\"&start='+str(pp)
      try:
        list_page = OPEN_URL(list_url)
      except:
        continue

      ad_url = re.findall(r'<url>(.*)</url>',list_page)
      urls += ad_url

      jread += len(ad_url)
      pp+=10

    self.urls = urls[0:self.n_ad]

  def read_ads(self):
    """
    This function reads the ad urls and fetches the ad text. It is multi-
    threaded for faster scraping.
    Result:
      self.ads - list of cleaned ad texts scraped from urls.
    """
    def get_text(self,u,adtext):
      try:
        page = OPEN_URL(u)
      except:
        return
      text = self.fetch_ad_text(page)
      adtext.put(text)

    adtext = Queue.Queue()
    threads = [threading.Thread(target=get_text,args=(self,arg,adtext)) \
               for arg in self.urls]

    for t in threads:
      t.start()
    for t in threads:
      t.join()
    adtext_list = []
    while(adtext.empty() != True):
      adtext_list.append(adtext.get())

    self.ads = adtext_list

  def fetch_ad_text(self,page):
    """
    This function processes the ad text scraped from the webpage.
    Input:
      page - the text from webpage (returned by OPEN_URL).
    Output:
      cleaned output with punctuation, html tags, etc removed
    """
    h = html.document_fromstring(page)
    meat = h.xpath('.//span[@class="summary"]')[0]
    text = etree.tostring(meat)
    text = text.lower()
    text = re.sub(r'<\w+.*>','',text)
    text = re.sub(r'</\w+>','',text)
    text = re.sub(r'<\w+/>','',text)
    text = re.sub(r"'\w\s",'',text)
    text = re.sub(r'\\xe2\\x80\\x99\w','',text)
    atext = re.findall(r'\s\w+[^\w\s]\w+\s',text)
    for a in atext:
      p = re.search(r'[^\w\s]',a).group()
      if(p=='/' or p==',' or p=='&'):
        text = text.replace(p,' and ')
      else:
        text = text.replace(p,'')
    text = re.sub('[0-9\+\#-\&\;\(\)\?\'\"\.\,\@\:\!\$\%\*\_]+','',text)
    text = re.sub(r'\s\d+\s','',text)
    text = re.sub(r'\s[\+\#-]+\s','',text)

    return text.split()
