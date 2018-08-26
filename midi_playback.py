import numpy as np
import simpleaudio as sa
from pydub import AudioSegment
import pydub.effects
import audioop as ao
import math
from sf2utils.sf2parse import Sf2File
from midi_IO import FileIO
import copy
import threading
import time


exitFlag = 0

class PlaybackThread(threading.Thread):
    #track_indices = []     #index in track array - where the current index starts
    track_indices_next = []     #real MIDI index - when the next event happens 
    #last_index = 0
    
    def __init__(self, parent, threadID, name, notes, starting_index):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.notes = copy.copy(notes)
        self.ci = starting_index
        self.track_indices = []
        self.parent = parent
        _index_next = 0
        self.last_index = 0
        for x in range(0,len(notes)):
            if notes[x][-1].index > self.last_index:
                self.last_index = notes[x][-1].index
            while _index_next < len(notes[x]) and notes[x][_index_next].index < starting_index:
                _index_next += 1
            self.track_indices.append(_index_next)
        print (self.track_indices)
        
    def run(self):
        print ("Starting " + self.name)
        self.play()
        print ("Exiting " + self.name)
        
    def play(self):
        #Create Audio Canvas
        
        
        for x in range (self.ci,self.last_index+1):
            print (str(100*x/(self.last_index+1-self.ci))+"%")
            _now = time.time()
            
            tempo = 0
            for tc in FileIO.tempo_changes:
                if tc['index'] >Playback.current_index: break
            tempo = tc['tempo_long']
            
            scale = tempo * 1e-6 / FileIO.ticks_per_beat
            tick_length = scale
            
            #tick_length = 
            #tick_length = 1/((tempo / 60) * FileIO.ticks_per_beat) #in seconds
            #print (FileIO.ticks_per_beat)
            #print (tempo)
            #print (tick_length)
            #print (str(x)+":")
            #print (self.track_indices)
            for i,track in enumerate(self.notes):
                if self.track_indices[i] >= len(track): continue
                
                while self.track_indices[i] < len(track) and track[self.track_indices[i]].index <= x:
                    if track[self.track_indices[i]].type != 'event':
                        _audio = self.parent.note_to_audio(FileIO.instruments[i],track[self.track_indices[i]].note,track[self.track_indices[i]].duration*tick_length,track[self.track_indices[i]].velocity)
                    self.track_indices[i] += 1                    

                
                
            #factor = ((FileIO.ticks_per_beat**2)*0.00000175)+(FileIO.ticks_per_beat*-0.0005)+1.04
            #print (factor)
            #_then = _now+tick_length/4000
            #while time.time() < _then:
            #    _then = _then
            #print (tick_length)
            
        
        return
        
        
       # while counter:
       #     if exitFlag:
       #         threadName.exit()
       # time.sleep(delay)
       # print ("%s: %s" % (threadName, time.ctime(time.time())))
       # counter -= 1
        
    

    

class Playback:
    sf2 = None
    #track_indices = [] #real MIDI index (ticks_per_beat etc.)

    notes = None #Copy of notes
    
    def __init__(self,sf2_file):
        Playback.sf2 = Sf2File(open(sf2_file, 'rb'))
    
    
    def stop_playback(self):
        print ("d")
    
    current_index = 0
    
#    def play_tracks(self,notes, index = 0):
#        #Notes has to be list with Tracks ( = List of Event objects)
#        Playback.current_index = index
#        
#        Playback.notes = copy.copy(notes)
#        #Playback.track_indices = [] 
#        Playback.track_next = []  
#        Playback.track_indices_next = [] 
#        
#        min_next_event = math.inf
#        for x in range(0,len(notes)):
#            #Playback.track_indices.append(index)
#            _index_next = 0
#            while _index_next < len(notes[x]) and notes[x][_index_next].index < index:
#                _index_next += 1
#            if _index_next < len(notes[x]):
#                Playback.track_indices_next.append(notes[x][_index_next].index)
#                Playback.track_next.append(_index_next)
#                if Playback.track_indices_next[-1] < min_next_event:
#                    min_next_event = Playback.track_indices_next[-1]
#            else:
#                Playback.track_indices_next.append(-1)
#                Playback.track_next.append(-1)
#            
#        #print (Playback.track_next)
#        #print (Playback.track_indices_next)
#        
#        tempo = 0
#        for tc in FileIO.tempo_changes:
#            if tc['index'] > index: break
#            tempo = tc['tempo']
#        
#        tick_length = 1/((tempo / 60) * FileIO.ticks_per_beat) #in seconds
#        #print (min_next_event)
#        threading.Timer((min_next_event-Playback.current_index)*tick_length, self.play_index).start()
#        Playback.current_index = min_next_event
    def play_tracks(self,notes, index = 0):
        playthread = PlaybackThread(self,1,"Thread",notes,index)
        playthread.start()
        
    def play_index(self):
        #print ("")
        #print (Playback.track_next)
        #print (Playback.track_indices_next)
        tempo = 0
        for tc in FileIO.tempo_changes:
            if tc['index'] >Playback.current_index: break
            tempo = tc['tempo']
        
        tick_length = 1/((tempo / 60) * FileIO.ticks_per_beat) #in seconds
        
        min_next_event = math.inf
        for i,track in enumerate(Playback.notes):
            if Playback.track_next[i] == -1: continue
            if track[Playback.track_next[i]].type != 'event':
                #print (i)
                #print (Playback.track_next[i])
                #print (len(track))
                #print (len(FileIO.instruments))
                
 
                self.play(FileIO.instruments[i],track[Playback.track_next[i]].note,track[Playback.track_next[i]].duration*tick_length,100)
            if Playback.track_next[i]+1 >= len(track):
                #Track playback ended
                Playback.track_next[i] = -1
                Playback.track_indices_next[i] = -1
            else:
                if Playback.track_indices_next[i] < min_next_event:
                    min_next_event = Playback.track_indices_next[i]
        for i,n in enumerate(Playback.track_indices_next):
            if n == min_next_event:                
                Playback.track_next[i] += 1
                Playback.track_indices_next[i] = Playback.notes[i][Playback.track_next[i]].index
        #for i,n in enumerate(Playback.track_indices_next):
        #    Playback.track_indices_next[i] = track[Playback.track_next[i]].index
                
            
        
        
        threading.Timer((min_next_event-Playback.current_index)*tick_length, self.play_index).start()
        Playback.current_index = min_next_event
        
        
        
    
    def play (self,patch=0,note=0,duration=1.0,velocity=64):
        patch += 1
        _audio = self.note_to_audio(patch,note,duration,velocity)
        if not isinstance(_audio, bytes):
            play_obj = sa.play_buffer(_audio.raw_data, _audio.channels, _audio.sample_width, _audio.frame_rate)
        
    
    def note_to_audio(self,patch=0,note=0,duration=1.0,velocity=64): #velocity in 0 - 127
        preset = None
   
        for p in Playback.sf2.presets:
            if hasattr(p,'preset'):
                if p.preset == patch and p.bank == 0:
                    preset = p
                    break
        if preset == None: return bytes([])
        
        instruments = [] #have to be played at the same time
        for bag in preset.bags:

            for gen in bag.gens:
                if bag.gens[gen].oper == 41: #Instrument
                    instruments.append(Playback.sf2.instruments[bag.gens[gen].word])
        sample = None
        final_audio = None
        for instr in instruments:
            for s in instr.bags:
                if s.key_range == None: continue
                if s.key_range[0] <= note and s.key_range[1] >= note:
                    sample = s
                    break
            
            #Get the AHDSR values
            attack = s.volume_envelope_attack
            hold = s.volume_envelope_hold
            decay = s.volume_envelope_decay
            sustain = s.volume_envelope_sustain
            release = s.volume_envelope_release
            if attack==None: attack = 0.0
            if hold==None: hold = 0.0
            if decay==None: decay = 0.0
            if sustain==None: sustain = 0.0
            if release==None: release = 0.0
            
            min_length = attack+hold
            
            
            #Find the right frequency for the correct pitch
            audio = s.sample.raw_sample_data
            swidth = s.sample.sample_width
            sample_rate = s.sample.sample_rate
            base_note = 60
            fine_tune = 0
            if s.fine_tuning != None:
                fine_tune = s.fine_tuning
            if s.base_note != None:
                base_note = s.base_note
            octaves = (note - base_note + (fine_tune / 100)) / 12   
            
            new_sample_rate = int(sample_rate * (2.0 ** octaves))
            
            #Create the initial audio loop     
            channels = int(len(audio) / s.sample.duration / swidth  )    
            loop_begin = s.sample.start_loop*swidth*channels
            loop_length = s.sample.loop_duration*swidth*channels

            
            
            audio_begin = audio[:loop_begin]
            audio_end = audio[(loop_begin+loop_length):]
            audio = audio[loop_begin:(loop_begin+loop_length)]
            
            #How many bytes needed to play AH&R  / Release minus the final audio_end part
            min_bytes = min_length * 44100 * swidth * channels + max(0,release* 44100 * swidth * channels - len(audio_end))
            
            
            #Loop the looping part as much as is needed for after changing the pitch (new_sample_rate)
            bytes_needed = duration*new_sample_rate*swidth*channels - (len(audio_begin))
            bytes_needed = max(bytes_needed, min_bytes)
            
            repeats_f = (bytes_needed / (len(audio)/swidth))
            audio_final = audio_begin
           
            if int(repeats_f) >= 1:
                for x in range(0,int(repeats_f)):
                    audio_final += audio

                    
            audio_final += audio_end
            
            #Change the pitch - length was already increased above (for higher tones)
            raw_audio = AudioSegment.from_raw(audio_final, sample_width=swidth,frame_rate=sample_rate,channels=channels)
         
            
            raw_audio = raw_audio._spawn(raw_audio.raw_data, overrides={'frame_rate': new_sample_rate})
            sample_rate = 44100
            raw_audio = raw_audio.set_frame_rate(sample_rate)
            raw_audio = raw_audio[0:max(duration+release,min_length+release)*1000]
            
            #Set the maximum volume
            current_volume = raw_audio.dBFS
            if velocity <= 0: velocity = 0.00001
            velocity = velocity / 1.27
            target_volume = math.log10(velocity/127)*50 - 10
            
            raw_audio = raw_audio - (current_volume - target_volume)
            
            
            #Set the AHDSR as much as time allows (AHR are always played)
            decay_allowed = int((len(raw_audio) - (attack+hold+release)*1000))
            percentage_decayed =  decay_allowed / decay*1000
            if percentage_decayed >= 1.0:
                final_decay_level = -sustain
            elif percentage_decayed <= 0:
                final_decay_level = 0
                decay_allowed = 0
            else:
                final_decay_level = -sustain*percentage_decayed
            #Attack
            if (attack!=0.0): raw_audio = raw_audio.fade(from_gain=-120.0, start=0, duration=int(attack*1000))
            #Decay
            raw_audio = raw_audio.fade(to_gain=final_decay_level, start=int((attack+hold)*1000), end=int((attack+hold)*1000)+decay_allowed)
            #Release
            raw_audio = raw_audio.fade_out(duration=int(release*1000))
            
            if final_audio == None:
                final_audio = raw_audio
            else:
                final_audio = final_audio.overlay(raw_audio)
               
        return final_audio
        