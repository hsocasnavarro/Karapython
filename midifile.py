#!/usr/bin/env python
#
# (c) 2015 Hector Socas-Navarro (hsocas.iac@gmail.com)
#

import struct, re
class midifile:

    # Used specs from http://www.midi.org/techspecs/midimessages.php
    # http://www.blitter.com/~russtopia/MIDI/~jglatt/tech/midifile.htm

    """ 
This module defines the class midifile which may be used to parse and
extract information from MIDI (.mid) files and Karaoke (.kar) files. 
This can be useful to analyze a MIDI file or as a back-end for a
karaoke player. The class midifile creates an object that is associated
to the MIDI (or .kar) file being parsed.  The following instance attributes
are defined:


ATTRIBUTES:

        fileobject: A file type associated to the .mid or .kar file

        error : Error condition upon exit from the class methods. It's False
      if no error or some other type depending on the error condition

    Tempo-related quantities: The tempo can change at any time, so the
      following quantities related to the tempo are defined as a list
      containing all the values taken and the real time (in seconds)
      at which something related to the tempo changed. For instance,
      if we have a song with three different values of the BPM (say,
      it started at 60, changed to 90 after two mintes and then went
      back to 90 after 30 seconds), we have that all tempo-related
      variables are lists of three elements. Each element is, in turn,
      a list of two elements. The first element is the value itself and
      the second is the real time at which it changed. So in this example
      we would have bpm=[ [60,0.], [90,120], [60,150] ]
     
        bpm=[[120,0.]] # Midi default

    	microsecondsperquarternote=[[60000000./120,0.]] # Midi default

	num=[[4, 0.]] # Midi default

    	den=[[4, 0.]] # Midi default
    
    For karaoke .kar files
    	karfile=Boolean that indicates whether the file has karaoke 
     information in the .kar format

     	kartrack=Track number (starting with 0) with the karaoke information

    	karsyl=List of strings with the kar syllabes 

    	kartimes=list of strings with the real-time (in seconds) associated 
     to the kar syllabes

     	karlinea=A list of three strings corresponding to the three lines
     that can be displayed in the karaoke. Note: Three lines is the 
     maximum that this program can handle!! Here we have the part of the
     text that has already been read and is usually displayed in a different
     color.    

    	karlineb=Same as above but for the text that has not yet been read
     (usually displayed by karaokes on white color). As time goes by, 
     syllabes from this string are removed and appended to the karlinea
     string above

    Track information
       ntracks=Number of tracks in the file

       tracknames=List of strings with the names of each track

    MIDI note information 
       patchesused=A list of lists, each element
       containing the patches (instruments) used in the file, the
       track number in which it was used and the time at which the
       midi program change event was recorded

       notes=A list containing the note events. Each element has the
     information for each note played, with the following values:
     [note_number, velocity, channel, patch, track, time_start, time_end]
     time_start and time_end are real time in seconds. Time_end
     is the time in which a note_off event (or a note_on with 0 velocity)
     was registered for this note. Some notes may not have an associated
     note_off event, in which case, time_end is set to -1. If two
     note_on events are registered for the same note without a note_off
     event in between, then the time_end for the first note is set to
     the time_start of the second note. Note on and note off matching is 
     done across tracks but not across patches, so a piano C4 is not 
     considered the same note as a guitar C4.


METHODS:

   The following methods are exposed by the class:

   load_file() : This method parses the .mid or .kar file and sets
     the corresponding class attributes. Should be called before
     using any of the attributes.

   update_karaoke(dt): The input argument dt is a float with the time
     in seconds elapsed since the start of the song. This method then
     checks the karaoke information and updates the related attributes 
     (particularly karlinea and karlineb) so that they can be used
     by the caller. Need to have run load_file() before.

   write_file(filein, fileout, tracks2remove, patches2remove): This
     method replicates a MIDI or karaoke file with the option to
     supress one or more tracks and/or instruments. filein and fileout
     are strings with the corresponding filenames (filein must exist and
     fileout will be overwritten). tracks2remove and patches2remove may
     be either None or a list (can be an empty list) of integers with
     the numbers of tracks or instruments that are not wanted in the
     output file.



EXAMPLES:

     With this module there are some very simple examples that illustrate
     possible use cases. example1.py is an extremely simple text-based
     karaoke application that runs on the console. It doesn't play any
     music, just shows the lyrics. It has no additional requirements. 
     example2.py adds music to it using pygame. Requires: pygame. 
     example3.py shows how to use pygame to build a graphic frontend for
     a karaoke application. Requires: pygame.

     Below is a very simple usecase:

import datetime, time, midifile

m=midifile.midifile()
m.load_file('myfile.kar')

# Show first karaoke line at song point 15 seconds
m.update_karaoke(15)
print m.karlinea[0]+'__'+m.karlineb[0]
"""

    def __init__(self):

        # Instance attributes
        self.fileobject=None
        self.closeonreturn=False
        self.error=False
        # Tempo and real time at which it was set
        self.bpm=[[120,0.]] # bpm using actual time signature
        self.microsecondsperquarternote=[[60000000./120,0.]]
        self.num=[[4, 0.]]
        self.den=[[4, 0.]]
        # For karaoke .kar files
        self.karfile=False
        self.kartrack=0
        self.karsyl=list()
        self.kartimes=list()
        self.karlinea=['']*3
        self.karlineb=['']*3
        self.karievent0=[-1]*3
        self.karievent1=[-1]*3
        self.karidx=0
        # Track information
        self.ntracks=0
        self.tracknames=list()
        # Note information
        self.patchesused=list()
        self.notes=list()
        return

    def read_var_length(self):
        read=129
        values=list()
        while read > 0b10000000:
            read=struct.unpack('>B',self.fileobject.read(1))[0]
            values.append(read)
        iread=len(values)
        var=values[iread-1] # Least-significant byte
        for i in range(iread-1):
            var=var+(values[i]-128)*(128**(iread-1-i))

        bytesread=struct.pack('B'*iread,*values)

        return [var,iread,bytesread] # Return value and number of bytes read


    def load_file(self,fileobject):
        
        if type(fileobject) == str:
            self.fileobject=open(fileobject,'rb')
            self.closeonreturn=True
        else:
            self.fileobject=fileobject

        headerid=str(self.fileobject.read(4))
        headerlen=struct.unpack('>I',self.fileobject.read(4))[0] # > is for big-endian, i for integer
        fileformat=struct.unpack('>H',self.fileobject.read(2))[0]
        self.ntracks=struct.unpack('>H',self.fileobject.read(2))[0]
        self.tracknames=['']*self.ntracks
        division=struct.unpack('>h',self.fileobject.read(2))[0] # Ticks per quarter note
        if division < 0: # It's a different format SMTPE
            self.error=1
            if self.closeonreturn:
                self.fileobject.close()
            return self.error

        for itrack in range(self.ntracks):
            currentpatch=0
            mastertime=0
            trackid=str(self.fileobject.read(4))
            tracklen=struct.unpack('>I',self.fileobject.read(4))[0]
            # track event
            metatype=0
            iread=0
            while iread < tracklen and metatype != 0x2f:
                [dtime,nbytesread,bytesread]=self.read_var_length()
                iread=iread+nbytesread
                # Midi event
                status=struct.unpack('>B',self.fileobject.read(1))[0]
                iread=iread+1

                # Set timing conversion. Find tempo for previous event at mastertime
                i0=len(self.microsecondsperquarternote)-1
                while (self.microsecondsperquarternote[i0][1]) > mastertime:
                    i0=i0-1
                # Try with that tempo
                tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                secondspertick=1./tickspermicrosecond*1e-6
                dtimesec=dtime*secondspertick
                # Check if there has been a tempo change in that interval
                i1=len(self.microsecondsperquarternote)-1
                while (self.microsecondsperquarternote[i1][1]) > mastertime+dtimesec:
                    i1=i1-1
                if i1 != i0: # Tempo has changed. Recompute using MIDI steps
                    tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                    secondspertick0=1./tickspermicrosecond*1e-6
                    tickspermicrosecond=division/self.microsecondsperquarternote[i1][0]
                    secondspertick1=1./tickspermicrosecond*1e-6
                    dtimesec=0.
                    for itick in range(dtime):
                        if mastertime+dtimesec <  self.microsecondsperquarternote[i1][1]:
                            dtimesec=dtimesec+secondspertick0
                        else:
                            dtimesec=dtimesec+secondspertick1


                else: # No tempo change. Proceed with value at i0            
                    tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                    secondspertick=1./tickspermicrosecond*1e-6
                    dtimesec=dtime*secondspertick

                mastertime=mastertime+dtimesec

                if status == 0xFF: # It's a non-MIDI event, META event
                    metatype=struct.unpack('>B',self.fileobject.read(1))[0]
                    iread=iread+1
                    [l,nb,bytesread]=self.read_var_length()
                    iread=iread+nb
                    data=self.fileobject.read(l)
                    iread=iread+l
                    if metatype == 0x51: # Set tempo
                        tt=struct.unpack('>BBB',data)
                        self.microsecondsperquarternote.append([tt[0]*65536.+tt[1]*256.+tt[2],mastertime])
                        self.bpm.append([60000000. / self.microsecondsperquarternote[-1][0] * (self.den[-1][0] / self.num[-1][0]), mastertime])
                        self.num.append([self.num[-1][0], mastertime])
                        self.den.append([self.den[-1][0], mastertime])
                    if metatype == 0x58: # Time signature
                        d=struct.unpack('>BBBB',data)
                        self.num.append([float(d[0]),mastertime])
                        self.den.append([float(d[1]**2),mastertime])
                        self.microsecondsperquarternote.append([self.microsecondsperquarternote[-1][0], mastertime])
                        self.bpm.append([self.bpm[-1][0], mastertime])
                    if metatype == 0x1:
                        if data == '@KMIDI KARAOKE FILE':
                            self.karfile=True
                            self.kartrack=itrack+1
                        if self.karfile and itrack == self.kartrack:
                            if data[0] != '@':
                                if '\\' in data:
                                    self.karsyl.append('\\')
                                    self.kartimes.append(mastertime)
                                    data=re.sub('\\\\','',data)
                                if '/' in data:
                                    self.karsyl.append('/')
                                    self.kartimes.append(mastertime)
                                    data=re.sub('/','',data)
                                self.karsyl.append(data)
                                self.kartimes.append(mastertime)    
                    if metatype == 0x3: # Track name
                        self.tracknames[itrack]=data
                    if metatype == 0x2F: # End of track
                        pass 

                elif status == 0xF0 or status == 0xF7: # Now a Sysex event
                    [l,nb,bytesread]=self.read_var_length()
                    iread=iread+nb
                    data=self.fileobject.read(l)
                    iread=iread+l

                else: # MIDI messages
                    if status < 128: # Use running status instead
                        status=runningstatus
                        self.fileobject.seek(-1,1)
                        iread=iread-1
                    status1 = status / 16
                    status2 = status % 16
                    channel=status2
                    if status1 == 0b1100: # Program change
                        read=struct.unpack('>B',self.fileobject.read(1))[0]
                        currentpatch=read
                        self.patchesused.append([itrack,currentpatch,mastertime])
                        iread=iread+1
                    elif status1 == 0b1101: # After-touch
                        read=struct.unpack('>B',self.fileobject.read(1))[0]
                        iread=iread+1
                    else:
                        data1=struct.unpack('>B',self.fileobject.read(1))[0]
                        data2=struct.unpack('>B',self.fileobject.read(1))[0]
                        iread=iread+2
                    if status1 == 0b1001 and data2 > 0: # Note on event
                        self.notes.append([data1,data2,status2,currentpatch,itrack,mastertime,-1])
                        inote=len(self.notes)-1 # If it was previously on, count it off
                        while inote >= 0:
                            if self.notes[inote][0] == data1 and self.notes[inote][2] == currentpatch:
                                self.notes[inote][5] == mastertime # Time note off
                                break
                            inote=inote-1
                    elif status1 == 0b1000 or (status1 == 0b1001 and data2 == 0): # Note off event
                        inote=len(self.notes)-1
                        while inote >= 0:
                            if self.notes[inote][0] == data1 and self.notes[inote][2] == currentpatch:
                                self.notes[inote][5] == mastertime # Time note off
                                break
                            inote=inote-1
                    runningstatus=status
                # End MIDI event


        if self.closeonreturn:
            self.fileobject.close()
        return self.error


    def update_karaoke(self, dt):
        if not self.karfile or self.kartrack == 0 or len(self.karsyl) == 0:
            return
        if self.karidx >= len(self.karsyl)-1:
            return
        dt0=self.kartimes[self.karidx]
        while dt > dt0 and self.karidx < len(self.kartimes)-1:
            self.karidx=self.karidx+1
            dt0=self.kartimes[self.karidx]
        self.karidx=max(self.karidx-1,0)
        if self.karidx == self.karievent1[2]: # If reached the end of 3 lines,
            self.karidx=self.karidx+1 # Make sure next 3 lines are displayed
        self.karidx=min(self.karidx,len(self.kartimes)-1)
        if self.karidx > self.karievent1[2]: # Clear and load next three lines
            self.karlinea=['']*3
            self.karlineb=['']*3
            self.karievent0=[len(self.karsyl)-1]*3
            self.karievent1=[len(self.karsyl)-1]*3
            self.karievent0[0]=self.karidx            
            idx=self.karidx+1
            iline=0
            while idx <= len(self.karsyl)-1:
                if self.karsyl[idx]== '/': # Next line
                    self.karievent1[iline]=idx-1
                    iline=iline+1
                    if iline == 3:
                        break
                    self.karievent0[iline]=idx+1
                if self.karsyl[idx] == '\\': # End of three lines
                    self.karievent1[iline]=idx-1
                    if iline < 2:
                        for i in range(iline+1,3):
                            self.karievent0[i]=idx-1
                            self.karievent1[i]=idx-1
                    break
                idx=idx+1

        for iline in range(3): # Colored text
            if self.karievent0[iline] == self.karievent1[iline]:
                self.karlinea[iline]=''
                continue
            i0=self.karievent0[iline]
            i1=self.karidx
            if i1 < self.karievent0[iline]:
                self.karlinea[iline]=''
                continue
            if i1 > self.karievent1[iline]:
                i1=self.karievent1[iline]
            self.karlinea[iline]=''.join(self.karsyl[i0:i1+1])
            self.karlinea[iline]=re.sub('\\\\','',self.karlinea[iline])
            self.karlinea[iline]=re.sub('/','',self.karlinea[iline])
        for iline in range(3): # White text
            if self.karievent0[iline] == self.karievent1[iline]:
                self.karlineb[iline]=''
                continue
            i0=self.karidx+1
            if i0 < self.karievent0[iline]:
                i0=self.karievent0[iline]
            i1=self.karievent1[iline]
            if i0 > i1:
                self.karlineb[iline]=''
                continue
            if self.karievent1[iline] < i0:
                i0=self.karidx
            self.karlineb[iline]=''.join(self.karsyl[i0:i1+1])
            self.karlineb[iline]=re.sub('\\\\','',self.karlineb[iline])
            self.karlineb[iline]=re.sub('/','',self.karlineb[iline])

        # Special case for song end
        if dt >= max(self.kartimes):
            for iline in range(-2,1):
                if self.karlinea[iline] != '':
                    self.karlinea[iline]=''.join(self.karsyl[self.karievent0[iline]:])
                    self.karlinea[iline]=re.sub('\\\\','',self.karlinea[iline])
                    self.karlinea[iline]=re.sub('/','',self.karlinea[iline])
                    self.karlineb[iline]=''
                    break

        return False


    def write_file(self,filein,fileout,tracks2remove,patches2remove):
        if tracks2remove == None:
            tracks2remove=list()
        if patches2remove == None:
            patches2remove=list()
        
        fout=open(fileout,'wb')
        if type(filein) == str:
            self.fileobject=open(filein,'rb')
            self.closeonreturn=True
        else:
            self.fileobject=filein

        headerid=self.fileobject.read(4)
        fout.write(headerid)
        headerlen=self.fileobject.read(4)
        fout.write(headerlen)
        fileformat=self.fileobject.read(2)
        fout.write(fileformat)
        ntracks=self.fileobject.read(2)
        ntracks=struct.unpack('>H',ntracks)[0]
        ntracks2=ntracks-len(tracks2remove)
        fout.write(struct.pack('>H',ntracks2))
        tracknames=['']*ntracks
        division=self.fileobject.read(2)
        fout.write(division)
        division=struct.unpack('>h',division)[0]
        if division < 0: # It's a different format SMTPE
            error=1
            fout.close()
            if closeonreturn:
                self.fileobject.close()
            return error

        for itrack in range(ntracks):
            writetrack=True
            if itrack in tracks2remove:
                writetrack=False
            currentpatch=0
            mastertime=0
            trackid=self.fileobject.read(4)
            if writetrack:
                fout.write(trackid)
            read=self.fileobject.read(4)
            if writetrack:
                fout.write(read)
            tracklen=struct.unpack('>I',read)[0]
            # track event
            metatype=0
            iread=0
            while iread < tracklen and metatype != 0x2f:
                [dtime,nbytesread,bytesread]=self.read_var_length()
                if writetrack:
                    fout.write(bytesread)
                iread=iread+nbytesread
                # Midi event
                read=self.fileobject.read(1)
                if writetrack:
                    fout.write(read)
                status=struct.unpack('>B',read)[0]
                iread=iread+1

                # Set timing conversion. Find tempo for previous event at mastertime
                i0=len(self.microsecondsperquarternote)-1
                while (self.microsecondsperquarternote[i0][1]) > mastertime:
                    i0=i0-1
                # Try with that tempo
                tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                secondspertick=1./tickspermicrosecond*1e-6
                dtimesec=dtime*secondspertick
                # Check if there has been a tempo change in that interval
                i1=len(self.microsecondsperquarternote)-1
                while (self.microsecondsperquarternote[i1][1]) > mastertime+dtimesec:
                    i1=i1-1
                if i1 != i0: # Tempo has changed. Recompute using MIDI steps
                    tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                    secondspertick0=1./tickspermicrosecond*1e-6
                    tickspermicrosecond=division/self.microsecondsperquarternote[i1][0]
                    secondspertick1=1./tickspermicrosecond*1e-6
                    dtimesec=0.
                    for itick in range(dtime):
                        if mastertime+dtimesec <  self.microsecondsperquarternote[i1][1]:
                            dtimesec=dtimesec+secondspertick0
                        else:
                            dtimesec=dtimesec+secondspertick1


                else: # No tempo change. Proceed with value at i0            
                    tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                    secondspertick=1./tickspermicrosecond*1e-6
                    dtimesec=dtime*secondspertick

                mastertime=mastertime+dtimesec

                if status == 0xFF: # It's a non-MIDI event, META event
                    read=self.fileobject.read(1)
                    metatype=struct.unpack('>B',read)[0]
                    if writetrack:
                        fout.write(read)
                    iread=iread+1
                    [l,nb,bytesread]=self.read_var_length()
                    if writetrack:
                        fout.write(bytesread)
                    iread=iread+nb
                    data=self.fileobject.read(l)
                    if writetrack:
                        fout.write(data)
                    iread=iread+l
                    if metatype == 0x51: # Set tempo
                        tt=struct.unpack('>BBB',data)
                    if metatype == 0x58: # Time signature
                        d=struct.unpack('>BBBB',data)

                elif status == 0xF0 or status == 0xF7: # Now a Sysex event
                    [l,nb,bytesread]=self.read_var_length()
                    if writetrack:
                        fout.write(bytesread)
                    iread=iread+nb
                    data=self.fileobject.read(l)
                    if writetrack:
                        fout.write(data)
                    iread=iread+l

                else: # MIDI messages
                    if status < 128: # Use running status instead
                        status=runningstatus
                        self.fileobject.seek(-1,1)
                        if writetrack:
                            fout.seek(-1,1)
                        iread=iread-1
                    status1 = status / 16
                    status2 = status % 16
                    channel=status2

                    writeevent=True
                    if currentpatch in patches2remove:
                        writeevent=False

                    if status1 == 0b1100: # Program change
                        read=self.fileobject.read(1)
                        if writetrack:
                            fout.write(read)
                        read=struct.unpack('>B',read)[0]
                        currentpatch=read
                        iread=iread+1
                    elif status1 == 0b1101: # After-touch
                        read=self.fileobject.read(1)
                        if writetrack:
                            fout.write(read)
                        read=struct.unpack('>B',read)[0]
                        iread=iread+1
                    else:
                        read1=self.fileobject.read(1)
                        read2=self.fileobject.read(1)
                        if writetrack:
                            if not writeevent:
                                read2=struct.pack('>B',0)
                            fout.write(read1)
                            fout.write(read2)
                        data1=struct.unpack('>B',read1)[0]
                        data2=struct.unpack('>B',read2)[0]
                        iread=iread+2

                    runningstatus=status
                # End MIDI event


        fout.close()
        if self.closeonreturn:
            self.fileobject.close()
        return self.error
