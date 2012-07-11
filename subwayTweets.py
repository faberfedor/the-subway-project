#!/usr/bin/python

import tweetstream
import simplejson as json
import pdb
import logging, logging.config, logging.handlers
import math
import sqlite3
import time

# Python log levels are : 'DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL'
logging.config.fileConfig('/home/faber/workspace/the-subway-project/conf/subwayTweets_logging.conf')
log = logging.getLogger('root')
log.info("Begin")

username="faberfedor"
password = "tu_1t!!"

database = './subwayTweets.sqlite'
connection = sqlite3.connect(database)
cursor = connection.cursor()
cursor.execute('create table if not exists tweets (ts integer, swLong real, swLat real, neLong real, neLat real, cntrLong real, cntrLat real, tweet text)')


# see https://dev.twitter.com/discussions/6797 about why we have to
# change our approach.
# Instead of using 1 unit square bounding boxes around our points of
# interest (pois), we will gather up the tweets from a larger boundary
# box, store it, and then filter them after the fact.
#
# This means that most of the work I did this weekend is for nought.
#
# Stoopid twitter!
#{ "name": "" , "lat": , "long":},

pois = [{ "name": "stamford hill",     "lat": 51.494935, "long": -0.246190 },
        { "name": "oxford circus",     "lat": 51.51517 , "long": -0.14119 },
        { "name": "charing cross",     "lat": 51.507108, "long": -0.122963 },
        { "name": "covent garden",     "lat": 51.51308,  "long": -0.12427 },
        { "name": "trafalgar square",  "lat": 51.5081,   "long":  0.1281 },
        { "name": "notting hill gate", "lat": 51.509028, "long": -0.1962847},
        { "name": "picadilly circus" , "lat": 51.51022 , "long": -0.13392},
        { "name": "hyde park corner" , "lat": 51.50313 , "long": -0.15278},
        { "name": "lancaster gate" ,   "lat": 51.512083 ,"long": -0.175067},
        { "name": "regent's park" ,    "lat": 51.52344 , "long": -0.14713},
        { "name": "bond street" ,      "lat": 51.51461 , "long": -0.14897},
        { "name": "knightsbridge" ,    "lat": 51.50169 , "long": -0.16030},
        { "name": "mansion house" ,    "lat": 51.51256 , "long": -0.09397}
      ]
#pois = [ 
#        { "name": "trafalgar square", "lat": 51.5081,   "long": 0.1281 }
#      ]

# London
# from M3-M25 intersection (near Chertsey) 
# to M11-M25 intersection (between Loughton and Epping)
#locations = ["-0.54,51.40",  "0.12,51.67"]

def getCenterOfBB(coords, returnAsArray = False ):
    ''' pass in coordinates and see which POI is in the bounding box 
    [[-0.213503, 51.512805], [-0.1053029, 51.512805], [-0.1053029, 51.572068], [-0.213503, 51.572068]]
          SW corner                SE corner                  NE Corner               NW Corner
        west       south        east        south        east         north       west      north
         X           Y           X            Y           X             Y          X          Y

    taken from http://stackoverflow.com/questions/6671183/calculate-the-center-point-of-multiple-latitude-longitude-coordinate-pairs

    this doesn't work so well...becasue we're crossing the Prime Meridian?  
    Look into this instead: http://www.geomidpoint.com/calculation.html

    '''
    # premature optimization and all that...
    swX = math.cos(math.radians(coords[0][1])) + math.cos(math.radians(coords[0][0]))
    swY = math.cos(math.radians(coords[0][1])) + math.sin(math.radians(coords[0][0]))
    swZ = math.sin(math.radians(coords[0][1]))

    neX = math.cos(math.radians(coords[2][1])) + math.cos(math.radians(coords[2][0]))
    neY = math.cos(math.radians(coords[2][1])) + math.sin(math.radians(coords[2][0]))
    neZ = math.sin(math.radians(coords[2][1]))

    avgX = (swX + neX) /2
    avgY = (swY + neY) /2
    avgZ = (swZ + neZ) /2

    ctrLong = math.degrees(math.atan2(avgY, avgX))
    hyp  = math.sqrt((avgX * avgX) + (avgY * avgY))
    ctrLat = math.degrees(math.atan2(avgZ, hyp))
 
    if (returnAsArray) :
      #  Assign new latitude and longitude to an array to be returned
      #  to the caller.
      coord = { "lat" : str(ctrLat), "long" : str(ctrLong) }  
    
    else :
      # twitter wants long,lat format
      coord = str(ctrLong) + "," + str(ctrLat);
    
    return coord;
    
    



def getPOI(coords):
    ''' pass in coordinates and see which POI is in the bounding box 
    [[-0.213503, 51.512805], [-0.1053029, 51.512805], [-0.1053029, 51.572068], [-0.213503, 51.572068]]
          SW corner                SE corner                  NE Corner               NW Corner
        west       south        east        south        east         north       west      north
    '''
    north = coords[2][1]
    south = coords[0][1]
    east  = coords[1][0]
    west  = coords[0][0]

    for poi in pois:
        if poi['lat'] <= north and poi['lat'] >= south and poi['long'] <= west and poi['long'] >= east:
            return poi['name']

        # if we're here, no poi was found
        return False # "no poi found"

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


# generate bounding boxes of 2 KM around the pois
locations = []

for poi in pois:
    # SE corner
    locations.append(getCoords( poi["lat"], poi["long"], 225, 0.5, distance_unit="km", returnAsArray = False ))
    # NW corner
    locations.append(getCoords( poi["lat"], poi["long"], 45 , 0.5, distance_unit="km", returnAsArray = False ))
    

# Get the tweets being sent from within our bounding boxes
with tweetstream.FilterStream(username, password,  
                              locations=locations) as stream:
  try:
    for tweet in stream:
        #print json.dumps(tweet)  
        #if getPOI(tweet['place']['bounding_box']['coordinates'][0]) :
            #print tweet['place']['bounding_box']['coordinates'][0]  #[1]
            #print "\nPOI:" + getPOI(tweet['place']['bounding_box']['coordinates'][0]) + "\n"
            #print tweet['text'] 
        coords = tweet['place']['bounding_box']['coordinates'][0]
        swLong = coords[0][0] 
        swLat  = coords[0][1]
        neLong = coords[2][0]
        neLat  = coords[2][1]
        center =  getCenterOfBB(coords, returnAsArray = True )

        text = tweet['text']
        ts = int(time.time())
        cursor.execute("Insert into tweets values( ?, ?, ?, ?, ?, ?, ?, ?)" , 
                                  (ts, swLong, swLat, neLong, neLat, center['long'], center['lat'], text))
        connection.commit()

  except Exception, e:
        print (e)
        #print("e.strerror =" + e.strerror)
    
