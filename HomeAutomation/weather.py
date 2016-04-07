#!/usr/bin/env python

#import urllib.request
import urllib

def get_weather():
    wetter="ist noch nicht sicher"
    try:
      wp = urllib.urlopen("http://www.wetter.at/wetter/oesterreich/wien/floridsdorf")
      pw = wp.read()
      #print(pw)
      pstring = source_code = pw.decode('utf-8')
      parts=pstring.split('Das Wetter in Floridsdorf heute:')
      wetter=parts[1].split('</div>')
      wetter=wetter[1].replace('\r\n','')
      wetter=wetter.replace('  ',' ')
      wetter=wetter.replace('  ',' ')
      wetter=wetter.replace('  ',' ')
      wetter=wetter.replace('  ',' ')

      print (wetter)
    return wetter