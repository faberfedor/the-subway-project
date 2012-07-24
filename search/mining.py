#!/usr/bin/python
import twitter
import nltk
import json
import re
from languageDetection import *

#qryStr = "Charing Cross"
qryStr = "Picadilly Circus"
#qryStr = "Stoke Newington"

regexes = [
    re.compile("[^\w\s]"),
    re.compile(r"\brt\b"),
    re.compile("&amp")
]

twitter_search= twitter.Twitter(domain="search.twitter.com")
search_results = []

twitters=twitter_search.search(q=qryStr, rpp=100, page=1)

for page in range(1,6):
    search_results.append(twitters)

ld = LangDetect()

tweets = [ r['text'] for result in search_results for r in result['results'] ]
en_tweets = [ tweet for tweet in tweets if ld.detect(tweet) == 'en' ]

words = []
for tweet in en_tweets:
    tw = tweet.lower().replace(qryStr.lower(), '')
    #t = tw # just until we get the previous line to work
    words += [ w for w in tw.split() ]

words_culled = [  w for w in words if w.lower() not in nltk.corpus.stopwords.words('english') ]

freq_dist = nltk.FreqDist(words_culled)
top_words = [ w for w in freq_dist.keys() if not any(regex.match(w) for regex in regexes) ]
for k in top_words[:10]:   #freq_dist.keys()[:10]:
    print k, freq_dist[k]


