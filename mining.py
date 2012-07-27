#!/usr/bin/python
import os, sys
import twitter
import nltk
import json, yaml
import re
from languageDetection import *
import logging, logging.config, logging.handlers
import time
import pdb
import argparse

'''
TODO
    put exception handling around the twitter search
    add logging
    add debug mode
    write term to database
    implement CLI

'''

logging.config.fileConfig('conf/logging.conf')
log = logging.getLogger('root')

debug = True
properties = dict()

regexes = [
    re.compile("[^\w\s]"),
    re.compile(r"\brt\b"),
    re.compile("&amp")
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
    

def getPOIs():

    if 'poi' in properties:  # override the file if a single POI is passed in
        pois = [ properties['poi'] ]
    else:
        pois = open(properties['poisfile']).read().split('\n')
        # remove blank line caused by EOL on last line
        pois.pop()

    return pois

def main(args):

    log.info("Begin processing at " + time.asctime(time.localtime()) )

    parseArgs()

    twitter_search= twitter.Twitter(domain="search.twitter.com")
   
    pois = getPOIs()
 
    for poi in pois:
        search_results = []
        
        twitters=twitter_search.search(q=poi, rpp=100, page=1)
                
        for page in range(1,6):
            search_results.append(twitters)
        
        tweets = [ r['text'] for result in search_results for r in result['results'] ]
        en_tweets = [ tweet for tweet in tweets if ld.detect(tweet) == 'en' ]

        if properties.has_key("dumpfile"):
            dumpfile = open(properties['dumpfile'], 'a')
            print>>dumpfile, poi, ':'
            for t in en_tweets:
                print>>dumpfile, '    ', t.encode('utf-8')
            
        
        words = []
        for tweet in en_tweets:
            tw = tweet.lower().replace(poi.lower(), '')
            #t = tw # just until we get the previous line to work
            words += [ w for w in tw.split() ]
        
        words_culled = [  w for w in words if w.lower() not in nltk.corpus.stopwords.words('english') ]
        
        freq_dist = nltk.FreqDist(words_culled)
        top_words = [ w for w in freq_dist.keys() if not any(regex.match(w) for regex in regexes) ]
        print "POI: " + poi
        for k in top_words[:5]:   #freq_dist.keys()[:10]:
            print "    ",k, freq_dist[k]
            if properties.has_key("dumpfile"):
                dumpfile = open(properties['dumpfile'], 'a')
                print>>dumpfile, '    ', k.encode('utf-8'), freq_dist[k]
    
    log.info("End processing at " + time.asctime(time.localtime()) )

    
if __name__ == "__main__":
    main(sys.argv[1:])

