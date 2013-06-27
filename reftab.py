import MySQLdb as mdb
from ad import *
from job import *

class RefTab:
  '''
  This class contains all functions needed to make the reference table.
  Functions:
    create() - create the table
    append() - append onto the table
    load_refs() - load reference tables
  '''

  def __init__(self, n_ad):
    self.con = mdb.connect('localhost', 'xxu', 'test623', 'jobdb')
    self.cur = self.con.cursor()
    self.cur.execute('''USE jobdb''')
    self.n_ad = n_ad
    self.mono = []
    self.bi = []
    self.tri = []

  def close(self):
    self.con.commit()
    self.con.close()
    self.mono = []
    self.bi = []
    self.tri = []

  def create(self):
    self.cur.execute('''DROP TABLE IF EXISTS reftab_mono''')
    self.cur.execute('''DROP TABLE IF EXISTS reftab_bi''')
    self.cur.execute('''DROP TABLE IF EXISTS reftab_tri''')
    self.cur.execute('''CREATE TABLE reftab_mono(Word VARCHAR(255), Count INT)''')
    self.cur.execute('''CREATE TABLE reftab_bi(Word VARCHAR(255), Count INT)''')
    self.cur.execute('''CREATE TABLE reftab_tri(Word VARCHAR(255), Count INT)''')

  def append(self):
    def insert(self, fd, tabname):
      for term, count in fd.items():
#Some times the connect times out or the ad doesn't load...just skip these.
        try:
          self.cur.execute('''INSERT INTO %s(Word,Count) VALUES("%s","%d")'''\
                              %(tabname,term,count))
        except:
          continue

    refs = Ads('', self.n_ad)
    refs.fetch_ad_urls()
    refs.read_ads()

    rjobs = Job('', self.n_ad, 0)
    rjobs.ads = refs.ads
    fd_m, fd_b, fd_t, gb, gt = rjobs.calc_fd()
    insert(self, fd_m, "reftab_mtest")
    insert(self, fd_b, "reftab_btest")
    insert(self, fd_t, "reftab_ttest")

    refs.kill()
    rjobs.kill()

    self.con.commit()

  def load_refs(self):
    """
    This function loads the reference frequency distributions.
    Results:
      self.uni-, bi- and trigram frequency distributions.
    """
    self.cur.execute("SELECT * FROM reftab_mono")
    refrow = self.cur.fetchall()
    ref_mono = {}
    for row in refrow:
      ref_mono[row[0]] = row[1]

    self.cur.execute("SELECT * FROM reftab_bi")
    refrow = self.cur.fetchall()
    ref_bi = {}
    for row in refrow:
      ref_bi[row[0]] = row[1]

    self.cur.execute("SELECT * FROM reftab_tri")
    refrow = self.cur.fetchall()
    ref_tri = {}
    for row in refrow:
      ref_tri[row[0]] = row[1]
  
    self.mono = ref_mono
    self.bi = ref_bi
    self.tri = ref_tri

def main():
  rt = RefTab(5000)
  rt.create()
  rt.append()
  rt.load_refs()
  rt.close()

if(__name__ == '__main__'):
  main()
