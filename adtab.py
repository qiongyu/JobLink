import MySQLdb as mdb
from misc import *
from ad import *
from job import *

class AdTab:
  '''
  This class contains all functions needed to make the ad table.
  Functions:
    create() - create the table
    append(jobs) - append ads for jobs to table, jobs is a list of job names
    load_ads(jobs) - loads ads for jobs, jobs is a list of job names
    lookup(jobs) - finds if the job is already in the database or not
    unique() - returns all unique job names in database
  '''
  def __init__(self, n_ad, n_key):
    self.con = mdb.connect('localhost', 'xxu', 'test623', 'jobdb')
    self.cur = self.con.cursor()
    self.cur.execute('''USE jobdb''')
    self.n_ad = n_ad
    self.n_key = n_key

  def close(self):
    self.con.commit()
    self.con.close()

  def create(self):
    self.cur.execute('''DROP TABLE IF EXISTS adtab''')
    self.cur.execute('''CREATE TABLE adtab \
                        (Job VARCHAR(255), Adtext TEXT)''')
    print "Will re-make ad table..."

  def append(self, jobs):
    for jn in jobs:
      ads = Ads(jn,self.n_ad)
      ads.fetch_ad_urls()
      ads.read_ads()
      
      remove_ads = []
      for i in range(0,self.n_ad):
        w = ads.ads[i]
        if(len(w)==0):
          remove_ads.append(i)
          continue
        all_ads_tab = " ".join(w)
        try:
          self.cur.execute('''INSERT INTO adtab(Job,Adtext) VALUE("%s","%s")'''\
                              %(jn,all_ads_tab))
        except: continue

      for i in remove_ads[::-1]: del ads.ads[i]
      print jn, "Scraped", len(ads.ads)

    self.con.commit()

  def lookup(self, q):
    """
    This function queries the adtab to see if the job is already in the 
    database.
    Input:
      q - job title.
    Output:
      old - 1 if already in database, 0 if not.
      jlist - Job object for q with ad info (note that it is a list)
    """
    rows = self.load_ads(q)
    old = 0
    if(rows == 0): return old, 0
    else:
      old = 1
    return old, rows

  def unique(self):
    '''
    This function pulls all the unique job names from the database.
    Output:
      unique_names - a list of unique job titles.
    '''
    self.cur.execute('''SELECT DISTINCT Job FROM adtab''')
    row = self.cur.fetchall()
    unique_names = [r[0] for r in row]
    return unique_names

  def load_ads(self, jobs):
    """
    This function pulls all the ads for some job from the adtab database.
    Input:
      q - job title, if set to 0, pulls all ads.
    Output:
      jlist - list of Job objects with their ads inserted.
    """
    njobs = len(jobs)
    jlist = []
    for i in range(njobs):
      jtemp = Job(jobs[i], self.n_ad, self.n_key)
      self.cur.execute('''SELECT * FROM adtab WHERE Job LIKE "%s"'''%(jobs[i]))
      jobrow = self.cur.fetchall()
      if(len(jobrow) == 0): return 0
      for row in jobrow:
        ad = row[1]
        jtemp.ads.append(ad.split())
      jlist.append(jtemp)

    return jlist

def main():
  job_names = READ_LIST("job_titles.clean.txt")
  #job_names = job_names[15:20]
  job_names = [jn.strip().lower() for jn in job_names]

  at = AdTab(50,8)
  at.create()
  at.append(job_names)
  jobs = at.load_ads(job_names)
  at.close()

if(__name__ == '__main__'):
  main()
