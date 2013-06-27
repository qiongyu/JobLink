import sys
from ad import *
from job import *
from adtab import *
from jobtab import *
from simtab import *
from reftab import *
from saltab import *

def main():
  #job_names = READ_LIST("missing_jobs.txt")
  ijob_names = ["postdoctoral researcher"]
  ijob_names = [jn.strip().lower() for jn in ijob_names]

  at = AdTab(50,8)
  job_names = []
  for job in ijob_names:
    old, jobs = at.lookup([job])
    if(old == 0): job_names.append(job)

  at.append(job_names)
  jobs = at.load_ads(job_names)
  print "Done appending ads."

  rt = RefTab(0)
  rt.load_refs()

  jt = JobTab()
  jt.append(jobs,rt)
  print "Done appending job skills."

  unique_names = at.unique()
  jobs1 = at.load_ads(unique_names)
  jobs1 = jt.load_jobs(jobs1)
  jt.close()
  rt.close()

  st = SimTab()
  st.create()
  st.append(jobs1)
  st.close()
  print "Done appending similar jobs."

  sat = SalTab()
  sat.append(jobs)
  sat.close()
  print "Done appending salary."

if(__name__ == '__main__'):
  main()
