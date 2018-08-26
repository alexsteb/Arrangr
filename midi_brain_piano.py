from midi_tools import *
from rhythm_groups import *
import sys
import copy
import math

class Create_Piano:
    
    combining_groups = [[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]]
    
    def arrange (notes):
        
        pianos = len(Create_Piano.combining_groups)
        
        notes = Tools.combine_tracks_groups(notes,Create_Piano.combining_groups)
        
        
        
        output = []
        #Main Loop / Do everything below this again for each piano
        for intr, track in enumerate(notes):
            
            right_hand = []
            left_hand = []
            this_notes = [] #will be multi-track
            this_notes.append(track)
            this_notes = Create_Rhythm_Groups.create(this_notes, combine_tracks = False) #True
            for x in this_notes:
                output.append(x)
            return output
                        
            
            #Find the average tone heights of the tracks
            avg_list = []
            for _track in this_notes:
                note_heights = 0
                for _note in _track:
                    note_heights += _note.note
                avg = note_heights / len(_track)
                avg_list.append(avg)
            
            #Give the lowest 60% to the left hand - rest to the right hand
            split_percentage = 0.6
            sorted_avg_list = sorted(avg_list)
            split_avg = sorted_avg_list[int(round(0.6*len(sorted_avg_list)))] #Index of first right hand track
            combining_groups = []
            left_cg = []
            right_cg = []
            for alin, al in enumerate(avg_list):
                if al < split_avg:
                    left_cg.append(alin)
                else:
                    right_cg.append(alin)
            combining_groups.append(right_cg)
            combining_groups.append(left_cg)
                        
            two_hands = Tools.combine_tracks_groups(this_notes,combining_groups)
            
            
            #Remove and change notes that are unplayable
            ############################################
            
            #Finding the most comfortable fit, between lowest and highest tone
            # begin_at = 0
            # end_at = 120 #120 = C10
            # 
            # in_range = {}
            # for x in range(begin_at,end_at+1,12):
            #     in_range[x] = 0
            # end_it = False
            # for note in two_hands[1]:
            #     if note.type == 'event': continue
            #     for x in range (begin_at,end_at+1,12):
            #         if note.note >= x and note.note <= x+12:
            #             in_range[x] += 1
            # 
            # #print (in_range)
            # max_no = 0
            # best_fit = 0
            # for val in in_range:
            #     if in_range[val] >= max_no: #Choose the highest fit, so it gets transposed down and is easier to play
            #         max_no = in_range[val]
            #         best_fit = val
            # adjustment = - best_fit
            # 
            # for note in track:
            #     if note.type != 'event':
            #         note.note += adjustment
            
            
            def get_key(item):
                return item.note*100000 - item.duration
            
            
            output_hand = [[],[]]
            
            two_hands[0].append(Event(index=two_hands[0][-1].index+10000))
            two_hands[1].append(Event(index=two_hands[0][-1].index+10000))
            
            for hand in range(0,2):
                ci = 0
                this_index = []
                distance = 0
                last_lowest = -1
                            
                for thin,note in enumerate(two_hands[hand]):
                    if note.index > ci:
                        distance = note.index - ci
                        tones_list = []
                        for ti in this_index:
                            if ti.type != 'event':
                                tones_list.append(copy.copy(ti))
                        
                        #Sort all in list
                        tones_list = sorted(tones_list,key=get_key)
                        
                        #Remove same tones (keep the longer ones)
                        old_tone = -1
                        new_list = []
                        for ti in tones_list:
                            if ti.type == 'event': continue
                            if old_tone == -1:
                                old_tone = ti.note
                                new_list.append(ti)
                                continue
                            if ti.note != old_tone:
                                new_list.append(ti)
                            old_tone = ti.note
                        tones_list = copy.copy(new_list)
                        
                        if len(tones_list) > 0:
                            #Put all tones in one hand range (lift them up to the highest tone)
                            highest_tone = tones_list[-1].note
                            lowest_possible_tone = highest_tone - 12
                            
                            for x in range(0,len(tones_list)-1):
                                if tones_list[x].note < lowest_possible_tone:
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
                                    
                                    tones_list[x].note = possible_positions[best_pos]
                            
                            allowed0 = 5
                            tones_list = sorted(tones_list,key=get_key)
                            if abs(tones_list[0].note - tones_list[-1].note) > 9:allowed0 = 4
                            
                            #Judge distance to next tone
                            allowed1 = 5
                            if distance <= (FileIO.ticks_per_beat/2): allowed1 = 3
                            if distance <= (FileIO.ticks_per_beat/4): allowed1 = 2
                            
                            #Judge tone height difference to last one
                            allowed2 = 5
                            if last_lowest != -1:
                                difference = abs(last_lowest - tones_list[0].note)
                            
                                if difference >= 6: allowed2 = 3
                                if difference >= 8: allowed2 = 2
                                if difference >= 12 and hand == 1:  #Right hand only
                                    #Lift tones up or down, if difference is too high
                                    factor = int(round(difference / 12))
                                    direction = 1
                                    #print (factor)
                                    if last_lowest - tones_list[0].note < 0: direction = -1
                                    
                                    for tl in tones_list:
                                        if tl.note + direction*factor*12 < 36 or tl.note + direction*factor*12 > 48:
                                            factor = int(factor/2)
                                    for tl in tones_list:    
                                        tl.note += direction*factor*12
                            
                            last_lowest = tones_list[0].note
                            
                            
                            #Remove too many tones
                            tones_allowed = min([allowed0,allowed1,allowed2])
                            neighbor_list = []
                            if len(tones_list)>1:
                                neighbor_list.append(tones_list[1].note-tones_list[0].note)
                            for x in range(1,len(tones_list)-1):
                                neighbor_list.append(min([tones_list[x].note-tones_list[x-1].note,tones_list[x+1].note-tones_list[x].note]))
                            if len(neighbor_list) > 1:
                                while len(tones_list) > tones_allowed:
                                    min_nb = min(neighbor_list)
                                    new_list = []
                                    new_neighbor_list = []
                                    for nbin,nb in enumerate(neighbor_list):
                                        if nb != min_nb:
                                            new_list.append(tones_list[nbin])
                                            new_neighbor_list.append(neighbor_list[nbin])
                                            if len(new_list) == tones_allowed: break
                                    neighbor_list = copy.copy(new_neighbor_list)
                                    tones_list = copy.copy(new_list)
                            
                            
                                                    
                                                    
                            #Shorten too long tones
                            for tl in tones_list:
                                if tl.duration > distance:
                                    tl.duration = distance
                        
                            for tl in tones_list:
                                output_hand[hand].append(tl)
                        
                        ci=note.index
                        this_index = []
                    this_index.append(note)
                
            
            
            output.append(output_hand[0])
            output.append(output_hand[1])
            
            # for tn in this_notes:
            #     output.append(tn)
 
                
        
        return output
    