import math
import string
from misc import *
import nltk
import MySQLdb as mdb
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer as wnl
from nltk.collocations import *
from collections import defaultdict
from lxml import html
from lxml import etree

class Job:
  '''
  This class contains information pertaining to a job, i.e. keywords, ads,
  similar jobs, etc. It also contains many functions that can be applied to
  the job data.
  Functions:
    calc_fd() - calculates aggregate frequency distributions
    calc_all_fd() - calculates individual frequency distributions
    extract_keywords(ref_m, ref_b, ref_t) - extracts keywords 
    calc_job_relevance(jobs) - finds similar jobs
    fetch_salary(place) - fetches salary info
    calc_keyword_freq(job2) - calculates keyword frequencies for job2 keywords
                              in self.ads
  '''
  
  def __init__(self, name, n_ad, n_key):
    self.name = name
    self.ads = []
    self.keywords = []
    self.simjobs = []
    self.fd_all = []
    self.statesal = {}
    self.n_ad = n_ad
    self.n_key = n_key

  def kill(self):
    self.ads = []
    self.keywords = []
    self.simjobs = []
    self.fd_all = []
    self.statesal = {}

  def calc_fd(self):
    """
    This function calculates the frequency distributions of unigrams, bigrams
    and trigrams from all the scraped ads (combined). It also finds the bigrams
    and trigrams that are likely combinations of words (i.e. those that make 
    sense).
    Output:
      fd_mono - unigram frequency distribution.
      fd_bi - bigram frequency distribution.
      fd_tri - trigram frequency distribution.
      goodbi - bigrams that have high measure of pointwise mutual information
      goodtri - trigrams that have high measure of pointwise mutual information
    """
    all_mono = []
    all_bi = []
    all_tri = []
    lmt = wnl()
    combined_ads = []

#Concatenante unigrams, bigrams and trigrams from different ads together so
#that we don't need to make frequency distributions for each one (we only care
#about the collective anyway).
    for ad in self.ads:
      combined_ads = combined_ads+ad

      btemp = nltk.bigrams(ad)
      all_bi += btemp
      ttemp = nltk.trigrams(ad)
      all_tri += ttemp
#Lemmatize unigrams (this prevents things like cat and cats from being
#counted as different words.
      mono_stem = [lmt.lemmatize(w) for w in ad]
      all_mono += mono_stem

#Do some collocation analysis using pmi - pointwise mutual information.
#This measures how likely it is that a bigram/trigram of words actually make
#sense together.
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    trigram_measures = nltk.collocations.TrigramAssocMeasures()

    finder = BigramCollocationFinder.from_words(combined_ads)
#Only keep grams that occur >25 times and pmi>100
    finder.apply_freq_filter(0.5*self.n_ad)
    goodbi = finder.nbest(bigram_measures.pmi, 100)

    finder = TrigramCollocationFinder.from_words(combined_ads)
    finder.apply_freq_filter(0.5*self.n_ad)
    goodtri = finder.nbest(trigram_measures.pmi, 100)

#Calculate frequency distributions.
    fd_mono = nltk.FreqDist(all_mono)
    fd_bi = nltk.FreqDist(all_bi)
    fd_bi = KEY_TUPLE_TO_LIST(fd_bi)
    fd_tri = nltk.FreqDist(all_tri)
    fd_tri = KEY_TUPLE_TO_LIST(fd_tri)

    goodbi = TUPLE_TO_LIST(goodbi)
    goodtri = TUPLE_TO_LIST(goodtri)

    return fd_mono, fd_bi, fd_tri, goodbi, goodtri

  def calc_all_fd(self):
    """
    This function creates a mega-frequency distribution dictionary. It takes
    a list of frequency distributions (from each ad) for each job and puts all
    of this info into a single dictionary keyed to job name.
    Result:
      self.fd_all - the mega-dictionary described above.
    """
    fd_all = []
    lmt = wnl()
    for ad in self.ads:
      btemp = nltk.bigrams(ad)
      fd_btemp = nltk.FreqDist(btemp)
      fd_btemp = KEY_TUPLE_TO_LIST(fd_btemp)

      ttemp = nltk.trigrams(ad)
      fd_ttemp = nltk.FreqDist(ttemp)
      fd_ttemp = KEY_TUPLE_TO_LIST(fd_ttemp)

      mono_stem = [lmt.lemmatize(w) for w in ad]
      fd_mtemp = nltk.FreqDist(mono_stem)

      fd_all.append( dict(fd_mtemp.items()+fd_btemp.items()+fd_ttemp.items()) )

    self.fd_all = fd_all

  def extract_keywords(self, rm, rb, rt):
    """
    This function drives the keyword extraction.
    Input:
      rm - reference table unigram frequency distribution.
      rb - reference table bigram frequency distribution.
      rt - reference table trigram frequency distribution.
    Output:
      dictionary of top keywords.
    """

    def calc_relevance(fd, ref, n):
      """
      This function constructs the term frequencies necessary to calculate the
      relevance score.
      Input:
        fd - frequency distribution for ads for a specific job.
        ref - frequency distributions for reference ads.
        n - set to 1 for unigrams, 2 to bigrams, 3 for trigrams.
      Output:
        Rel - dictionary of relevance scores for each keyword.
      """

      C_query_tot = sum(fd.values())*1.
      C_query_avg = C_query_tot/len(fd)

      C_ref_tot = sum(ref.values())*1.
      C_ref_avg = C_ref_tot/len(ref)

      R = {}
      for term, count in fd.items():
#For some reason, unigrams get split into individual characters some times, so
#set a maxsplit.
        k = string.split(term,maxsplit=n)
        C_query = count
        f_query = C_query/C_query_avg

        C_ref = ref.get(term,-1)
        if(C_ref <= 10):
          f_ref = 1. if(IS_WORD(term)==1) else 100000
        else:
          f_ref = C_ref/C_ref_avg
        rel = relevance(f_query,f_ref,C_query,0.6)
        R[term] = rel

      return R

    def relevance(fq, fr, Cq, x):
      """
      This function calculates the relevance score of a keyword.
      Input:
        fq - term frequecy of the keyword in the ads for a specific job.
        fr - term frequency of the keyword in the reference table.
        Cq - number of times the keyword appears in the ads for a specific job.
        x - some extra floating term.
      Output:
        relevance score.
      """
      return (x*math.log(fq/fr)+(1.-x))*Cq

    def remove_junk(tm, tb, tt, gb, gt):
      """
      This code cleans the keyword list (i.e. removes similar words, etc.)
      Input:
        tm - dictionary of unigram relevance scores.
        tb - dictionary of bigram relevance scores.
        tt - dictionary of trigram relevance scores.
        gb - bigrams with high pmi scores.
        gt - trigrams with high pmi scores.
      Output:
        tm, tb and tt cleaned.
      """
#Filter out all of the bigrams/trigrams with low pmi scores (i.e. only keep the
#ones in gb and gt.
      tempb = {}
      for term in gb: tempb[term] = tb.get(term,0)
      tb = tempb

      tempt = {}
      for term in gt: tempt[term] = tt.get(term,0)
      tt = tempt

#Get rid of terms that contain the job name. 
      job_name = self.name
      if(' ' in str(job_name)):
        sjn = job_name.split()
        for w in sjn:
          tm.pop(w,None)
        if(len(sjn)==2):
          tb.pop(job_name,None)
        elif(len(sjn)==3):
          tt.pop(job_name,None)
      else:
        tm.pop(job_name,None)
    
#Set the stopwords + other words that seem to come up often but obviously make
#no sense.
      sw = stopwords.words('english')+\
           ['yes', 'no', 'your', 'youll', 'benefits', 'go', 'river', 'amp',\
            'us', 'e', 'permit','requires','work','types', 'dot', 'without',\
            'plus', 'must', 'way', 'new', 'job', 'click', 'http', 'winning',\
            '/', 'intended', 'youre', 'location', 'conditions', 'sized',\
            'use', 'may', 'june', 'year', 'o', 'g', 'n', 'take', 'right',\
            'term', 'always', 'existing', 'onto', 'youve', 'experience',\
            'really', 'ensure', 'difference', 'ensures', 'v', 'years', 'onto']
      monopop = []
      bipop = []
      tripop = []
  
#Remove stop words (or terms containing stop words).
      for key in tm.keys():
        if(key in sw):
          monopop.append(key)
      for key in tb.keys():
        k = key.split()
        for w in k:
          if(w in sw):
            bipop.append(key)
            break
      for key in tt.keys():
        k = key.split()
        for w in k:
          if(w in sw):
            tripop.append(key)
            break
      for p in set(monopop): tm.pop(p,None)
      for p in set(bipop): tb.pop(p,None)
      for p in set(tripop): tt.pop(p,None)

#Take care of trigrams with duplicating bigrams (i.e. banker residential 
#brokerage and residential brokerage company, etc.): remove the one with the
#lower relevance score (or if equal, just keep one).
      monopop = []
      bipop = []
      tripop = []

      maxr = {}
      for term, rel in tt.items():
        k = term.split()
        c1 = k[0]+' '+k[1]
        c2 = k[1]+' '+k[2]
        if(maxr.get(c1,0) <= rel): maxr[c1] = term
        if(maxr.get(c2,0) <= rel): maxr[c2] = term
      for term, rel in tt.items():
        k = term.split()
        c1 = k[0]+' '+k[1]
        c2 = k[1]+' '+k[2]
        if(maxr.get(c1,0) != term and maxr.get(c2,0) != term): 
          tripop.append(term)

#Do some lemmatizing on the units making up bigrams and trigrams to get rid of
#similar words or bigrams contained in trigrams (unigrams contained in bigrams).
      lmt = wnl()
      for term, rel in tt.items():
        k = term.split()
        c1 = k[0]+' '+k[1]
        c2 = k[1]+' '+k[2]
        if(math.fabs(rel-tb.get(c1,1e5)) < 140. and rel > 70.): bipop.append(c1)
        if(math.fabs(rel-tb.get(c2,1e5)) < 140. and rel > 70.): bipop.append(c2)
        if(c1 == job_name or c2 == job_name): tripop.append(term)
        kl = [lmt.lemmatize(w) for w in k]
        if( (math.fabs(rel-tm.get(kl[0],rel))<140. or \
             math.fabs(rel-tm.get(kl[1],rel))<140. or \
             math.fabs(rel-tm.get(kl[2],rel))<140.) and rel > 34. ):
          monopop += kl
  
      for term, rel in tb.items():
        k = term.split()
        kl = [lmt.lemmatize(w) for w in k]
        if( (math.fabs(rel-tm.get(kl[0],rel))<70. or \
             math.fabs(rel-tm.get(kl[1],rel))<70.) and rel > 17. ):
          monopop += kl
    
#Do some stemming on unigrams to get rid of similar words.
      stemmer = nltk.PorterStemmer()
      for t1, r1 in tm.items():
        if(r1 < 17.): continue
        st1 = stemmer.stem(t1)
        for t2, r2 in tm.items():
          if(t1 == t2 or r2 < 17.): continue
          st2 = stemmer.stem(t2)
  
          if(r1 < r2): small = t1
          else: small = t2
          if( (st1 == st2) or (st1 == st2+"e") or (st1+"e" == st2) or \
              (st1[:-1] == st2) or (st1 == st2[:-1]) or \
              (st1[:-1] == st2[:-1]) ):
            monopop.append(small)
  
      for p in set(monopop): tm.pop(p,None)
      for p in set(bipop): tb.pop(p,None)
      for p in set(tripop): tt.pop(p,None)

      return tm, tb, tt

    fd_mono, fd_bi, fd_tri, gbi, gtri = self.calc_fd()

    R_mono = calc_relevance(fd_mono,rm,1)
    R_bi = calc_relevance(fd_bi,rb,2)
    R_tri = calc_relevance(fd_tri,rt,3)

    top_mono, top_bi, top_tri = remove_junk(R_mono,R_bi,R_tri,gbi,gtri)
    top_tri = {}
    top = dict(top_mono.items()+top_bi.items()+top_tri.items())

    top_words = []
    for term, rel in sorted(top.iteritems(),key=lambda(w,f): (f,w)):
      top_words.append( (term,rel) )
    top_words = top_words[::-1][:self.n_key]

    return top_words

  def calc_job_relevance(self,jobs):
    """
    This function calculates the similarity score based on the Jaccard distance
    between the query job and all other jobs.
    Input:
      jobs - list of Job objects that you want to find sim jobs for.
    Output:
      dictionary of similar scores for each job (relative to query job q).
    """

    def fetch_keyword_counts(q_top, t_top, fd):
      """
      This function counts the occurrences of keywords in job ads to obtain 
      numbers for the Jaccard distance calculation.
      Input:
        q_top - top keywords from job 1.
        t_top - top keywords from job 2.
        fd - list of frequency distributions for each ad (job1 + job2).
      Output:
        # of ads (job1+job2) where a keyword for job1 occurred.
        # of ads (job1+job2) where a keyword for job2 occurred.
        # of ads (job1+job2) where pairs of keywords (job1,job2) occur.
      """
      n = len(q_top)
      qkeyword_count = defaultdict(int)
      qkeyword_count.fromkeys(q_top,0)
      tkeyword_count = defaultdict(int)
      tkeyword_count.fromkeys(t_top,0)
      qtkeyword_count = defaultdict(int)
      for w1 in q_top:
        for w2 in t_top:
          qtkeyword_count[(w1,w2)] = 0

      for ad in fd:
        for w1 in q_top:
          v1 = ad.get(w1,0)
          if(v1!=0): qkeyword_count[w1] += 1
        for w2 in t_top:
          v2 = ad.get(w2,0)
          if(v2!=0): tkeyword_count[w2] += 1
        for w1 in q_top:
          v1 = ad.get(w1,0)
          for w2 in t_top:
            v2 = ad.get(w2,0)
            if(v1!=0 and v2!=0): qtkeyword_count[(w1,w2)] += 1
      return qkeyword_count, tkeyword_count, qtkeyword_count

    def calc_Jaccard(cq, ct, cqt):
      """
      This function calculates the Jaccard distance between the keywords for 
      2 different jobs.
      Input:
        cq - # of ads (job1+job2) where a keyword for job1 occurred.
        ct - # of ads (job1+job2) where a keyword for job2 occurred.
        cqt - # of ads (job1+job2) where pairs of keywords (job1,job2) occur.
      Output:
        Jaccard distance = # where pair occurred / (total # where either 
                           occurred)
      """
      n = len(cq)
      Jaccard = {}
      for kq, vq in cq.items():
        for kt, vt in ct.items():
          Jaccard[(kq,kt)] = cqt[(kq,kt)]*1./(vq+vt-cqt[(kq,kt)])

      return Jaccard

    qkeywords = self.keywords
    qfd_all = self.fd_all
    nk = len(qkeywords)
    nd = nk*nk*1.

    avgJaccard = {}
    for job in jobs:
      tkeywords = job.keywords
      tfd_all = job.fd_all

      cq, ct, cqt = fetch_keyword_counts(qkeywords,tkeywords,qfd_all+tfd_all)
      J = calc_Jaccard(cq, ct, cqt)
      avgJ = 0.
      skill_pair = J.keys()
      for skills in skill_pair: avgJ += J[skills]
      avgJ = avgJ/nd
      avgJaccard[job.name] = avgJ

    return avgJaccard

  def fetch_salary(self,place):
    """
    This code fetches salary information for a job and place.
    Input:
      place - location.
    Output:
      salary - the salary (as a string, i.e. with $ and ,).
    """
    job_name = self.name.split()
    job_name = '+'.join(job_name)
    city_name = place.split()
    city_name = '+'.join(city_name)

    home = "http://www.indeed.com/salary?q1=\""
    page = OPEN_URL(home+job_name+"\"&l1="+city_name)

    h = html.document_fromstring(page)
    meat = h.xpath('.//span[@style="display:block;"]')[0]
    text = etree.tostring(meat)
    for i in range(0,len(text)):
      if(text[i] == "$"): bdex = i
      if(text[i] == "<" and text[i+1] == "/"): edex = i
    salary = text[bdex:edex]
    if(salary == ''): salary = 0

    return salary

  def calc_keyword_freq(self, job2):
    """
    This function calculates which of job2's keywords are already known by 
    someone with job1 and which skills they should work on to transition to
    job2.
    Input:
      job2 - list of Job objects for similar job(s) 
    Output:
      dictionary of tuple(occurrence rates for each keyword, 0 or 2), where 0 
      indicates a common keyword and 2 indicates that it is more applicable to
      job2.
    """
    kw = job2.keywords
    q1_fd = self.fd_all
    q2_fd = job2.fd_all
    len1 = len(q1_fd)*1.
    cdict1 = {}
    len2 = len(q2_fd)*1.
    cdict2 = {}

#First calculate how often a keyword from job2 occurs in job ads from job1
#as well as how often it occurs in job ads from job2.
    for k in kw:
      count = 0
      for fd in q1_fd:
        if(fd.get(k,0)!=0): count+=1
      cdict1[k] = count/len1

      count=0
      for fd in q2_fd:
        if(fd.get(k,0)!=0): count+=1
      cdict2[k] = count/len2

#If the keyword occurs in more than 40% of job1 ads, then people in job1 
#probably already know it. So it is "common" to both jobs (these keywords get
#the 0 label). Otherwise, the keywords get the 2 label. The occurrence rate
#of the keyword for job2 is recorded to size the circles on the results.html 
#page.
    cdict = {}
    ndiff = 0
    for k in kw:
      if(cdict1[k] > 0.4): cdict[k] = [cdict2[k],0]
      else:
        cdict[k] = [cdict2[k],2]
        ndiff += 1

    return cdict, ndiff
