from flask import Flask, render_template, request, url_for, jsonify, send_file
import os
from reftab import *
from adtab import *
from jobtab import *
from simtab import *
from saltab import *
from ad import *
from job import *
import MySQLdb as mdb 
import json

app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(340284)

@app.route("/")
def home():
  con = mdb.connect('localhost','xxu','test623','jobdb')
  cur = con.cursor()

  with con:
    cur.execute("USE jobdb")
    cur.execute('''SELECT DISTINCT Job FROM adtab''')
    row = cur.fetchall()
    titles = [w[0] for w in row]
    jobs = {}
    jobs['titles'] = titles

  jsonjobs = jsonify(jobs)

  con.commit()
  con.close()

  return render_template('index.html', jobs=json.dumps(titles))

@app.route("/about.html")
def about():
  return render_template('about.html')

@app.route("/sorry.html")
def sorry():
  return render_template('sorry.html')

@app.route("/update.html")
def update():
  return render_template('update.html')

@app.route("/results.html", methods=['POST'])
def results():
  if not 'q' in request.form:
    return render_template('index.html')
  return render_template('results.html', q=request.form['q'])

@app.route("/backresults.html")
def backresults():
  return render_template('results.html', q=request.args.get('q'))

@app.route("/query.json")
def jobQuery():
  q = request.args.get('q')
  at = AdTab(50,8)
  jt = JobTab()
  st = SimTab()

  outDict = {}
  old, qjob = at.lookup([q])
  if(old):
    qjob = jt.load_jobs(qjob)[0]
    qjob.calc_all_fd()
    qkeywords = qjob.keywords
  else:
    outDict['result'] = -1
    fout = open("missing_jobs.txt","a")
    fout.write(q+"\n")
    return jsonify(outDict)
#      return render_template('update.html')
#      jdict, kdict = ADD_NEW_JOB(cur,q,50,8)

  qads = qjob.ads
  qjob = st.load_sim(qjob)
  slist = qjob.simjobs
  nsim = len(slist)
  if(nsim > 3): 
    slist = slist[:3]

  if(nsim == 0): 
    outDict['result'] = 0
    outDict['query'] = q
    outDict['qwords'] = qkeywords
    return jsonify(outDict)
#      return render_template('sorry.html',q=q,kw=qkeywords)

  fd_q = qjob.fd_all
  counts = {}
  tkeywords = {}
  sscore = []
  for job in slist:
    print job
    old, tjob = at.lookup([job])
    tjob = jt.load_jobs(tjob)[0]
    tjob.calc_all_fd()
    fd_t = tjob.fd_all
    tkeywords[job] = tjob.keywords
    cdict, ndiff = qjob.calc_keyword_freq(tjob)
    counts[job] = cdict
    sscore.append(ndiff)

  outDict['result'] = 1
  outDict['query'] = q #string
  outDict['qwords'] = qkeywords #list
  outDict['simjobs'] = slist #list
  outDict['simscores'] = sscore #list
  outDict['simwords'] = tkeywords #dict
  outDict['counts'] = counts #dict of dicts??

  at.close()
  jt.close()
  st.close()

  return jsonify(outDict)

@app.route("/more.html")
def more():
  return render_template('more.html')

@app.route("/states.json")
def states():
  return send_file("states.json")

@app.route("/salary.json")
def salaryQuery():
  city = request.args.get('city')
  q = request.args.get('q')

  st = SimTab()
  sat = SalTab()

  qjob = Job(q, 50, 8)
  qjob = st.load_sim(qjob)
  slist = qjob.simjobs
  nsim = len(slist)
  if(nsim > 3): 
    slist = slist[:3]

  data = {}
  data["q"] = q
  data["simjobs"] = slist

  qsalary = qjob.fetch_salary(city)
  ssalary = []
  allsstate = []
  for job in slist:
    tjob = Job(job, 50, 8)
    ss = tjob.fetch_salary(city)
    ssalary.append(ss)
    tjob = sat.load_sal(tjob)
    sstate = tjob.statesal
    allsstate.append(sstate)

  print qsalary
  print ssalary
  data["qsalary"] = qsalary
  data["simsalary"] = ssalary
  data["sstate"] = allsstate

  st.close()
  sat.close()
  return jsonify(data)

if __name__ == "__main__":
  app.run("0.0.0.0", 9999)
