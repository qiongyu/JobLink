from reftab import *
from adtab import *
from ad import *
from job import *
import MySQLdb as mdb
import re

class JobTab:
  '''
  This class contains all functions needed to make the job table (with keywords
  for each job).
  Functions:
    create() - create the table.
    append(jobs) - append keywords for jobs to table, jobs is a list of Job 
                   objects
    load_jobs(jobs) - load keyword information into jobs, jobs is a list of Job
                      objects (create this using AdTab functions)
  '''
  def __init__(self):
    self.con = mdb.connect('localhost', 'xxu', 'test623', 'jobdb')
    self.cur = self.con.cursor()
    self.cur.execute('''USE jobdb''')

  def close(self):
    self.con.commit()
    self.con.close()

  def create(self):
    self.cur.execute('''DROP TABLE IF EXISTS jobtab''')
    self.cur.execute('''CREATE TABLE jobtab \
                        (Job VARCHAR(255), Keyword VARCHAR(255),\
                        Relevance FLOAT)''')
    print "Will re-make jobs table..."

  def append(self, alljobs, ref):

    for j in alljobs:
      job = j.name
      ads = j.ads
      print job, len(ads)
      t_top = j.extract_keywords(ref.mono, ref.bi, ref.tri)
      print t_top
#Create a new entry for each keyword...this is because SQL can't seem to store
#lists.
      for w in t_top:
        kw = " ".join(w[0])
        self.cur.execute('''INSERT INTO jobtab(Job,Keyword,Relevance) \
                            VALUES("%s","%s","%f")'''%(job,w[0],w[1]))

    self.con.commit()

  def load_jobs(self, jobs):
    """
    This function loads the keywords for each job.
    Input:
      jobs - list of Job objects for storing keyword info.
    Output:
      jobs - returns the input list with keyword info inserted.
    """
    njobs = len(jobs)
    for i in range(njobs):
      job = jobs[i].name
      print job
      self.cur.execute('''SELECT * FROM jobtab WHERE Job LIKE "%s"'''%(job))
      jobrow = self.cur.fetchall()
      skill = [row[1] for row in jobrow]
      jobs[i].keywords += skill

    return jobs

def main():
  at = AdTab(50,8)
  job_names = at.unique()
  jobs = at.load_ads(job_names)

  rt = RefTab(0)
  rt.load_refs()

  jt = JobTab()
  jt.create()
  jt.append(jobs,rt)

  at.close()
  rt.close()
  jt.close()

if(__name__ == '__main__'):
  main()
