from adtab import *
from jobtab import *
from ad import *
from job import *
import MySQLdb as mdb

class SimTab:
  '''
  This class contains all functions needed to make the similar jobs table.
  Functions:
    create() - create the table.
    append(jobs) - append similar jobs for jobs to table, jobs is a list of Job
                   objects.
    load_sim(job) - load similar job information into jobs, jobs is a _SINGLE_
                    Job object (i.e. can only load one at a time!)
  '''
  def __init__(self):
    self.con = mdb.connect('localhost', 'xxu', 'test623', 'jobdb')
    self.cur = self.con.cursor()
    self.cur.execute('''USE jobdb''')
    self.cutoff = 0.2

  def close(self):
    self.con.commit()
    self.con.close()

  def create(self):
    self.cur.execute('''DROP TABLE IF EXISTS simtab''')
    self.cur.execute('''CREATE TABLE simtab(Job VARCHAR(255), Simjob VARCHAR(255),\
                   Simscore FLOAT)''')
    print "Will remake simtab..."

  def append(self, jobs):
    njob = len(jobs)
    print "Calculating all fds..."
    for i in range(njob):
      jobs[i].calc_all_fd()
    for i in range(njob):
      job1 = jobs[i]

      J = job1.calc_job_relevance(jobs)
      nsim = 0
#Store each similar job as a separate entry because SQL can't store lists.
#Technically job1-job2 has the same similarity score as job2-job1, so the table
#is redundant since it stores the similar jobs (job2) for each job (job1). This
#can be fixed at some point if necessary, but the tables are so small it doesn't
#really matter.
      for job2 in J.keys():
        rel = J[job2]
        if(rel > self.cutoff):
          print job1.name, job2, rel
          self.cur.execute('''INSERT INTO simtab(Job,Simjob,Simscore)\
                              VALUES("%s","%s","%f")'''%(job1.name,job2,rel))
          nsim += 1

      if(nsim == 0):
        self.cur.execute('''INSERT INTO simtab(Job, Simjob, Simscore)\
                            VALUES("%s","none","0.0")'''%(job1.name))

  def load_sim(self, job):
    """
    This function loads all of the jobs that have a large enough similarity
    score to the query (stored in simtab).
    Input:
      job - a Job object for storing similar job infor.
    Output:
      job - the same Job object with keyword info inserted.
    """
    q = job.name
    self.cur.execute('''SELECT * FROM simtab WHERE Job="%s" ORDER BY Simscore DESC'''%(q))
    sim = self.cur.fetchall()
    sjob = []
    for row in sim:
      if(row[1] != q): job.simjobs.append(row[1])

    return job

def main():
  at = AdTab(50,8)
  job_names = at.unique()
  jobs = at.load_ads(job_names)

  jt = JobTab()
  jobs = jt.load_jobs(jobs)

  st = SimTab()
  st.create()
  st.append(jobs)

  at.close()
  jt.close()
  st.close()

if(__name__ == '__main__'):
  main()
