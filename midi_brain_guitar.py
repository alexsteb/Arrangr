from mido import MidiFile
from mido import Message
from mido import MidiTrack
from midi_IO import FileIO
from midi_tools import *
import sys
import copy
import math



class Create_Guitar:
    tabs = [] #internal format
    
    
    #combining_groups = [[0,1,2,3,4,5,6],[7,8,9,10,11,12],[14,15,16,17,18,19,20,21],[23,24,25,26,27]]
    #combining_groups = [[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]]#,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]]
    
#Setting #Patch,Number of Strings, base-tones(e.g.EADGBE), highest fret, hand-width, same_time_tones
    #guitar_settings = [[24,6,[40,45,50,55,59,64],8]]
    #guitar_settings = [[24,4,[55,60,64,57],12]]
    #guitar_settings = [[24,6,[64,59,55,50,45,40],12,3,2]]
    #guitar_settings = [[24,5,[62,59,55,50,67],12,3,2]]
    
      #notes=_track_list,instrument=ensemble_instrument_list[inst][0],guitar_settings=  
    def combine_guitar_music(notes,instrument,channel,guitar_settings):
        
#Setting #Combining Groups (1 List = 1 Guitar)
        
        #guitars = len(Create_Guitar.combining_groups)
        guitar_settings = [guitar_settings]
        notes = Tools.combine_tracks([notes])
        

        

        
        output = []
        #Loop only once -> Keep structure in case i want it to loop more often later..
        for intr, track in enumerate(notes):
            hand_width = guitar_settings[intr][4]
            possible_tones = guitar_settings[intr][5]
            tabs_track = []
            output_track = []
            lowest_string_tone = min(guitar_settings[intr][2])
            highest_string_tone = max(guitar_settings[intr][2])+guitar_settings[intr][3]
            tone_range = highest_string_tone - lowest_string_tone
            tone_range_hand = max(guitar_settings[intr][2])+hand_width - lowest_string_tone
            #tone_range_hand can't be < 12!
            
            
            #Finding the most comfortable fit, between lowest and highest tone
            begin_at = lowest_string_tone % 12
            end_at = 120 + (highest_string_tone % 12) - tone_range #120 = C10
            
            in_range = {}
            for x in range(begin_at,end_at+1,12):
                in_range[x] = 0
            end_it = False
            for note in track:
                for x in range (begin_at,end_at+1,12):
                    if note.note >= x and note.note <= x+tone_range:
                        in_range[x] += 1
            
            #print (in_range)
            max_no = 0
            best_fit = 0
            for val in in_range:
                if in_range[val] >= max_no: #Choose the highest fit, so it gets transposed down and is easier to play
                    max_no = in_range[val]
                    best_fit = val
            adjustment =  lowest_string_tone - best_fit
            
            for note in track:
                if note.type != 'event':
                    note.note += adjustment
            
            
            #Clean up the indices to be set near the closest 16th
            resolution = FileIO.ticks_per_beat*(1/4)
            for inx,note in enumerate(track):
                befor = note.index
                note.index = int(int(round(note.index/resolution)) * resolution)
                #print (str(befor)+" -> "+str(note.index))
                
            

            
            def get_key(item):
                return item.note*100000 - item.duration
    
            ci = 0
            this_index = []
            same_time_tones = [] #Keeping a list which tones *sound* at the same time in the original data 
            last_fret = 1 #Which fret the last tone(s) were played on
            for inx, note in enumerate(track):
                
                
                if note.index > ci: 
                
                
                    #Remove from stt all that have finished
                    if note.type != 'event' and inx > 0:
                        same_time_tones = [x for x in same_time_tones if not (x.original_index + x.duration < (track[inx-1].index))]
                        
                        
                    #Sort all in list
                    this_index = sorted(this_index,key=get_key)
                    
                    #Remove same tones (keep the longer ones)
                    old_tone = -1
                    new_list = []
                    for ti in this_index:
                        if ti.type == 'event': continue
                        if old_tone == -1:
                            old_tone = ti.note
                            new_list.append(ti)
                            continue
                        if ti.note != old_tone:
                            new_list.append(ti)
                        old_tone = ti.note
                    this_index = copy.copy(new_list)
                    
                    #Find optimal frets
                    begin_at_fret = 1
                    end_at_fret = guitar_settings[intr][3]-hand_width
                    tones_list = []
                    empty_strings = []
                    
                    for ti in this_index:
                        if ti.type != 'event':
                            tones_list.append(copy.copy(ti))
                                
                    # liste = []
                    # for tl in tones_list:
                    #     liste.append(tl.note)
                    # print ("*******")
                    # print (liste)
                    if len(tones_list) > 0:
                        #Put all tones in one hand range (lift them up to the highest tone)
                        highest_tone = tones_list[-1].note
                        lowest_possible_tone = highest_tone - tone_range_hand
                        
                        for x in range(0,len(tones_list)-1):
                            if tones_list[x].note < lowest_possible_tone and not tones_list[x].note in guitar_settings[intr][2]:
                                #Put all lower tones somewhere with the fewest neighbors within the range
                                note_value = tones_list[x].note % 12
                                possible_positions = []
                                for y in range (note_value,highest_tone,12):
                                    if y >= lowest_possible_tone:
                                        possible_positions.append(y)
                                
                                max_distance = 0
                                best_pos = 0
                                for ip,p in enumerate(possible_positions):
                                    min_distance = 127
                                    for y in range (0,len(tones_list)-1):
                                        if tones_list[y].note < lowest_possible_tone: continue
                                        if abs(tones_list[y].note - p) < min_distance: min_distance = abs(tones_list[y].note - p)
                                    if min_distance > max_distance: 
                                        max_distance = min_distance
                                        best_pos = ip
                                if len(possible_positions) > 0:
                                    tones_list[x].note = possible_positions[best_pos]
                                
                        #Put all tones onto the guitar
                        lowest_tone = 127
                        adjustment = 0
                        for x in range(0,len(tones_list)):
                            if tones_list[x].note < lowest_tone and not tones_list[x].note in guitar_settings[intr][2]: lowest_tone = tones_list[x].note
                        if lowest_string_tone > lowest_tone:
                            adjustment = lowest_string_tone - lowest_tone
                            adjustment = adjustment + (12-(adjustment % 12)) #round to the next octave
                        if highest_string_tone < highest_tone:
                            adjustment = highest_tone - highest_string_tone
                            adjustment = -(adjustment + (12-(adjustment % 12)))
                        for tl in tones_list:
                            if tl.note in guitar_settings[intr][2]: continue
                            tl.note += adjustment
                        
                        #Sort all in list
                        tones_list = sorted(tones_list,key=get_key)
                        new_list = []
                        new_list.append(tones_list[0])
                        for x in range(1,len(tones_list)):
                            if tones_list[x].note != tones_list[x-1].note:
                                new_list.append(tones_list[x])
                        tones_list = copy.copy(new_list)
                            
                        
                        
                

                    #Find out which frets are able to play most of the tones
                    in_fret_range = {}
                    for x in range(begin_at_fret,end_at_fret+1):
                        in_fret_range[x] = 0
                        
                    
                    for x in range(begin_at_fret,end_at_fret+1):
                        for tl in tones_list:
                            if tl.note in guitar_settings[intr][2]: continue
                            if tl.note >= x+lowest_string_tone and tl.note <= x+lowest_string_tone+tone_range_hand:
                                in_fret_range[x] += 1
                    fret_list = []
                   
                    max_no = 0
                    best_fit = 0
                    for val in in_fret_range:
                        if in_fret_range[val] > max_no:
                            max_no = min(possible_tones, in_fret_range[val]) #If only few tones possible, more frets are acceptable
                            
                    for val in in_fret_range:
                        if in_fret_range[val] >= max_no and max_no != 0:
                            fret_list.append(val)
                    # if (tones_list != []):
                    #     print (fret_list) 
                    if fret_list == []:
                        fret_list.append(last_fret)
                    
                    playable_notes_amounts = []
                    playable_notes = []
                    strings = sorted(copy.copy(guitar_settings[intr][2]))
                    used_strings = []
                    non_playable_notes = []
                    # tones_status = [] #Follows where the tones will be put

                    for infr,fr in enumerate(fret_list):
                        playable_amount = 0
                        string_index = len(strings)-1
                        tl_index = len(tones_list)-1
                        #ts_index = len(tones_list)-1
                        non_playable = []
                        playable = []
                        used = []
                        # status = {}
                        #print ("#########")
                        while string_index >= 0 and tl_index >= 0 and playable_amount < possible_tones:
                            base = strings[string_index] + fr
                            if (tones_list[tl_index].note == strings[string_index]):
                                
                          
                                
                                used.append(-2)
                                playable_amount += 1
                                playable.append(tones_list[tl_index])
                                string_index -= 1
                                tl_index -= 1 
                                #ts_index -= 1
                            elif (tones_list[tl_index].note >= base and tones_list[tl_index].note <= base+hand_width):
                                

                                used.append(tones_list[tl_index].note - base)
                                playable_amount += 1
                                playable.append(tones_list[tl_index])
                                string_index -= 1
                                tl_index -= 1
                                #ts_index -= 1
                                
                            else:
                                string_index -= 1
                                used.append(-1)

                                
                            while string_index >= 0 and tones_list[tl_index].note > strings[string_index]+fr+hand_width and tl_index>=0:
                                non_playable.append(tones_list[tl_index])
                                tl_index -= 1   #If not possible to find anymore, try next one
                        for x in range (tl_index,-1,-1):
                            non_playable.append(tones_list[tl_index])
                        while len(used) < len(strings):
                            used.append(-1)
                        non_playable_notes.append(non_playable)
                        playable_notes.append(playable)
                        used_strings.append(used)
                        # tones_status.append(status)
                        playable_notes_amounts.append(playable_amount)
                    
                    
                    
                    #Remove from fret_list frets that are less than ideal playable (that are not maximum)
                    max_playable = max(playable_notes_amounts)
                    new_list = []
                    new_used_list = []
                    new_playable = []
                    new_non_playable = []
                    for inpn, pn in enumerate(playable_notes_amounts):
                        if pn == max_playable:
                            new_list.append(fret_list[inpn])
                            new_used_list.append(used_strings[inpn])
                            new_playable.append(playable_notes[inpn])
                            new_non_playable.append(non_playable_notes[inpn])
                                                        
                    fret_list = copy.copy(new_list)
                    used_strings = copy.copy(new_used_list)
                    playable_notes = copy.copy(new_playable)
                    non_playable_notes = copy.copy(new_non_playable)
                                        
                                     
                    #Find the optimal fret to not move too much
                    favorite_fret = fret_list[0]
                    min_distance = guitar_settings[intr][3]
                    favorite_index = 0
                    for inf,f in enumerate(fret_list):
                        if abs(f - last_fret) < min_distance: 
                            min_distance = abs(f - last_fret)
                            favorite_fret = f
                            favorite_index = inf
                    
                    last_fret = favorite_fret


                            
                    tones_list = [x for x in tones_list if (x in playable_notes[favorite_index])]  

                    still_may_add = possible_tones - 1 - (len(playable_notes[favorite_index]))

                    
                     
                    #Try to add back the non-playable tones in a different octave
                    highest_string = 0
                    for inus,us in enumerate(used_strings):
                        if us != -1:
                            highest_string = inus
                            break
                    if highest_string < len(strings)-1:
                        for x in range (len(non_playable_notes[favorite_index])-1,-1,-1):
                            if still_may_add <= 0:
                                break
                            npn = non_playable_notes[favorite_index][x]
                            
                            for y in range (0,len(strings)-1): #highest_string+1
                                # print (favorite_fret)
                                # print (len(used_strings))
                                # print (used_strings[favorite_index])
                                
                                if used_strings[favorite_index][y] != -1: continue
                                try_note = npn.note % 12 - (strings[len(strings)-1-y] + favorite_fret) % 12 #
                                if try_note < 0: try_note += 12
                                if try_note >= 0 and try_note <= hand_width:
                                    #We found a fit!

                                    non_playable_notes[favorite_index][x].note = (strings[len(strings)-1-y] + favorite_fret) + try_note  #
                                    tones_list.append(non_playable_notes[favorite_index][x])
                                    still_may_add -= 1
                                    #print (used_strings)

                                    used_strings[favorite_index][y] = try_note
                                    # print (used_strings)                                    
                                    
                                    break

                    #Shorten all previous notes
                    if len(tones_list) > 0:
                        resolution = FileIO.ticks_per_beat*(1/8)
                            
                        last_index = -1
                        for inot in range(len(output_track)-1,-1,-1):
                            if last_index == -1: last_index = output_track[inot].index
                            if output_track[inot].index != last_index: #before last
                                break
                            allowed_length = tones_list[0].index - last_index
                            
                            if output_track[inot].duration > allowed_length:
                                output_track[inot].duration = allowed_length
                            if output_track[inot].duration <= FileIO.ticks_per_beat*(1/4):
                                output_track[inot].duration = allowed_length
                            
                            output_track[inot].duration = int(int(round(output_track[inot].duration/resolution)) * resolution)
                            
                        
                    
                    #Create the internal tabs (made up of normal tones, with extra info)
                    tab_entry = []
                    stringss = []
                    for intl,tl in enumerate(tones_list):
                        
                        tab_note = tl
                        
                        tab_note.base_fret = favorite_fret
                        
                        # if tones_status[favorite_index] == {0: [2, 7], 2: [0, 3]}:
                        #     print ("d")#
                        found = False
                        
                        for inus,us in enumerate(used_strings[favorite_index]):
                            val = strings[(len(strings)-1)-inus] + us + favorite_fret  #
                            if us == -1: continue
                            if us == -2: 
                                val = strings[(len(strings)-1)-inus]  #
                            
                            tone_height = val
                            if tone_height == tab_note.note:
                                if inus in stringss:
                                    continue
                                stringss.append(inus)
                                
                                #Unsort the strings -> put the tone on the xth lowest string
                                
                                strinx = 0 #which of multiple same strings (if existing)
                                for x in range (0,len(strings)):
                                    if x>0 and strings[x] == strings[x-1]:
                                        strinx+=1
                                    else:
                                        strinx = 0
                                    if x == inus:break
                                gsinx = 0
                                for gsin,gs in enumerate(guitar_settings[intr][2]):
                                    if gs == strings[len(strings)-1-inus]: strinx -= 1
                                    if strinx == -1:
                                        gsinx = gsin
                                        break
                                tab_note.string = gsinx
                                tab_note.fret = favorite_fret + us
                                if us == -2:
                                    tab_note.fret = 0
                                found = True
                                break
                        tab_entry.append(tab_note)
                    if len(tab_entry) != 0: tabs_track.append(tab_entry)
                    
                    
                    for x in range(0,len(this_index)):
                        
                        # if this_index[x].type == 'event':
                        #     output_track.append(this_index[x])
                        new_stt = copy.copy(this_index[x])
                        same_time_tones.append(new_stt)
                      
                    # for x in range(0,len(empty_strings)):
                    #     output_track.append(empty_strings[x])
                    for x in range(0,len(tones_list)):

                        output_track.append(tones_list[x])
                    
                    this_index = []    
                    ci = note.index
                
                this_index.append(note)
                
            
            Create_Guitar.tabs = copy.copy(tabs_track)
            output.append(output_track)
            
 
                
        
        return output[0]