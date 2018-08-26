from mido import MidiFile
from mido import Message
from mido import MidiTrack
from midi_IO import *
import copy

class Tools:
    
    def get_channels(patches):
        #Returns a list of channels for the instrument list.
        #Same instruments should get the same channel, channel 10 should be skipped
        channels = []
        index = 0
        for x in range(0,len(patches)):
            
            found = False
            for y in range(0,x):
                if patches[y] == patches[x]: 
                    found = True
                    break
            
            if found:
                channels.append(channels[y])
            else:           
                channels.append(index)
                index += 1
            
            if index == 9: index += 1
        return channels
            
        
    
    def unify_lengths(notes):
        resolution = int((1/4)*FileIO.ticks_per_beat)
        for track in notes:
            for inx,note in enumerate(track):
                note.index = int(int(round(note.index/resolution)) * resolution)
                note.duration = int(int(round(note.duration/resolution)) * resolution)
                if note.duration == 0:
                    note.duration = resolution
        return notes
    
     
        
    def transpose_notes (notes, measure_start = -1, measure_end = -1, beat_start = -1, beat_end = -1, track = -1, amount = 0):
        
        if track == -1: #all tracks
            cnt = 0
            for tr in notes:
               notes = Tools.transpose_track (notes,cnt, measure_start=measure_start, measure_end=measure_end, beat_start=beat_start, beat_end=beat_end, amount=amount) 
               cnt = cnt + 1
        else: #single track
            notes = Tools.transpose_track (notes, track, measure_start, measure_end, beat_start, beat_end, amount) 
        return notes
    
    
    
    def transpose_track (notes,track, measure_start = -1, measure_end = -1, beat_start = -1, beat_end = -1, amount = 0):
        if measure_start == -1 and beat_start == -1:
            beat_start = 0
        if measure_end == -1 and measure_end == -1:
            beat_end = Tools.amount_beats(notes[track])
        
        if beat_start == -1: #so measure_start > -1
            beat_start = Tools.current_beat(measure_start,0)
        
        if beat_end == -1: #so measure_end > -1
            beat_end = Tools.current_beat(measure_end,0)
            
        for note in notes[track]:
            if note.beat_index >= beat_end:
                break
            if note.beat_index >= beat_start:
                note.note += amount
        
        return notes
        
    def set_duration (notes, measure_start = -1, measure_end = -1, beat_start = -1, beat_end = -1, track = -1, duration = -1, beats = -1):
        
        if track == -1: #all tracks
            cnt = 0
            for tr in notes:
               notes = Tools.set_duration_track (notes,cnt, measure_start=measure_start, measure_end=measure_end, beat_start=beat_start, beat_end=beat_end, duration=duration, beats= beats) 
               cnt = cnt + 1
        else: #single track
            notes = Tools.set_duration_track (notes, track, measure_start, measure_end, beat_start, beat_end, duration, beats) 
        return notes
    
    
    
    def set_duration_track (notes,track, measure_start = -1, measure_end = -1, beat_start = -1, beat_end = -1, duration = -1, beats = -1):
        if measure_start == -1 and beat_start == -1:
            beat_start = 0
        if measure_end == -1 and measure_end == -1:
            beat_end = Tools.amount_beats(notes[track])
            
        if duration == -1:
            duration = beats * FileIO.ticks_per_beat
        if beats == -1:
            beats = duration / FileIO.ticks_per_beat
        if duration * beats < 0:
            return notes
        
        if beat_start == -1: #so measure_start > -1
            beat_start = Tools.current_beat(measure_start,0)
        
        if beat_end == -1: #so measure_end > -1
            beat_end = Tools.current_beat(measure_end,0)
            
        for note in notes[track]:
            if note.beat_index >= beat_end:
                break
            if note.beat_index >= beat_start:
                note.beats = beats
                note.duration = duration
        
        return notes
            
    
    def amount_beats (track):
        return track[-1].beat_index
       
    def amount_indices (track):
        return track[-1].index
        
    def current_beat (measure, beats_in):
        last_beats = 4
        beats = 0
        for bc in FileIO.beat_changes:
            measures_passed = bc['increment'] / last_beats
            #print (str(measures_passed)+' - '+str(measure))
            if measures_passed >= measure:
                
                return beats + (measure * last_beats) + beats_in
            else:
                measure -= measures_passed
                beats += measures_passed * last_beats
            last_beats = bc['beats']
            #print (last_beats)
        return 0  
        
    def insert_note_at (notes, track, note, beats=1, beat_index=-1, measure=0, beats_in_measure=0, channel=0):
        if beat_index == -1:
            beat_index = Tools.current_beat(measure,beats_in_measure)
            
        new_note = Event(type='note',msg=Message("note_on"),beat_index=beat_index, note=note, octave = int(note / 12),channel = channel, beats=beats)

                
        cnt = 0
        for note in notes[track]:
            if note.beat_index >= beat_index:
                notes[track].insert(cnt,new_note)
                break
            cnt += 1
        
        # for note in notes[track]:
        #     print (note.__dict__)
        return notes
        
        
    def get_note(octave, note):
        val = str(note)
        if val.isdigit():
            return octave*12 + note
        else:
            tones = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B','C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
            cnt = 0
            int_val = 0
            for tone in tones:
                if tone == val:
                    int_val = cnt % 12
                    break
                cnt += 1
            return octave*12 + int_val
        
            
    def combine_tracks(notes):
        print ("..Combining all tracks..")
    
        final = []
        
        indices = {}
        cnt = 0
        for track in notes:
            indices[cnt] = 0
            cnt += 1
        
        # 1.) Find longest track (by duration)
        longest = 0
        for track in notes:
            if len(track)>0:
                a = track[-1].index
                if a > longest:
                    longest = a
        
        # 2.) Go from 0 to that end
        for x in range(0,longest):


            cnt = 0
            # 3.) Check for every number quickly if a track has a note for that position
            for track in notes:
                # 4.) if yes, add them to the final stack

                
                while (indices[cnt] < len(track) and track[indices[cnt]].index == x):
                    final.append(track[indices[cnt]])
                    indices[cnt] += 1
                cnt += 1
        
        
        
        # 5.) Delete Control and program changes
        final2 = []
        for f in final:
            if not (f.msg.type == 'program_change' or f.msg.type == 'control_change' or f.msg.type == 'track_name' or f.msg.type == 'midi_port' or f.msg.type == 'channel_prefix'):
                f.channel = 0
                final2.append(f)
        
        # 5.) find overlapping notes and delete them
        seen = set()
        seen_add = seen.add
        final2 = [x for x in final2 if not ((str(x.index) + str(x.note)) in seen or seen_add((str(x.index) + str(x.note))))]

        
        new_notes = []
        new_notes.append(final2)
        
        
        return new_notes
    
    def combine_tracks_groups(notes,groups):
        print ("..Combining tracks into groups..")
        new_notes = []
        for group in groups:
            final = []
            
            indices = {}
            cnt = 0
            for i,track in enumerate(notes):
                if not i in group: continue
                indices[cnt] = 0
                cnt += 1
            
            # 1.) Find longest track (by duration)
            longest = 0
            for i,track in enumerate(notes):
                if len(track)>0:
                    a = track[-1].index
                    if a > longest:
                        longest = a
            
            # 2.) Go from 0 to that end
            for x in range(0,longest):
    
    
                cnt = 0
                # 3.) Check for every number quickly if a track has a note for that position
                for i,track in enumerate(notes):
                    # 4.) if yes, add them to the final stack
                    if not i in group: continue
                    
                    while (indices[cnt] < len(track) and track[indices[cnt]].index == x):
                        final.append(track[indices[cnt]])
                        indices[cnt] += 1
                    cnt += 1
            
            
            
            # 5.) Delete Control and program changes
            final2 = []
            for f in final:
                if not (f.msg.type == 'program_change' or f.msg.type == 'control_change' or f.msg.type == 'track_name' or f.msg.type == 'midi_port' or f.msg.type == 'channel_prefix'):
                    f.channel = 0
                    final2.append(f)
            
            # 5.) find overlapping notes and delete them
            seen = set()
            seen_add = seen.add
            final2 = [x for x in final2 if not ((str(x.index) + str(x.note)) in seen or seen_add((str(x.index) + str(x.note))))]

            new_notes.append(final2)
        return new_notes
    
    def find_chords(tones):
        ci = 0
        this_index = []
        chords = []
        collection = [] #Keeps a collection of all the past few tones
        first_index = 0
        
        def turn_into_list(co,which):
            
            if which != -1:
                min = co[0][which].note 
            else:
                min = co[0][0].note 
            
            begin = 1
            if which == -1:
                begin = 0
            
            for x in range(begin,len(co)):
                for y in range(0,len(co[x])):
                    if co[x][y].note < min:
                        min = co[x][y].note
            
            ret_val = []
            ret_val.append(min % 12)  #So the lowest tone stays the bass tone
            
            ret_val.append(co[0][which].note % 12)
            for x in range(begin,len(co)):
                for y in range(0,len(co[x])):
                    ret_val.append(copy.copy(co[x][y].note % 12))
            #print (ret_val)
            return ret_val
            
            
        last_output_chord = None
       
        for inx,note in enumerate(tones):
                
            if note.index != ci:
                if len(collection)>0:
                    first_index = collection[0][0].index
                tone_list = []
                for tone in this_index:
                    if tone.type == 'event': continue
                    tone_list.append(tone.note % 12)
               
                #Create the chord or tone of the current index (might be overwritten)
                chor = Chord()
                chor.set_chord(copy.copy(tone_list))
   
                
                #Add current chord or tone to collection list
                sanitized = []
                for tone in this_index:
                    if tone.type != 'event':
                        sanitized.append(copy.copy(tone))
                
                
                #Add all new tones to the collection, if there is at least one new tone in the mix (that does not exist in the most recent output chord)
                output_chord = None   
                if sanitized != []:
                    for s in sanitized:
                        if last_output_chord == None or not (s.note % 12) in last_output_chord.tones:
                            collection.append(copy.copy(sanitized))
                            break
                
                if chor.tones != [] and chor.may_overwrite != True:
                    collection = []
                    
                if chor.tones != []:
                    output_chord = copy.copy(chor)
                    
                 
                if chor.tones == [] and len(collection)>1:
                    
                    
                    
                    new_chords = []
                    
                    #Make a list of chords using each one distinct tone of the chord at the beginning of the collection
                    for x in range(-1,len(collection[0])):
                        temp = Chord()
                        temp.set_chord(copy.copy(turn_into_list(collection,x)))
                        new_chords.append(copy.copy(temp))
                        
                       
                    #Choose the simplest and highest chord from that list
                    for x in range(0,len(new_chords)):
                        if output_chord == None or (len(new_chords[x].tones)>0 and len(new_chords[x].tones) < len(output_chord.tones)):
                            output_chord = copy.copy(new_chords[x])
                    
                    
                    

                    
                if output_chord != None and len(output_chord.tones) > 0 and output_chord.may_overwrite != True:
                    collection = []
                

                if output_chord != None:
                    last_output_chord = copy.copy(output_chord)
                    output_chord.index = first_index
                    if chor.tones != []:
                        output_chord.index = ci
                    chords.append(copy.copy(output_chord))
                    Chord.final_tones_list.append(copy.copy(chor.tones))

                this_index = []    
                ci = note.index
                
            this_index.append(note)

        chords = [x for x in chords if not (x.tones == [])]
        return copy.copy(chords)
   
    def create_chord_track(chords):
        track = []
        old_chord = None
        for j,c in enumerate(chords):
            if c.base == -1:
                continue
            # if old_chord != None and c.tones == old_chord:
            #     continue
            old_chord = copy.copy(c.tones)
            #base tone 36 bis 47, akkord ab 48
            track.append(Event(type='note',index=c.index, note=c.base+36, channel = 12, duration = FileIO.ticks_per_beat))
            print (c.get_chord_name())
            for i,x in enumerate(c.tones):  #Chord.final_tones_list[j]
                
                track.append(Event(type='note',index=c.index+(0*i*30), note=x+48,channel = 12, duration = FileIO.ticks_per_beat))
        
        return track
    
    def simplify_chords(chords, per_measure, simple_chords):
        #Create list of chord locations, with only x chords per measure
        locations = []
        start = 0
        end = 0
        for i,bc in enumerate(FileIO.beat_changes):
            duration_per_measure = bc['beats'] * FileIO.ticks_per_beat
            start = end
            if i == len(FileIO.beat_changes) -1:
                end = chords[-1].index
            else:
                end = FileIO.beat_changes[i+1]['index']
            
            for x in range (start, end, int((bc['beats']*FileIO.ticks_per_beat)/ per_measure)):
                locations.append(x)
        
        
        fuzzy_width = int(FileIO.ticks_per_beat / 4) #How different the previous and next tone can lie, to be still considered equally far
        
        new_chords = []
        chord_index = 0
       
            
            
        for lo in locations:
            #Find the nearest chords
            
            #Loop until we reached the location or overstepped it
            while chord_index < len(chords) and chords[chord_index].index < lo:
                chord_index += 1
                
            
            if chord_index == len(chords): break
            
            distance_before = -1
            if chord_index > 0:
                distance_before = lo - chords[chord_index-1].index
            distance_after = chords[chord_index].index - lo
            
            new = Chord()
            
            if simple_chords == True:
                if chords[chord_index-1].fourth == 2 or chords[chord_index-1].fourth == 4 or chords[chord_index-1].fourth == 6:
                    chords[chord_index-1].fourth = 0
                        
            if distance_before <= FileIO.ticks_per_beat or distance_after <= FileIO.ticks_per_beat:
                if abs(distance_before - distance_after) < fuzzy_width or distance_after < distance_before or chord_index == 0 or distance_before == -1:
                    #take the next chord
                    if simple_chords == True:
                        if chords[chord_index].fourth == 2 or chords[chord_index].fourth == 4 or chords[chord_index].fourth == 6:
                            chords[chord_index].fourth = 0
                    new.set_chord_by_name(chords[chord_index].base,chords[chord_index].mode,chords[chord_index].fourth)
                    #new = copy.copy(chords[chord_index])
                    
                else:
                    #take the last chord
                    
                    if simple_chords == True:
                        if chords[chord_index-1].fourth == 2 or chords[chord_index-1].fourth == 4 or chords[chord_index-1].fourth == 6:
                            chords[chord_index-1].fourth = 0
                    new.set_chord_by_name(chords[chord_index-1].base,chords[chord_index-1].mode,chords[chord_index-1].fourth)
                    #new = copy.copy(chords[chord_index-1])
                
            new.index = lo
            new_chords.append(copy.copy(new))
            
        
        #for x in range (0,len(chords)):
            
        return new_chords
    
    
    def current_measure ( index ):
        beat_index = index / FileIO.ticks_per_beat
        measure = 0
        last_beats = 4
        for bc in FileIO.beat_changes:
    
            if beat_index > bc['increment']:
                beat_index -= bc['increment']
                measure += bc['increment'] / last_beats
                last_beats = bc['beats']
            else:
                break
            
        return (measure+int(beat_index/last_beats))
    
class Chord:
    tone_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    chords = []
    final_tones_list = []
    #3 Tones:
    chords.append([0,4,7])#major
    chords.append([0,3,7])#minor
    chords.append([0,4,8])#aug
    chords.append([0,3,6])#dim
    chords.append([0,5,7])#sus4
    chords.append([0,2,7])#sus2
        
    #4 Tones:
    #C0,C#,D2,D#,E4,F5,F#,G7,G#,A9,A#,B11   
    #C - 2,4,6,7,7+
    chords.append([0,2,4,7]) #6
    chords.append([0,4,5,7])
    chords.append([0,4,7,9])
    chords.append([0,4,7,10])
    chords.append([0,4,7,11])
    #Cm - 2,4,6,7,7+
    chords.append([0,2,3,7]) #11
    chords.append([0,3,5,7])
    chords.append([0,3,7,9])
    chords.append([0,3,7,10])
    chords.append([0,3,7,11])
    #Caug - 2,4,6,7,7+
    chords.append([0,2,4,8])  #16
    chords.append([0,4,5,8])
    chords.append([0,4,8,9])
    chords.append([0,4,8,10])
    chords.append([0,4,8,11])
    #Cdim - 2,4,6,7,7+
    chords.append([0,2,3,6])  #21
    chords.append([0,3,5,6])
    chords.append([0,3,6,9])
    chords.append([0,3,6,10])
    chords.append([0,3,6,11])
    #Csus4 - 2,6,7,7+
    chords.append([0,2,5,7])  #26
    chords.append([0,5,7,9])
    chords.append([0,5,7,10])
    chords.append([0,5,7,11])
    #Csus2 - 6,7,7+
    chords.append([0,2,7,9])  #30
    chords.append([0,2,7,10])
    chords.append([0,2,7,11])
    def __init__(self):
        
                                #Example Csus4/maj7 starting with F (F,G,B,C)
        self.base = -1           #C (0)
        self.original_tones = []#F,G,B,C 
        self.tones = []         #C,F,G,B (0,5,7,11)
        self.lowest_tone = 0    #F
        self.mode = ''          #'sus4','' = major
        self.fourth = 0         #8       (4,6,2. 7=minor 7th, 8=major 7th)
        self.fourth_add = ''    #maj7    (add a "/" if base tone ended with an additional word or is minor-mode
        self.inversion = 1      #2
        self.index = 0
        self.lil = 0
        self.may_overwrite = False
        

    def set_chord_by_name(self,base,mode,fourth):
        final = []
        if fourth == 0:
            if mode == '': final = copy.copy(Chord.chords[0])
            if mode == 'm': final = copy.copy(Chord.chords[1])
            if mode == 'aug': final = copy.copy(Chord.chords[2])
            if mode == 'dim': final = copy.copy(Chord.chords[3])
            if mode == 'sus4': final = copy.copy(Chord.chords[4])
            if mode == 'sus2': final = copy.copy(Chord.chords[5])
        if fourth == 2:
            self.fourth_add = "9"
            if mode == '': final = copy.copy(Chord.chords[6])
            if mode == 'm': final = copy.copy(Chord.chords[11])
            if mode == 'aug': final = copy.copy(Chord.chords[16])
            if mode == 'dim': final = copy.copy(Chord.chords[21])
            if mode == 'sus4': final = copy.copy(Chord.chords[26])
            if mode == 'sus2': final = copy.copy(Chord.chords[5])
        if fourth == 4:
            self.fourth_add = "4"
            if mode == '': final = copy.copy(Chord.chords[7])
            if mode == 'm': final = copy.copy(Chord.chords[12])
            if mode == 'aug': final = copy.copy(Chord.chords[17])
            if mode == 'dim': final = copy.copy(Chord.chords[22])
            if mode == 'sus4': final = copy.copy(Chord.chords[4])
            if mode == 'sus2': final = copy.copy(Chord.chords[5])
        if fourth == 6:
            self.fourth_add = "6"
            if mode == '': final = copy.copy(Chord.chords[8])
            if mode == 'm': final = copy.copy(Chord.chords[13])
            if mode == 'aug': final = copy.copy(Chord.chords[18])
            if mode == 'dim': final = copy.copy(Chord.chords[23])
            if mode == 'sus4': final = copy.copy(Chord.chords[27])
            if mode == 'sus2': final = copy.copy(Chord.chords[30])                               
        if fourth == 7:
            self.fourth_add = "7"
            if mode == '': final = copy.copy(Chord.chords[9])
            if mode == 'm': final = copy.copy(Chord.chords[14])
            if mode == 'aug': final = copy.copy(Chord.chords[19])
            if mode == 'dim': final = copy.copy(Chord.chords[24])
            if mode == 'sus4': final = copy.copy(Chord.chords[28])
            if mode == 'sus2': final = copy.copy(Chord.chords[31])
        if fourth == 8:
            self.fourth_add = "maj7"
            if mode == '': final = copy.copy(Chord.chords[10])
            if mode == 'm': final = copy.copy(Chord.chords[15])
            if mode == 'aug': final = copy.copy(Chord.chords[20])
            if mode == 'dim': final = copy.copy(Chord.chords[25])
            if mode == 'sus4': final = copy.copy(Chord.chords[29])
            if mode == 'sus2': final = copy.copy(Chord.chords[32])
        
        for i in range(0,len(final)):
            final[i] += base
            final[i] = final[i] % 12
        
        self.tones = copy.copy(final)
        self.original_tones = copy.copy(final)
        self.mode = mode
        self.base = base
        self.lowest_tone = base
        self.fourth = fourth
        self.inversion = 1
        
        
    def set_chord(self,_tones):
        
        def delete_neighbors(tones_,until):
            #until x tones left
            while len(tones_) > until:
                neighbors = []
                for x in range (0,len(tones_)):
                    neighbors.append(0)
                neighbors[0] = (tones_[1]-tones_[0]) + (tones_[0]-tones_[-1]+12)
                neighbors[-1] = (tones_[-1]-tones_[-2]) + (tones_[0]-tones_[-1]+12)
                for x in range (1,len(tones_)-1):
                    neighbors[x] = (tones_[x]-tones_[x-1]) + (tones_[x+1]-tones_[x])
                nmin = 13
                ind = 0
                for indx,n in enumerate(neighbors):
                    if n < nmin: 
                        nmin = n
                        ind = indx
                        
                del tones_[ind]
            return tones_
        if len(_tones) <= 2:
            return
        
        def delete_same_tones(tones):
            new_tones = []
            new_tones.append(tones[0])
            for x in range (1,len(tones)):
                if tones[x] != tones[x-1]:
                    new_tones.append(tones[x])
            return new_tones
            
        def is_strong_third(tones):  #Multiple base tones and 1-x times the third (major or minor) 
            allowed = [0,3,4,8,9]
            is_three = False
            is_four = False
            is_eight = False
            is_nine = False
            
            #Return False if has incorrecrt combinations
            for x in range(0,len(tones)):
                if not tones[x] in allowed: return None
                if tones[x] == 4 and is_three: return None
                if tones[x] == 9 and is_eight: return None
                if (is_three or is_four) and (tones[x] == 8 or tones[x] == 9): return None
                if tones[x] == 8: is_eight = True
                if tones[x] == 3: is_three = True
                if tones[x] == 4: is_four = True
                if tones[x] == 9: is_nine = True
            
            if not (is_three or is_four or is_eight or is_nine): return None
                
            mode = ''
            base = 0
            third = 0
            if is_three or is_nine: mode = 'm'
             
            
            for x in range(0,len(tones)):
                if (is_three or is_four) and tones[x] == 0: base += 1
                if (is_eight or is_nine) and tones[x] == 0: third += 1
                if tones[x] == 3 or tones[x] == 4: third += 1
                if tones[x] == 8 or tones[x] == 9: base += 1
                                
            if base >= third: #Third is assumed, add the fifth
                if is_three or is_four: tones.append(7)
                if is_nine: tones.append(4)
                if is_eight: tones.append(3)
                tones.sort()
                return copy.copy(tones)
            # if third > base: #Fifth is assumed, add the base
            #     if is_eight or is_nine: tones.append(5)
            #     if is_three: tones.append(8)
            #     if is_four: tones.append(9)
            #     tones.sort()
            #     return copy.copy(tones)
                
            return None
        
                
        self.lowest_tone = _tones[0]
        self.original_tones = copy.copy(_tones)
        
        #1. Sort tones, to be comparable with list
        _tones.sort()
        
            
        #2. 0-base the chord
        distance = _tones[0]
        for i,t in enumerate(_tones):
            _tones[i] -= distance
        
        new_tones = is_strong_third(_tones)
        may_overwrite = False
        if new_tones != None:
            _tones = copy.copy(new_tones)
            may_overwrite = True

                    
        _tones = delete_same_tones(_tones)
        delete_neighbors(_tones,4)
        
        distance2 = _tones[0]
        for i,t in enumerate(_tones):
            _tones[i] -= distance2
            
        if len(_tones) <= 2:
            return   
        not_yet = 1
        while not_yet == 1: 
            
            #3. Find the chord
            chord = []
            self.mode = ''
            self.fourth = 0
            self.fourth_add = ''
            self.may_overwrite = may_overwrite
            
            
            inversion = 0
            #Direct result
            ind = 0
            for i in range(0,len(Chord.chords)):

                c = copy.copy(Chord.chords[i])
                inversion = Chord.same_chord(_tones, c)
                if inversion > 0: 
                    chord = copy.copy(_tones)
                    ind = i
                    break
            #print (str(chord)+" "+str(len(_tones)))
            if chord == [] and len(_tones) == 4: 
                delete_neighbors(_tones,3)
            elif len(_tones) == 3 or chord != []:
                not_yet = 0
                # for x in range (0,len(tones)):
                #     tones[x] += distance
                
        if chord == []:
            return
        
        self.inversion = inversion
        self.tones = chord
        
        for x in range(0,len(self.tones)):
            self.tones[x] += distance
        self.base = self.tones[-(inversion-1)]    
        self.lil = self.tones[0]
        
        if ind == 1 or (ind >=11 and ind <= 15):self.mode = 'm'
        elif ind == 2 or (ind >=16 and ind <= 20):self.mode = 'aug'
        elif ind == 3 or (ind >=21 and ind <= 25):self.mode = 'dim'
        elif ind == 4 or (ind >=26 and ind <= 29):self.mode = 'sus4'
        elif ind == 5 or (ind >=30 and ind <= 32):self.mode = 'sus2'
        
        if ind == 6 or ind == 11 or ind == 16 or ind == 21 or ind == 26: self.fourth = 2
        elif ind == 7 or ind == 12 or ind == 17 or ind == 22: self.fourth = 4
        elif ind == 8 or ind == 13 or ind == 18 or ind == 23 or ind ==27 or ind == 30: self.fourth = 6
        elif ind == 9 or ind == 14 or ind == 19 or ind == 24 or ind ==28 or ind == 31: self.fourth = 7
        elif ind == 10 or ind == 15 or ind == 20 or ind == 25 or ind ==29 or ind == 32: self.fourth = 8
                
        if self.fourth == 2: self.fourth_add = '9'
        if self.fourth == 4: self.fourth_add = '11'
        if self.fourth == 6: self.fourth_add = '6'
        if self.fourth == 7: self.fourth_add = '7'
        if self.fourth == 8: self.fourth_add = 'maj7'
                
        
            
     
    def same_chord(list1, list2a):
        #list2 will be changed
        list2 = copy.copy(list2a)
        if len(list1) != len(list2):
            return 0
        if list1 == list2:
            return 1
        for x in range(0,len(list2)):
            diff = list2[1]
            for y in range (0,len(list2)):
                list2[y] -= diff
            del list2[0]
            list2.append(12-diff)
            if list1 == list2:
                return x+2
        return 0
        
        
    def get_chord_name(self):
        if self.base == -1:
            return ''
        name = Chord.tone_names[self.base]+self.mode
        if self.mode != '' and self.fourth_add != '':name += "/"
        name += self.fourth_add
        return name
    
    
        
        
        
        
        
        
    
                
            