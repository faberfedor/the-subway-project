#!/usr/bin/python

import urllib
import simplejson
import sqlite3
import time
from nltk.corpus import stopwords

database = './tweets.sqlite'
connection = sqlite3.connect(database)
cursor = connection.cursor()
cursor.execute('create table if not exists poiwords (ts integer, poi text, bow text)')



def getTweets(query):
  search = urllib.urlopen("http://search.twitter.com/search.json?q="+query)
  dict = simplejson.loads(search.read())
  res = ""
  for result in dict["results"]: # result is a list of dictionaries
    #print "*",result["text"],"\n"
    res += result["text"]
  return res

# implement this in a list comprehension for filtering  
#  import re
#  
#  regexes = [
#      # your regexes here
#      re.compile('hi'),
#  #    re.compile(...),
#  #    re.compile(...),
#  #    re.compile(...),
#  ]
#  
#  mystring = 'hi'
#  
#  if any(regex.match(mystring) for regex in regexes):
#      print 'Some regex matched!'
#  

pois = open("pointsofinterest.txt").read().split('\n')
# remove blank line caused by EOL on last line
pois.pop()

for poi in pois:
    texts = getTweets('"'+poi+'"')
    texts = texts.lower().replace(poi, '')
    textsdict = texts.split()
    filteredtexts = [ t for t in textsdict if t.lower() not in stopwords.words("english") ]
    #counts = {}
    #for w in filteredtexts:
    #    counts[w] = counts.get(w,0) + 1

    ts = int(time.time())
    cursor.execute('insert into poiwords values (?, ?, ?)', (ts, poi, ",".join(filteredtexts)))
    connection.commit()

