from midi_IO import FileIO,Event
from midi_tools import Tools
from mido import Message
import copy, math
from random import shuffle, randint
from munkres import Munkres
from midi_arrange import *
from midi_combine import *
from midi_brain_guitar import Create_Guitar

# midi_split: (Used for all ensemble instruments)
#    IN: STTs, all tracks, instruments (to get special tone lists, i.e. Timpani), instrument ranges - OUT: output tracks
#    0.) Find groups - using substitute and grouping rules -> Same instruments are automatically grouped
#    
#    1.) Give to each output track each fitting tone (apply tone lists)
#    2.) Take for each instrument all tones that are > STT (randomly!) and copy them to another voices that has not enough tones. Separate per group. 
#    (Avoid duplicates.)
#    3.) Go through each output track -> least important to most important, take the >STT tones  and remove them if someone else in the
#    same group already plays this tone
#    4.) Redistribute all now leftover tones so that each distance to its previous tone is minimal
#    5.) Analyse the rhythm structure and find cut points
#    6.) Randomize, which instruments to play, at each cut-point
#        -> 3 Steps -> 1. Type of combination, 2. Amount of groups playing, 3. which groups
#        a.) Try to apply any rules first (e.g. this type of segment should be played by strings)
#        b.) Don't mix groups (e.g. flute with strings without violin)
#        c.) Over time use more and more groups - end will be the loudest
#        d.) Ok to use single instruments representing different groups -> Always followed by all represented groups playing together in next segment
#        e.) Whole group always stays together otherwise (can't simply leave out one of the instruments -> Groups should represent a wide range of tones)
#        f.) Let the random choice be influenced somewhat by the amount of differing STTs
#        g.) Consider the average relative instrument playing time in an orchestra (french horn less than violin)
#    7.) Put the melody on top of the current arrangement. Find the ranges combination of instruments (higest first), where the melody has to change instrument
#    the fewest:
#        1.) Go through melody and keep track of which instrument can keep up longest, once the longest can't anymore, find again all instruments that play the current tone etc.
#        2.) For each segment (see above), check if the currently playing instruments can take over the melody (with the same amount of instrument changes or fewer)
#            -> yes, then let them play it - no, then let the originally found instrument continue with the melody


def split_music(notes,melody,chords,instruments_list,dont_add_melody=False):
    
    if len(instruments_list) == 0: return []
    groups = [] #e.g. [[0,1,2,3],[4],[5,6]]
    
    tracks = []
    patches = []
    averages = []
    ranges = []
    max_amounts = []
    arpeggios = []
    for instrument in instruments_list:
        #Prepare patches
        patches.append(instrument[0])
        #Prepare output tracks
        tracks.append([])
        #Get range averages
        averages.append(int(round((instrument[4][0]+instrument[4][1])/2)))
        #Prepare ranges
        ranges.append(instrument[4])
        #Prepare max amounts (stt)
        max_amounts.append(instrument[2])
        #Arpeggios
        arpeggios.append(instrument[3])
    
    channels = Tools.get_channels(patches)
    
    #Create instrument change messages and add them to the output tracks
    for x in range(0,len(channels)):
        _new_msg = Message('program_change')
        _new_msg.channel = channels[x]
        _new_msg.program = patches[x]-1
        _event = Event(type='event',msg=_new_msg,index=0)
        tracks[x].append(_event)
    
    #0.) Find Groups
    groups = get_groups(patches) #List of sets
    
    #0b.) Combine notes
    notes = copy.copy(Tools.combine_tracks(notes)[0])
    

    
    #1.) Distribute all fitting tones, duplicates allowed - only depending on range and tone lists    
    for note in notes:
        if note.type == 'event': continue
        found = False #Found any fitting instrument
        for inil,instrument in enumerate(instruments_list):
            if note.note >= instrument[4][0] and note.note <= instrument[4][1]: #in range
                found = True
                _note = copy.copy(note)
                _note.channel = channels[inil]
                tracks[inil].append(_note)
        if not found:
            #Give it to all voices, in their respective range
            
            for inil,instrument in enumerate(instruments_list):
                while abs(note.note - averages[inil]) > 6:
                    dir = -(note.note - averages[inil]) / abs(note.note - averages[inil])
                    note.note += int(dir*12) 
                _note = copy.copy(note)
                _note.channel = channels[inil]
                tracks[inil].append(_note)

    
    #2.) For each voice with too few tones (per time index), copy tones from the nearest neighbor that has too many tones
    # Choose tones that the voice does not have yet
    # Repeat this once per group.
    
    #2.1) Get amount of segments (each 1/16th note long)
    final_index = notes[-1].index
    segments = int(math.ceil(final_index / (FileIO.ticks_per_beat/4) )) #beat/4 = 1/16th
    segment_size = FileIO.ticks_per_beat/4

    

    #2.2) Collect all notes per segment across all tracks
    all_segments = get_segment_data(tracks,segments,segment_size)
    
    
                
    #2.3.1) Redistribute Notes
    for segment in all_segments:
        for inse,note_list in enumerate(segment):
            if len(note_list) < instruments_list[inse][2]: #allowed stt
    
                #has not enough tones, now find a donor
                unique_tones = get_unique_tones(note_list)
                for inse2,note_list2 in enumerate(segment):
                    if inse2 == inse: continue
                    if len(note_list2) > instruments_list[inse][2]:
                        #Try to get an unique new tone first
                        new_list = copy.copy(note_list2) #Randomize which tones to choose
                        shuffle(new_list)
                        
                        for note in new_list:
                            val = note.note % 12
                            if not val in unique_tones:
                                unique_tones.add(val)
                                new_note = copy_into(tracks,channels,averages,ranges,inse,note)
                                
                            if len(note_list) >= instruments_list[inse][2]: break
                        if len(note_list) >= instruments_list[inse][2]: break
                if len(note_list) >= instruments_list[inse][2]: continue
                
                #Could not find enough tones
                #print (str(instruments_list[inse][2] - len(note_list))+" notes missing.")
    
    
    
    
    #Update segment data
    all_segments = get_segment_data(tracks, segments, segment_size)
    
    #3.) Remix output instruments
    tracks = arrange(all_segments,tracks,melody,instruments_list,groups, averages,ranges,channels,dont_add_melody)
    
     #Update segment data
    all_segments = get_segment_data(tracks, segments, segment_size)
    
    
    #3.2) Remove tones in groups (First stage removing related to group tones - midi_combine will clean up the result of this.) 
    #Save all the tones that got removed, so that midi_combine can add back arpeggio if needed
    tones_for_arpeggio = [] #dimensions: 1.segment, 2.instrument, 3.tones between 0-11 (midi_combine will decide on the order)
    
    save_until = [0 for z in instruments_list] #Keeping melody tone save until this index
    
            
    for inas,segment in enumerate(all_segments):
        already_added_instruments = False
        for group in groups:
    
            _tones_for_arpeggio = []
            
            for inse,instr in enumerate(segment):
                _arpeggio_instrument = set()
                
                if not patches[inse] in group: 
                    _tones_for_arpeggio.append(_arpeggio_instrument)
                    continue
                
                played_in_group = get_played_in_group(segment,group,patches) #list of all currently played notes in this group
           
                amount_list = [] #how often each tone appears in the group
                for note in instr:
                    amount_list.append(played_in_group.count(note.note % 12))
                while len(instr) > max_amounts[inse]:
                    found_non_melody_tone = False
                    while found_non_melody_tone == False:
                        index_of_highest = max(range(len(amount_list)), key=amount_list.__getitem__)
                        if instr[index_of_highest] in melody and amount_list[index_of_highest] != -1:
                            amount_list[index_of_highest] = -1 #keep melody tones safe as long as possible
                            #Remember that a melody tone is currently playing -> all other tones that start now should be removed
                            if instr[index_of_highest] in melody:
                                save_until[inse] = instr[index_of_highest].index + instr[index_of_highest].duration
                        else:
                            found_non_melody_tone = True
                    
                    #Delete the note from all lists and from the output track
                    _arpeggio_instrument.add(instr[index_of_highest].note % 12)
                    tracks[inse].remove(instr[index_of_highest])                    
                    del instr[index_of_highest]
                    del amount_list[index_of_highest]
                    #for z in range(0,len(instr)):
                    z = 0
                    while z < len(instr):
                        if instr[z].index < save_until[inse] and not (instr[z] in melody):
                            del instr[z]
                            del amount_list[z]
                        z += 1
                _tones_for_arpeggio.append(_arpeggio_instrument)
            if already_added_instruments == False:
                tones_for_arpeggio.append(_tones_for_arpeggio) 
            else:
                tones_for_arpeggio[-1] = integrate_into(_tones_for_arpeggio,tones_for_arpeggio[-1],set())
            already_added_instruments = True               
    
    print(tones_for_arpeggio)
    _tracks = []
    for intr,track in enumerate(tracks):
        if instruments_list[intr][6] == []:
            _tracks.append(combine_music(track,patches[intr],channels[intr],arpeggios[intr],max_amounts[intr],ranges[intr],tones_for_arpeggio,intr)) 
        else:
            _tracks.append(Create_Guitar.combine_guitar_music(track,patches[intr],channels[intr],instruments_list[intr][6]))
            
    
    
    if chords != [] and 2 == 3: #To be used for the entire song (if only melody), or as a little alternative
        chord_tracks = create_chord_tracks(chords,tracks,averages,max_amounts,ranges,groups,instruments_list,len(all_segments),segment_size)
        print (chord_tracks)   
        #delete
        for inil,instrument in enumerate(instruments_list):
            tracks[inil] = tracks[inil][:1]
        
        current_index = 0
        for inct,chord in enumerate(chord_tracks):
            measure_width = get_measure_width_in_segments(current_index, segment_size)
            chord_distance = measure_width / 2 #in segments
                
            if chord == []:
                current_index += int(chord_distance)
                continue
            
            for inch, instrument in enumerate(chord):
                for inin,tone in enumerate(instrument):
                    
                    #Check if the tone appears also in the next chords (then play this one longer, delete the next ones)
                    cnt = inct+1
                    duration = chord_distance * segment_size 
                    found = True
                    _index = current_index
                    while cnt < len(chord_tracks) and found:
                        found = False
                        if len(chord_tracks[cnt]) == 0: break #no-chord section
                        
                      
                        if tone in chord_tracks[cnt][inch]: 
                            found = True
                            chord_tracks[cnt][inch].remove(tone)
                            cnt+=1
                            _measure_width = get_measure_width_in_segments(_index, segment_size)
                            _chord_distance = measure_width / 2 #in segments
                            _index += int(_chord_distance)
                            duration += _chord_distance * segment_size
                    cnt -= 1 #cnt = inct, wenn nix
                    
                    
                    tracks[inch].append(Event(type='note',msg=Message('note_on'),index=current_index*segment_size,duration=duration, note=tone, octave = int(tone / 12),channel = channels[inch], velocity = 100))
                
                
            current_index += int(chord_distance)        
                        
                
    return tracks 

def integrate_into(what,into_where,empty):
    output = into_where
    for x in range(0,min(len(what),len(into_where))):
        if output[x] == empty:
            output[x] = what[x]
    return output
    

def create_chord_tracks(chords,tracks,averages,max_amounts,ranges,groups,instruments_list,segment_count,segment_size):
    #Create chord tracks in different styles
    #The chord tracks recognize the different groups and handle them individually
    #A chord track tries to have all instruments in one group play together the chords:
    #    the lowest (or a single) instrument gets the base line, the rest get the other chord tones
    #Style 0 = Play tones as long as possible, but at most 1 measure 
    #        - Instruments try to move as few as possible beetween tones (hungarian algorithm)
    #Style 1 = Play something every half measure. If it's the same chord, let the base move an octave if possible
    #         -Let all the other tones also move to a different position
    #         -Let highest note always go up, down, up, up
    
    def key_by_average(item):
        return averages[item]
    
    #Functions:
    ###############################################################################################################
    ##############################################################################
    #Distribute chord tones to all instruments best-fitting to last distribution:#
    ##############################################################################
    def create_chord_from_old(chord,last_list):
        new_tones = []
        for x in range(0,len(instruments_list)): new_tones.append([])
        for group in groups:
            in_group = []
            
            for inil, instrument in enumerate(instruments_list):         
                if instrument[0] in group: in_group.append(inil)
            in_group = sorted(in_group,key=key_by_average) #Sort instruments in current group by average tone height 
            
            this_group_last_time = []
            for instrument in in_group:
                this_group_last_time.append(last_list[instrument])
            
            tones_used = [] #To always find the most underrepresented chord tone
            for tone in chord:
                tones_used.append(0)
            
            possible_positions = -1 #minus the one bass note
            for instrument in in_group:
                possible_positions += max_amounts[instrument]
            
            
            #create N chord tones
            chord_tones = math.floor(possible_positions/len(chord[0])) * chord[0]
            chord_tones.extend(chord[0][0:(possible_positions-len(chord_tones))])
            
            #Find the best match between the old tones and these new chord tones
            this_group_new_tones = find_match(chord_tones,this_group_last_time,in_group,lowest_range=ranges[in_group[0]])
            
            for inig, instrument in enumerate(in_group):
                new_tones[instrument] = this_group_new_tones[inig]
        return new_tones
        
    
    def find_match(chord_tones,_last_list,in_group,lowest_range):
        bass_tone = -12
        range_list = []
        skipped = False
        for x in range(0,len(_last_list)):
            for tone in _last_list[x]:
                if x==0 and skipped == False: 
                    skipped = True #Skip the bass tone
                    continue
                range_list.append(ranges[in_group[x]])
        print (range_list)
        last_list = copy.copy(_last_list)
        if len(last_list[0]) >= 1: 
            bass_tone = last_list[0][0]
            del last_list[0][0]
        
        last_list = [item for sublist in last_list for item in sublist]
        
        chord_tones = chord_tones[0:len(last_list)]
        m= Munkres()
        matrix = []
        matrix_val = []
        for inll,old_tone in enumerate(last_list):
            row = []
            row_val = []
            for new_tone in chord_tones:
                val = (new_tone+12 - ((old_tone-6) % 12))%12 + (old_tone-6)  #nearest variant of the chord tone
                while val < range_list[inll][0]:
                    val += 12
                while val > range_list[inll][1]:
                    val -= 12
                
                    
                diff = abs(val-old_tone)%12
                row_val.append(val)
                row.append(diff)
            matrix.append(row)
            matrix_val.append(row_val)
        new_tones = []
        print (matrix)
        indices = m.compute(matrix)
    
        for inin,index in enumerate(indices):
            new_tones.append(matrix_val[inin][index[1]])
    
        new_bass_tone = chord_tones[0]
        minimum = math.inf
        new_list = []
        index_new_tones = 0
        for instrument in _last_list:
            new_sub_list = []
            for tone in instrument:
                new_sub_list.append(new_tones[index_new_tones])
                if new_tones[index_new_tones] < minimum: minimum = new_tones[index_new_tones]
                index_new_tones += 1
            new_list.append(new_sub_list)
        new_bass_tone = (new_bass_tone+12-lowest_range[0]%12)%12+lowest_range[0]#(new_bass_tone+12 - ((minimum-12) % 12))%12 + (minimum-12)
        new_list[0].insert(0,new_bass_tone)
        
        
        return new_list                
    
    #####################################################
    #Distribute chord tones randomly to all instruments:#
    #####################################################
    def create_new_chord(chord):
        new_tones = []
        for x in range(0,len(instruments_list)): new_tones.append([])
        for group in groups:
            in_group = []
            
            for inil, instrument in enumerate(instruments_list):         
                if instrument[0] in group: in_group.append(inil)
            in_group = sorted(in_group,key=key_by_average) #Sort instruments in current group by average tone height
            
            #go through all instruments in this group, start at the lowest
            tones_used = [] #To always find the most underrepresented chord tone
            for tone in chord:
                tones_used.append(0)
            for inig, instrument in enumerate(in_group):
                if inig == 0: #Bass line instrument
                    bass_note = chord[1]
                    #Create first bass tone
                    val = (bass_note+12-ranges[instrument][0]%12)%12+ranges[instrument][0]#(bass_note+12 - ((averages[instrument]-6) % 12)) + (averages[instrument]-6) 
                    tones_used[0] += 1
                    
                    
                    new_tones[instrument].append(val)
                    
                    distance_to_next = 6
                    last_val = val+distance_to_next #Leave some room to the next tone!
                    
                #Create multiple tones on top of each other
                for y in range(0,max_amounts[instrument]):
                    if inig==0: continue #bass line instrument already got it's first tone above
                    
                    #find random underrepresented tone
                    my_tone = find_underrepresented_tone(tones_used)
                    tones_used[my_tone] += 1
                    
                    val = (12+chord[0][my_tone]-last_val%12)%12 + last_val
                    
                    lowest_possible = (12+val%12-ranges[instrument][0]%12)%12+ranges[instrument][0]
                    val = max(val,lowest_possible) #Raise to lowest possible tone
                    
                    while val > ranges[instrument][1]:
                        val -= 12
                    new_tones[instrument].append(val)
                    
                        
                    
                    
                    last_val = val
        return new_tones 
    
        #################################################################################################
    
    
    style_0_tones = [] #[[[instrument 1 tones],[instr2]...[instr x]],[[2 measure, instrument 1].....
    x = 0
    non_zero_index = -1
    while x < segment_count and x < len(chords):
        measure_width = get_measure_width_in_segments(x, segment_size)
        print (measure_width)
        chord_distance = measure_width / 2 #in segments
        
        chord = chords[x]
       
        if chord[2] == 'x':
            style_0_tones.append([])
        else:
            if x == 0 or non_zero_index == -1: 
                style_0_tones.append(create_new_chord(chord))
                non_zero_index = len(style_0_tones)-1
            else:
                last_list = []
                for val in style_0_tones[non_zero_index]:
                    last_list.append(copy.copy(val))
                style_0_tones.append(create_chord_from_old(chord,last_list))
                non_zero_index = len(style_0_tones)-1
               
                            
            
        x += int(chord_distance)
    
       
    return style_0_tones
        
def find_underrepresented_tone(tones_used):
    my_tone = 0
    low = min(tones_used)
    choice = tones_used.count(low)
    selection = randint(1,choice)
    for intu,tone in enumerate(tones_used):
        if tone == low: selection -= 1
        if selection == 0:
            my_tone = intu
            break
    return my_tone
    
def get_measure_width_in_segments(segment, segment_size):
    index_of_segment = segment * segment_size
    
    beats = 4
    for bc in FileIO.beat_changes:
        if bc['index'] <= index_of_segment:
            beats = bc['beats']
        else: break
    return beats*4    

def get_played_in_group(segment,group,patches):
    ret_val = []
    
    for inse,instrument in enumerate(segment):
        if patches[inse] in group:
            ret_val.extend(get_unique_tones(instrument))
    return ret_val
    

def get_segment_data(tracks,segments,segment_size, only_values=False,check_stt=False):
    track_indices = []
    for tr in tracks:
        track_indices.append(0)
    
    all_segments = []
    repeat_box = [] #Notes that are longer than one segment
    
    for segment in range(1,segments):
        start_pos = (segment-1) * segment_size
        end_pos = segment * segment_size

        notes_in_segment = []
        for intr,tr in enumerate(tracks):
            notes_in_segment.append([])
            
            
            for repeat in repeat_box:
                if repeat[1] != intr: continue
                if only_values:
                    notes_in_segment[-1].append(repeat[0].note % 12)
                else:
                    notes_in_segment[-1].append(repeat[0])
                
                
            repeat_box = [repeat for repeat in repeat_box if not(repeat[1] == intr and repeat[0].index + repeat[0].duration <= end_pos)]
            
            
            
            while track_indices[intr] < len(tr) and tr[track_indices[intr]].index < end_pos:
                if tr[track_indices[intr]].type != 'event': 
                    if only_values:
                        notes_in_segment[-1].append(tr[track_indices[intr]].note % 12)
                    else:
                        notes_in_segment[-1].append(tr[track_indices[intr]])
                    
                    if check_stt:
                        
                        if tr[track_indices[intr]].duration > segment_size:
                            repeat_box.append([tr[track_indices[intr]],intr])#what note and which track
                track_indices[intr] += 1
            
        all_segments.append(notes_in_segment)  
        
    return all_segments

def get_unique_tones(note_list,full=False):
    #Returns a unique set of tones (mod 12) that appear in this note_list
    unique = set()
    for note in note_list:
        if full:
            unique.add(note.note)
        else:   
            unique.add(note.note % 12)
    
    return unique


 #index = next(
    #    ((idx) for idx, obj in enumerate(tracks[where]) if obj.index >= event_index and obj.type != 'event'),len(tracks[where])-1)
   
    #index = index[0]
    

def get_groups(patches):
    groups = []
    for p in patches:
        fits_to = [] #List of patches this patch can be combined with
        fits_to.append(p) #with itself
        identities = [] #patches it can substitute
        identities.append(p)
        for rg in FileIO.GM_replace_groups:
            if p == rg[0]: 
                identities.extend(rg[1:])
                break
        
        for gr in FileIO.GM_groups:
            for id in identities:
                if id in gr:
                    fits_to.extend(gr)
                    continue
        groups.append(set(fits_to))
    
    #Create unique groups
    groups2 = []
    for x in range(0,len(groups)):
        is_extension = False
        for g2 in groups2:
            if not set(g2).isdisjoint(groups[x]): #they share common values
                g2.update(groups[x])
                is_extension = True
        if not is_extension:
            groups2.append(groups[x])
                
    
    return groups2

def copy_into(tracks,channels,averages,ranges,where,_event):
    #When copying a note, the index has to be in order in the new track
    event = copy.copy(_event)
    event_index = event.index

    
    index = -1 #index of last acceptable note
    for intr,note in enumerate(tracks[where]):
        if note.index > event_index: break
        if note.type != 'event':
            index = intr
    
    if index == -1:
        #Move note into middle of instrument range
        previous_note = averages[where]
        index = len(tracks[where])-1
    else:
        previous_note = tracks[where][index].note
      
    
    
    #Move note in range - near previous note
    if previous_note != event.note:
        dir =  int((previous_note - event.note) / abs(previous_note - event.note))
        while abs(previous_note - event.note) >= 12:
            event.note += dir*12
        #Now get back in range (if outside)
        while event.note < ranges[where][0]:
            event.note += 12
        while event.note > ranges[where][1]:
            event.note -= 12
        
        
        
    event.channel = channels[where]
    tracks[where].insert(index+1,event)
    
    return event.note

       
        