#!/usr/bin/python

import sqlite3

connection = sqlite3.connect('../subwayTweets.sqlite')
cursor = connection.cursor()

cursor.execute('select swLong, swLat, neLong, neLat from tweets limit 100')
tweets=cursor.fetchall()

kmlhead = (
   '<?xml version="1.0" encoding="UTF-8"?>\n'
   '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
   '<Document>' )
kmlfoot= (
   '</Document>'
   '</kml>')

print kmlhead,

for t in tweets:
  kml = (
   '<Placemark>'
   '<Polygon>\n'
   '  <extrude>1</extrude>\n'
   '  <altitudeMode>relativeToGround</altitudeMode>\n'
   '  <outerBoundaryIs>\n'
   '    <LinearRing>\n'
   '      <coordinates> %f,%f,0\n'
   '        %f,%f,0\n'
   '        %f,%f,0\n'
   '        %f,%f,0\n'
   '        %f,%f,0 </coordinates>\n'
   '    </LinearRing>\n'
   '  </outerBoundaryIs>\n'
   '</Polygon>\n' 
   '</Placemark>' ) % ( t[0],t[1], t[2],t[1], t[2],t[3], t[0],t[3], t[0],t[1] ) 

  print kml,

print kmlfoot
