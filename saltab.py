import MySQLdb as mdb
from adtab import *
from job import *

class SalTab:
  '''
  This class contains all functions needed to make the salary table.
  Functions:
    create() - create the table.
    append(jobs) - append salaries for jobs to table, jobs is a list of Job
                   objects.
    load_sal(job) - load the salary for 50 states for job, job is a _SINGLE_
                    Job object (i.e. can only load 1 at a time).
  '''
  def __init__(self):
    self.con = mdb.connect('localhost', 'xxu', 'test623', 'jobdb')
    self.cur = self.con.cursor()
    self.cur.execute('''USE jobdb''')
    self.states = READ_LIST("states.txt")

  def close(self):
    self.con.commit()
    self.con.close()

  def create(self):
    self.cur.execute('''DROP TABLE IF EXISTS saltab''')
    self.cur.execute('''CREATE TABLE saltab(Job VARCHAR(255), State TEXT, Salary FLOAT)''')
    print "Will remake saltab..."

  def append(self, jobs):
    for job in jobs:
      jn = job.name
      print jn
      for s in self.states:
        salary = job.fetch_salary(s)
        salary =float( salary.replace('$','').replace(',',''))
        self.cur.execute('''INSERT INTO saltab(Job,State,Salary) VALUE("%s","%s","%f")'''%(jn,s,salary))
    
    self.con.commit()

  def load_sal(self, job):
    '''
    This function loads the salaries for each state for job.
    Input:
      job - a Job object to load salary info into.
    Output:
      job - the same Job object with a dictionary of state salaries inserted.
    '''
    q = job.name
    self.cur.execute('''SELECT * FROM saltab WHERE Job LIKE "%s"'''%(q))
    rows = self.cur.fetchall()
    sdict = {}
    for row in rows: sdict[row[1]] = row[2]
    job.statesal = sdict
    return job

def main():
  at = AdTab(50,8)
  job_names = at.unique()
  jobs = at.load_ads(job_names[0:5])
  
  sat = SalTab()
  sat.create()
  sat.append(jobs)
  sat.close()

if(__name__ == '__main__'):
  main()
