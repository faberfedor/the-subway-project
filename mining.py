#!/usr/bin/python
import os, sys, urllib
import twitter
import nltk
import json, yaml, sqlite3
import re
from languageDetection import *
import logging, logging.config, logging.handlers
import time
import argparse

'''
TODO
    add logging

'''

logging.config.fileConfig('conf/logging.conf')
log = logging.getLogger('root')

debug = True
properties = dict()

word_regexes = [
    re.compile("[^\w\s]"),
    re.compile(r"\brt\b"),
    re.compile(r"RT"),
    re.compile("&amp"),
    re.compile("http:\S+"),
]

phrase_regexes = [
    re.compile(r"\b[Rr][Tt]\b"),
    re.compile(r"RT"),
]

ld = LangDetect()

# this is used in the parseArgs function
class Args(object):
    pass

def parseArgs():

    global properties

    a = Args() # temporary holding space for CLI args
    
    parser = argparse.ArgumentParser(description='Search for top term for list of points of interest')

    parser.add_argument("-d", "--dumpfile", nargs='?', 
                        help="dump raw tweets to a file")

    parser.add_argument("--poi", nargs='?', 
                        help="single point of interest, overrides --poisfile")

    parser.add_argument("--poisfile", nargs='?', 
                        help="file with list of points of interest, one poi per line")

    parser.add_argument("-b", "--database", nargs='?', 
                        help="write output to sqlite3 database (default: data/terms.sqlite3")

    parser.add_argument("-o", "--outfile", nargs='?', 
                        help="write output to file")

    parser.add_argument("-c", "--configFile", nargs="?", default="conf/subway.conf",
                        help="configuration file to use (default: conf/subway.conf).")

    args = parser.parse_args( namespace=a )
    argStr = ""

    log.info("   using config file " + a.configFile)
    if not os.path.isfile(a.configFile):
        log.critical("FATAL: config file " + a.configFile + " not found!  Exiting.")
        sys.exit(1)
        
    properties = yaml.load(open(a.configFile))

    # set/append only those args that have a value
    for k,v in a.__dict__.iteritems():
        if v is not None :
            properties[k] = v
            argStr += k + "=" + str(v) + "; "

    log.debug("Using args: %s." % (argStr))
    
def initDB():
    if properties.has_key("database"):
        db = properties["database"]
    else:
        db = "data/terms.sqlite3"

    connection=sqlite3.connect(db)
    cursor=connection.cursor()
    cursor.execute("create table if not exists terms (ts timestamp, poi char(25), top1 char(25), top5 char(50))")
    connection.commit()

    return [ connection, cursor ]

def getPOIs():

    if 'poi' in properties:  # override the file if a single POI is passed in
        pois = [ properties['poi'] ]
    else:
        pois = open(properties['poisfile']).read().split('\n')
        # remove blank line caused by EOL on last line
        pois.pop()

    return pois

def getStopWords():

    stopset = set(nltk.corpus.stopwords.words('english'))

    f = open("data/stopwords.txt")
    lines = f.read().splitlines()

    stopset.update(lines)

    return stopset

def main(args):

    log.info("Begin processing at " + time.asctime(time.localtime()) )
    ts = time.time()

    parseArgs()
    stopset = getStopWords()

    connection, cursor = initDB()

    twitter_search= twitter.Twitter()
   
    pois = getPOIs()
 
    for poi in pois:
        search_results = []

        try:
            twitters=twitter_search.search(q=poi, geocode="51.500,-0.126,15km", rpp=100, page=1)
        except:
            continue
                
        for page in range(1,6):
            search_results.append(twitters)
        
        tweets = [ r['text'] for result in search_results for r in result['results'] ]
        en_tweets = [ tweet for tweet in tweets if ld.detect(tweet) == 'en' ]
        # only those tweets that have our pio in them
        poi_tweets = [tweet for tweet in en_tweets if poi in tweet and
                      not any(regex.match(tweet) for regex in phrase_regexes)]
 
        if properties.has_key("dumpfile"):
            dumpfile = open(properties['dumpfile'], 'a')
            print>>dumpfile, poi, ':'
            for t in poi_tweets:
                print>>dumpfile, '    ', t.encode('utf-8')
            
        
        words = []
        for tweet in poi_tweets:
            tw = tweet.lower().replace(poi.lower(), '')
            #t = tw # just until we get the previous line to work
            words += [ w for w in tw.split() ]
        
        #words_culled = [  w for w in words if w.lower() not in nltk.corpus.stopwords.words('english') ]
        words_culled = [  w for w in words if w.lower() not in stopset ]
        
        freq_dist = nltk.FreqDist(words_culled)
        top_words = [ w for w in freq_dist.keys() if not any(regex.match(w) for regex in word_regexes) ]
        print "POI: " + poi
        for k in top_words[:5]:   #freq_dist.keys()[:10]:
            print "    ",k   #, top_words[:5]  #freq_dist[k]
            if properties.has_key("dumpfile"):
                dumpfile = open(properties['dumpfile'], 'a')
                print>>dumpfile, '    ', k.encode('utf-8') #, top_words[k] #freq_dist[k]

        cursor.execute("Insert into terms values(?, ?, ?, ?)", (ts, poi, top_words[0], ','.join(top_words[:5])))
        connection.commit()
    
    log.info("End processing at " + time.asctime(time.localtime()) )

    
if __name__ == "__main__":
    main(sys.argv[1:])

