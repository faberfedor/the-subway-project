#!/usr/bin/python

import tweetstream
import simplejson as json
import pdb
import logging, logging.config, logging.handlers
import math

# Python log levels are : 'DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL'
logging.config.fileConfig('/home/faber/workspace/subway/conf/subwayTweets_logging.conf')
log = logging.getLogger('root')
log.info("Begin")

username="faberfedor"
password = "tu_1t!!"

# see https://dev.twitter.com/discussions/6797 about why we have to
# change our approach.
# Instead of using 1 unit square bounding boxes around our points of
# interest (pois), we will gather up the tweets from a larger boundary
# box, store it, and then filter them after the fact.
#
# This means that most of the work I did this weekend is for nought.
#
# Stoopid twitter!

#pois = [ { "name": "stamford hill",    "lat": 51.494935, "long": -0.246190 },
#        { "name": "oxford circus",    "lat": 51.51517 , "long": -0.14119 },
#        { "name": "charing cross",    "lat": 51.507108, "long": -0.122963 },
#        { "name": "covent garden",    "lat": 51.51308,  "long":  -0.12427 },
#        { "name": "trafalgar square", "lat": 51.5081,   "long": 0.1281 }
#      ]
#pois = [ 
#        { "name": "trafalgar square", "lat": 51.5081,   "long": 0.1281 }
#      ]


# from M3-M25 intersection (near Chertsey) 
# to M11-M25 intersection (between Loughton and Epping)
# locations = ["-0.54,51.40",  "0.12,51.67"]

def getPOI(coords):
    ''' pass in coordinates and see which POI is in the bounding box 
    [[-0.213503, 51.512805], [-0.1053029, 51.512805], [-0.1053029, 51.572068], [-0.213503, 51.572068]]
          SW corner                SE corner                  NE Corner               NW Corner
        west       south        east        south        east         north       west      north
    '''
    north = coords[2][1]
    south = coords[0][1]
    east  = coords[1][1]
    west  = coords[0][0]

    for poi in pois:
        if poi['lat'] <= north and poi['lat'] >= south and poi['long'] <= west and poi['long'] >= east:
            return poi['name']

        # if we're here, no poi was found?!
        return "no poi found"

def getCoords( lat, long, bearing, distance, distance_unit="km", returnAsArray = False ):
    ''' Modified from:
     http://www.sitepoint.com/forums/showthread.php?656315-adding-distance-gps-coordinates-get-bounding-box
    
    bearing is 0 = north, 180 = south, 90 = east, 270 = west
    '''
    if (distance_unit == "m") :
      # Distance is in miles.
      radius = 3963.1676;
    else :
      # distance is in km.
      radius = 6378.1;
  
    #  New latitude in degrees.
    new_latitude = math.degrees(math.asin(math.sin(math.radians(lat)) \
                   * math.cos(distance/radius) \
                   + math.cos(math.radians(lat)) \
                   * math.sin(distance/radius) * \
                   math.cos(math.radians(bearing))));
            
    #  New longitude in degrees.
    new_longitude = math.degrees(math.radians(long) + \
                     math.atan2(math.sin(math.radians(bearing)) * math.sin(distance / radius) * \
                     math.cos(math.radians(lat)), math.cos(distance / radius) - \
                     math.sin(math.radians(lat)) * math.sin(math.radians(new_latitude))));
    
    if (returnAsArray) :
      #  Assign new latitude and longitude to an array to be returned
      #  to the caller.
      coord = { "lat" : str(new_latitude), "long" : str(new_longitude) }  
    
    else :
      # twitter wants long,lat format
      coord = str(new_longitude) + "," + str(new_latitude);
    
    return coord;


# generate bounding boxes of 1 KM around the pois
locations = []

for poi in pois:
    # SE corner
    locations.append(getCoords( poi["lat"], poi["long"], 225, 0.5, distance_unit="km", returnAsArray = False ))
    # NW corner
    locations.append(getCoords( poi["lat"], poi["long"], 45, 0.5, distance_unit="km", returnAsArray = False ))
    
locations_orig = ["-0.54,51.40", "0.12,51.67"]




# Get the tweets being sent from within our bounding boxes
with tweetstream.FilterStream(username, password,  
                              locations=locations) as stream:
  try:
    for tweet in stream:
        print json.dumps(tweet)  
        print ","
        #print tweet['place']['bounding_box']['coordinates']   # [0][1]
        #print "\nPOI:" + getPOI(tweet['place']['bounding_box']['coordinates'][0]) + "\n"
        #print tweet['text'] 
  except Exception, e:
        print ("e.errno  =" + str(e.errno) )
        print("e.strerror =" + e.strerror)
    
