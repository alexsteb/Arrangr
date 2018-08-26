import math
from midi_IO import FileIO, Event

# midi_combine: (Used for non-ensemble instruments and ensemble instruments after splitting)
#    IN: arpeggiated?, STT, tracks, instrument - OUT: 1 combined track 
#    1.) Do tracks contain melody? Keep melody always safe and on top (except for really impossible parts)
#    2.) Change octave of too difficult tones (except melody)   
#    3.) Remove tones according to STT rule -> Arpeggiate all the leftover tones if so wished
#        -> Use special rules for removing for different instruments, e.g. finger-rules for piano, tone rules for harp etc.

def combine_music(track,instrument,channel,arpeggio,stt,my_range, tones_for_arpeggio,which): #stt = "same time tones"
   
  
    
    
    #1.) Shorten tones so that stt-rule is applied 
    shorten_track(track, stt)
    
    #Lift or lower tones that are out of range for this instrument
    for note in track:
        while note.note > my_range[1]: note.note -= 12
        while note.note < my_range[0]: note.note += 12
    
    #Close too big jumps (>= 15 distance of a tone to each the tone before and after)
    previous = -1
    my_next = 0
    for intr,note in enumerate(track):
        if note.type == 'event': continue
        if previous == -1:
            previous = 0
            continue
        
        my_next = note.note
        x=1
        while intr+x < len(track):               
            
            if track[intr+x].type != 'event': 
                my_next = track[intr+x].note
                break
            else:
                
                x += 1
        
        previous = track[intr-1].note
        
        if abs(note.note - previous) >= 15 and abs(note.note - my_next) >= 15:
            if (note.note - previous) * (note.note - my_next) < 0: break #break if one is lower and one is higher
            nearer = previous
            if abs(note.note - previous) > abs(note.note - my_next): nearer = my_next
            dir = -abs(note.note - nearer)/(note.note - nearer)
            while abs(note.note - nearer) >= 15: 
                note.note += int(dir*12)
            
    
    #Simplify notes according to level

    
    level = FileIO.preferred_speeds[instrument-1][1]
    level_in_ticks = level*FileIO.ticks_per_beat/8
    level = 1
    remove_list = []
    last_note = None
    for intr,note in enumerate(track):
        if note.type == 'event': continue
        if last_note == None: 
            last_note = note
            continue
        
        removed_it = False
        if note.index - last_note.index < level*(FileIO.ticks_per_beat/8):
            if note.duration > 2*(note.index - last_note.index):
                remove_list.append(last_note)
            else:
                last_note.duration += note.duration
                remove_list.append(note)
                removed_it = True
        
        if not removed_it: #if the current note was removed, the last note (for distance comparison) does not update
            last_note = note
    
    for element in remove_list:
        track.remove(element)
    
  
    #Create Arpeggios
    #Width of arpeggio should depend on instrument (and difficulty)
    #Arpeggio tones are added before the first tone in the segment, below the lowest tone in the segment, only if still in range
    #no arpeggio tone if at the beginning of the song
    #each tone once, in the shortest possible distance
    #if there is a tone in the path of the a.tones, shorten that tone to max(minimum_duration, level_in_ticks)
    #if that's still not enough, ignore the remaining a.tones
    
    arpeggio_width = int(0.8 * FileIO.preferred_speeds[instrument-1][1] * (FileIO.ticks_per_beat/8)) #maximum speed of instrument
    segment_size = FileIO.ticks_per_beat/4
    print (arpeggio_width)
    this_segment = []
    current_segment = 0
    
    playing_until_x = [] #Remember the tones that need to be shortened for the arpeggio (or potentially prevent the arpeggio)
    playing_until_x_original = []
    who_plays = []
    for note in track:
        if not arpeggio: break
        
        #while note.index >= (current_segment+1)*segment_size and this_segment == []:
        #    current_segment += 1
        #
        #if note.index < (current_segment+1)*segment_size:
        #    this_segment.append(note)
        #    continue
        
        if note.index >= (current_segment+1)*segment_size:
            #Collected 1 segment
            
            #Get lowest note and arpeggio tones
            my_notes = [note.note for note in this_segment if note.type != 'event' and note.index >= current_segment*segment_size]
            my_note_objects = [note for note in this_segment if note.type != 'event' and note.index >= current_segment*segment_size ]
            if len(my_notes)>0: 
                min_note = min(my_notes)
                arpeggio_tones = tones_for_arpeggio[current_segment][which]
            
                if arpeggio_tones != set():
                    #Create ordered list of arpeggio tones below min_note, stopping at range of instrument
                    arpeggio_list = create_arpeggio_list(arpeggio_tones,min_note,my_range)
                    #if min_note == 70:
                    #    print ("d")
                    first_tone = my_note_objects[0]
                    #Check if there is space to the left (beginning of file)
                    max_width = len(arpeggio_list) * arpeggio_width
                    if first_tone.index < max_width:
                        arpeggio_list = arpeggio_list[-int(math.floor(first_tone.index / arpeggio_width)):]
                    
                    #Stop the arpeggio tones, if they reach another previous tone (within arpeggio width)
                    del_list = []
                    for inwp in range(0,len(who_plays)):
                        if who_plays[inwp].type == 'event': del_list.append(inwp)
                        if who_plays[inwp] in my_note_objects or who_plays[inwp].type == 'event': continue #Leave the current notes until the next segment
                        del_list.append(inwp)
                        if playing_until_x_original[inwp] > first_tone.index - max_width: #in the way
                            max_possible = first_tone.index - playing_until_x[inwp]
                            if math.floor(max_possible / arpeggio_width) == 0:
                                arpeggio_list = []
                            else:
                                arpeggio_list = arpeggio_list[-int(math.floor(max_possible / arpeggio_width)):]
                            
                            if (first_tone.index - max_possible) < playing_until_x_original[inwp]:
                                who_plays[inwp].duration = (first_tone.index - len(arpeggio_list)*arpeggio_width) - who_plays[inwp].index
                    
                    #Delete from lists all that are not in the current segment
                    del_list = [x for x in del_list if playing_until_x_original[x] < first_tone.index] #Don't delete yet, if still sounding
                    who_plays = [x for inwp,x in enumerate(who_plays) if not (inwp in del_list)]
                    playing_until_x = [x for inwp,x in enumerate(playing_until_x) if not inwp in del_list]
                    playing_until_x_original = [x for inwp,x in enumerate(playing_until_x_original) if not inwp in del_list]
                    
                    #print (arpeggio_list)
                    
                    if len(arpeggio_list) > 0:
                        #Place the arpeggio tones
                        volume = int(first_tone.velocity * 0.9)
                        cnt = 0
                        for x in range (len(arpeggio_list)-1,-1,-1):
                            cnt += 1
                            new_note = Event(note=arpeggio_list[x], octave=arpeggio_list[x]%12, channel=channel, 
                                             index=int(first_tone.index-cnt*arpeggio_width), type='note', duration=int(arpeggio_width), velocity=int(volume))                            
                            volume *= 0.9
                            
                            copy_into(track,new_note,segment_size,stt) #Do not copy if there is already a note in the same segment
                        
            
            while note.index >= (current_segment+1)*segment_size:
                current_segment +=1
            this_segment = []  
        who_plays.append(note)
        playing_until_x.append(note.index + min(arpeggio_width,note.duration)) #minimum duration
        playing_until_x_original.append(note.index + note.duration) #maximum duration
        this_segment.append(note)
        #current_segment += 1
    
    #Quickly clean again the stt's
    shorten_track(track, stt)
    
    return track

def create_arpeggio_list(arpeggio_tones,min_note,my_range):
    tones = list(arpeggio_tones)
    tones.sort()

    highest = min_note % 12
    lowest_tone = min(tones)
    #Move them around, so they are below min_note
    if lowest_tone < highest:
        while tones[-1] > highest:
            tones = [tones[-1]] + tones[:-1]
            
    output = []
    current_pos = min_note
    for x in range(len(tones)-1,-1,-1):
        if tones[x] < current_pos%12:
            output.insert(0,current_pos-(current_pos%12-tones[x]))
            current_pos = output[0]
            continue
        
        if tones[x] >= current_pos%12:
            output.insert(0,(current_pos-current_pos%12)-(12-tones[x]))
            current_pos = output[0]
            continue
    output = [x for x in output if x >= my_range[0] and x <= my_range[1]]
    #print ("Unter "+str(min_note)+":")
    #print (output)
    return output
  
def copy_into(track,event,segment_size,stt):
    #When copying a note, the index has to be in order in the new track

    event_index = event.index
    if event_index < 0: return
    
    index = -1 #index of last acceptable note
    for intr,note in enumerate(track):
        
        if note.index > event_index: break
        if note.type != 'event':
            index = intr
    
    if index == -1:
        index = len(track)-1
        
    #Check if there are already notes in this segment
    this_segment = []
    begin_of = math.floor(event_index / segment_size)*segment_size
    end_of = begin_of + segment_size
    
    for note in track:
        if note.index >= begin_of:
            if note.index >= end_of:
                break       
            this_segment.append(note)
    
    if len(this_segment) >= stt: return
            
    track.insert(index+1,event)

def shorten_track(track,stt):
    stts = []
    for note in track:
        
        if note.type == 'event': continue
        ci = note.index
        
        #remove from stts if ended before current index
        for tone in stts:
            if tone.index + tone.duration < ci:
                del tone
        _stts = [tone for tone in stts if tone.index + tone.duration >= ci]
        stts = _stts
        stts.append(note)
        
        minimum_duration = int(FileIO.ticks_per_beat / 10)
        
        while len(stts) > stt: #Too many tones currently playing
            #shorten the oldest
            
            index_of_oldest = 0 
            oldest = math.inf
            for inst,tone in enumerate(stts):
                if tone.index < oldest: 
                    oldest = tone.index
                    index_of_oldest = inst
            stts[index_of_oldest].duration = ci - stts[index_of_oldest].index
            del stts[index_of_oldest]
        
        track = [note for note in track if note.duration > minimum_duration or note.type == 'event']
        
        
    