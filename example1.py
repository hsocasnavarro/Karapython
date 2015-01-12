#!/usr/bin/env python

# Extremely simple text-base karaoke application that runs on the console.
# It doesn't play any music, just shows the lyrics. It has no additional 
# requirements. 

import midifile, time, datetime

filename=raw_input('Please enter filename of .mid or .kar file:')
m=midifile.midifile()
m.load_file(filename)
start=datetime.datetime.now()
#start=start-datetime.timedelta(0,15) # To start at a later point

dt=0.
while dt < max(m.kartimes)+2:
    dt=(datetime.datetime.now()-start).total_seconds()
    m.update_karaoke(dt)

    print ''
    print 't=',dt,' of ',max(m.kartimes)
    for iline in range(3):
        print m.karlinea[iline]+'__'+m.karlineb[iline]
    print ''

    time.sleep(.1)


