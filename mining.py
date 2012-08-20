#!/usr/bin/python
import os, sys, urllib
import twitter
import nltk
import json, yaml, sqlite3
import re
from languageDetection import *
import logging, logging.config, logging.handlers
import time
import argparse, csv

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
    cursor.execute("create table if not exists terms (ts timestamp, poi char(25), searchFor char(25), top1 char(25), top5 char(50), numTweets int, duration real, firstTweet char(20), lastTweet char(20))")
    connection.commit()

    return [ connection, cursor ]

def readInputCSV():

    csvfile = open('./data/Tube_SearchTerms.csv')
    records = csv.reader(csvfile)
    return records

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
   
    #pois = getPOIs()

    records = readInputCSV()
 
    for rec in records:
        search_results = []

        poi = rec[0]
        if poi == 'Name of Station' or poi[0] == '#':
            continue
        start = time.time()

        searchFor = rec[1].lower()
        excludeTweetFor = rec[2]
        excludeTerms = rec[3]

        try:
            twitters=twitter_search.search(q=searchFor, geocode="51.500,-0.126,15km", rpp=100, page=1)
        except:
            continue
                
        for page in range(1,6):
            search_results.append(twitters)
       
 
        tweets = [ r['text'].lower() for result in search_results for r in result['results'] ]
        created_ats = [ r['created_at'] for result in search_results for r in result['results'] ]

        created_tss = sorted([time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(c,'%a, %d %b %Y %H:%M:%S +0000'))
                         for c in created_ats ])
        firstTweet = created_tss[0]
        lastTweet  = created_tss[len(created_tss)-1]

        totalTweets = len(tweets)
        en_tweets = [ tweet for tweet in tweets if ld.detect(tweet) == 'en' ]
        # only those tweets that have our pio in them
        poi_tweets = [tweet for tweet in en_tweets if searchFor in tweet and
                      not any(regex.match(tweet) for regex in phrase_regexes)]
 
        if excludeTweetFor:
            poi_tweets = [line for line in poi_tweets 
                           if not any(term  in line for term in excludeTweetFor.lower().split('|')) ]

        if properties.has_key("dumpfile"):
            dumpfile = open(properties['dumpfile'], 'a')
            print>>dumpfile, poi, searchFor, ':'
            for t in poi_tweets:
                print>>dumpfile, '    ', t.encode('utf-8')
            
        
        words = []
        for tweet in poi_tweets:
            tw = tweet.replace(searchFor, '')
            words += [ w for w in tw.split() ]
        
        words_culled = [ w for w in words if w.lower() not in stopset 
                        and w not in excludeTerms.lower().split('|') ]

        freq_dist = nltk.FreqDist(words_culled)
        top_words = [ w for w in freq_dist.keys() if not any(regex.match(w) for regex in word_regexes) ]
        print "POI: " + poi
        wordFreq = ''
        for k in top_words[:5]:   #freq_dist.keys()[:10]:
            print "    ",k,  freq_dist[k]
            wordFreq += k + ' (' + str(freq_dist[k]) + '), '
            if properties.has_key("dumpfile"):
                dumpfile = open(properties['dumpfile'], 'a')
                print>>dumpfile, '    ', k.encode('utf-8') #, top_words[k] #freq_dist[k]

        end = time.time()
        duration = end-start
        cursor.execute("Insert into terms values(?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (ts, poi, searchFor, top_words[0], wordFreq, totalTweets, duration, firstTweet, lastTweet))
        connection.commit()
    
    log.info("End processing at " + time.asctime(time.localtime()) )

    
if __name__ == "__main__":
    main(sys.argv[1:])

