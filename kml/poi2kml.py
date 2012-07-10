#!/usr/bin/python

import sqlite3

connection = sqlite3.connect('../subwayTweets.sqlite')
cursor = connection.cursor()

cursor.execute('select * from pois')
pois=cursor.fetchall()

kmlhead = (
   '<?xml version="1.0" encoding="UTF-8"?>\n'
   '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
   '<Document>' )
kmlfoot= (
   '</Document>'
   '</kml>')

print kmlhead

for poi in pois:
  kml = (
   '  <Placemark>\n'
   '    <name>%s</name>\n'
   '    <Point>\n'
   '      <coordinates>%f,%f,0</coordinates>\n'
   '    </Point>\n'
   '  </Placemark>\n') %(poi[0], poi[2], poi[1])

  print kml

print kmlfoot
