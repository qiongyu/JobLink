import urllib2
from nltk.corpus import wordnet as wn

def OPEN_URL(url):
  """
  This function opens urls.
  Input:
    url - url of webpage to open.
  Output:
    contents (text) of webpage.
  """
  return urllib2.urlopen(url).read()

def IS_WORD(word):
  """
  This function determines if the input is actually a word.
  Input:
    word - input word (term)
  Output:
    isword - equals 1 if it is a word, else equals 0
  """
  isword = 1
  for w in word.split():
    if(wn.synsets(w)):
      isword *= 1
    else:
      isword *= 0
  return isword

def READ_LIST(jlist):
  """
  This function reads in a file (with only one column!)
  Input:
    jlist - file name.
  Output:
    jobTitle - list of whatever was in the column.
  """
  fin = open(jlist,"r")
  jobTitle = []
  jobTitle = [line[0:-1] for line in fin]

  return jobTitle

def TUPLE_TO_LIST(l):
  """
  This function takes a tuple and concatenates the words. This is useful because
  from the frequency distribution, the bigrams/trigrams are returned as tuples
  and having to type () everytime I want to use the term as a key to fetch the
  frequency from the distribution dictionary is annoying.
  Input:
    l - list of tuples to be converted into lists
  Output:
    out - list of converted tuples
  """
  out = []
  for key in l:
    k=[key[i] for i in range(0,len(key))]
    k = " ".join(k)
    out.append(k)
  return out

def KEY_TUPLE_TO_LIST(d):
  """
  Same as above, except now the input/output are dictionaries. Basically 
  concatenantes the keys (tuples) and returns the dictionary with the new
  concatenated key.
  """
  for key, value in d.items():
    k=[key[i] for i in range(0,len(key))]
    k = " ".join(k)
    d[k] = d.pop(key)
  return d
