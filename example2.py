#!/usr/bin/env python

# example1.py is an extremely simple text-based karaoke application that
#  runs on the console. It doesn't play any music, just shows the lyrics. 
# This adds music to example1.py using the power of pygame. 
# Requires: pygame. 

import midifile, time, datetime, sys
import pygame

filename=raw_input('Please enter filename of .mid or .kar file:')
m=midifile.midifile()
m.load_file(filename)

pygame.mixer.init()
pygame.mixer.music.load(filename)
pygame.mixer.music.play(0,0) # Start song at 0 and don't loop
start=datetime.datetime.now()

if not m.karfile:
    print "This is not a karaoke file. I'll just play it"
    while pygame.mixer.music.get_busy():
        time.sleep(1)
    sys.exit(0)


#start=start-datetime.timedelta(0,90) # To start lyrics at a later point
dt=0.
while pygame.mixer.music.get_busy():
    dt=(datetime.datetime.now()-start).total_seconds()
    m.update_karaoke(dt)

    print ''
    print 't=',dt,' of ',max(m.kartimes)
    for iline in range(3):
        print m.karlinea[iline]+'__'+m.karlineb[iline]
    print ''

    time.sleep(.1)


