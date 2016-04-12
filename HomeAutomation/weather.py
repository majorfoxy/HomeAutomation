#!/usr/bin/env python

#import urllib.request
import urllib

def get_weather():
    wetter="Das Wetter in Floridsdorf ist noch nicht sicher."
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
      wetter=("Das Wetter in Floridsdorf heute: %s " % wetter)

      print (wetter)
    except Exception, e:
        import traceback  
        print traceback.format_exc()     
    return wetter