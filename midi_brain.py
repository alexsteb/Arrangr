from mido import MidiFile
from mido import Message
from mido import MidiTrack
from midi_IO import *
from midi_tools import *
import sys
import copy
import math
from timeit import default_timer as timer

class Create:
    def arrange(notes):
        
             
        notes = Tools.combine_tracks(notes)
        
#Setting        
        chords = Tools.find_chords(notes[0])
        chords = Tools.simplify_chords(chords,2, True)
        chord_track = Tools.create_chord_track(chords) #Probably soon deleted
        
    
#Setting #If too many tones in one voice: (After moving around)
         #0 - Allow it
         #1 - Arpeggiate (Have to set the arpeggio value then
         #2 - keep only the most important note
        too_many_tones = 1

#Setting #Try to attach notes to other voices if possible
        try_to_attach = True
          
#Setting #Difficulty 16th notes: max distance in half-tones (but minimum 6) = difficulty * (180-Tempo)* (Beats*4) * 12 / 80 
         #difficulty should be between 0,25 and 4 
        difficulty = 1
        
#Setting        
        arpeggio = 5  #If 0, then the "Select the most relevant tone" function should start
        
        cnt_bs = 0
        
#Setting #Duration to be used, if Arpeggio is turned off
        short_duration = 5
        
#Setting 
        keep_melody_long = 0
#Setting
        all_short = 0 #1 = Keep everything short, 0 = always try to play something
        
#Setting Simultaneous tones
        sim_tones = 1
        
        track = notes[0]
        size = Tools.amount_indices(track)
        
        ci = 0
        this_index = []
        this_index_start = 0
        
        output = []
        for x in range(0,sim_tones):
            tr = []
            output.append(tr)
            
        last_final_index = 0
        last_final_indices = []
        for x in range (0,sim_tones):
            last_final_indices.append(0)
        same_time_tones = [] #Keeping a list which tones *sound* at the same time in the original data 
        #stt_voice = [] #Following along to remember in which voice the tone was saved

        
        dur = [-1,0,0,0,0]
        
        def get_key(item):
            return item.note*100000 + item.index
        
        def get_stt_key(item):
            return -item.original_index
          
          
          
          
          
        
        
        
        
        
        current_tempo = 500000
        for tr_index, note in enumerate(track):
            if note.type == 'event' and note.msg.type != 'note_off':
                
                if note.msg.type == 'set_tempo':
                    current_tempo = note.msg.tempo
            
            
            
            if note.index > ci: #New note position
              
                len_this_index = len(this_index)
                           
                if last_final_index >= this_index[0].index and last_final_index != 0:
                    delay = last_final_index - this_index[0].index + arpeggio  
                else:
                    delay = 0
                

#Setting        #Remove from Same Time Tones all tones that have finished recently
                
                if note.type != 'event' and tr_index > 0:

                    same_time_tones = [x for x in same_time_tones if not (x.original_index + x.duration < (track[tr_index-1].index-delay))]
                    
                    
            

#Setting        #Shortening all to arpeggio value
                if all_short == 1:
                    for strack in output:
                        if len(strack) > 0:
                            if arpeggio == 0:
                                strack[-1].duration = short_duration
                            else:
                                strack[-1].duration = arpeggio
                    
                
                #Moving every new note to the voice with the highest relevance that fits the range
                #(Voices will be later sorted automatically according to their pitch, so that the 135642 shape will be used.)
               
                #Sort all in list
                this_index = sorted(this_index,key=get_key)
               
                voice = [] #In which voice does the "this_index" entry lie currently?
                fits = []  #List of fitting voices per entry - sorted best to worst
                voice_ranges = []
                
                for x in range (0,len(this_index)):
                    fit = []
                
                
                    for y in range (0,sim_tones): #Replace later. Check for each tone, which voices could play it, sorted highest relevance to lowest
                        fit.append(y)
                    
                    #voice_ranges.append([55,90])
                    #voice_ranges.append([28,48])
                    #voice_ranges.append([48,76])
                    #voice_ranges.append([40,57])                    
                    #if this_index[x].note >= 55:
                    #    fit.append(0)
                    #if this_index[x].note <= 48:
                    #    fit.append(1)
                    #if this_index[x].note >= 48 and this_index[x].note <= 76:
                    #    fit.append(2)
                    #if this_index[x].note >= 40 and this_index[x].note <= 57:
                    #    fit.append(3)
                    
                    # if this_index[x].note >= 51:
                    #     fit.append(0)
                    # if this_index[x].note <= 48:
                    #     fit.append(1)
                    # if this_index[x].note >= 40 and this_index[x].note <= 55:
                    #     fit.append(2)
                        
                        #No matter how user chooses the instrument ranges - sorting will always be 13542 highest to lowest
                    
                                    
                    
                    fits.append(fit)
                    voice.append(min(fit))
                
                start1 = timer()
                
                
                stt_voices = []  #in which voice/tracks are the currently looming tones located
                for s in same_time_tones:
                    stt_voices.append(-1)
                
                if tr_index == 200:
                    print ("d")
                
                stt_list = sorted(same_time_tones,key=get_stt_key)
                # if tr_index > 100 and tr_index < 250:
                    # print ("")
                    # print ("*****")
                    # for s in stt_list:
                    #     print (s.__dict__)
                cnt_bs += len(stt_list)
                find = False
                find0 = False
                stt_cnt = 0
                if len(stt_list)>0:

                    for intr,tr in enumerate(output):
                        #for instt,s in enumerate(same_time_tones):
                        while stt_list[stt_cnt].type == 'event':
                            stt_cnt += 1
                            if stt_cnt == len(stt_list):
                                find0 = True
                                break
                        if find0 == True:
                            break
                        for x in range(len(tr)-1,-1,-1):
                            # print (x)
                            # print (stt_cnt)
                            
                            
                            
                            if tr[x].original_index == stt_list[stt_cnt].original_index and tr[x].note == s.note:
                                stt_voices[stt_cnt] = intr 
                                stt_cnt += 1
                                if stt_cnt == len(stt_list):
                                    find = True
                                break
                            if tr[x].original_index < stt_list[stt_cnt].original_index:
                                # find = True
                                break
                        if find:
                            break
                
                end1 = timer()
                dur[1] += (end1-start1)
                
                start2 = timer()
                #Move notes down until they are at their lowest relevance fit
                all_ok = 0
                while (all_ok == 0):
                    for i,t in enumerate(this_index):
                        #if t.note == 31:
                            # print (voice[i])
                        looming_tone = 0
                        all_ok = 1
                        for s in stt_voices:
                            if voice[i] == s:
                                looming_tone = 1
                                all_ok = 0
                                break
                        if looming_tone == 1:
                            for j,f in enumerate(fits[i]):
                                if f == voice[i] and j<(len(fits[i])-1):  #if not: already at its worst position
                                    voice[i] = fits[i][j+1]
                                    break
                                else:
                                    all_ok = 1
                end2 = timer()
                dur[2] += (end2-start2)
                #Try to have the amount of tones in each voice ideally same (hand them down, if fitting)
                
                start3 = timer()
                voice_amounts = {}
                for x in range (0,sim_tones):
                    voice_amounts[x] = 0
                for inv,v in enumerate(voice):
                    if this_index[inv].type == 'event': continue
                    voice_amounts[v] += 1
                
                for st in range(0,sim_tones):
                    for x in range(0, sim_tones-1):
                        is_low = (x % 2) #low voices should try to give away to a higher voice +1,-1
                        if voice_amounts[x] > 1:
                            for y in range(0,len(this_index)):
                                if voice_amounts[x] <= 1:
                                    break
                                ind_y = y
                                
                                if is_low == 1:
                                    ind_y = len(this_index)-y-1  #which note to choose first
                                if voice[ind_y] != x:
                                    continue
                                
                                for j,f in enumerate(fits[ind_y]):
                                    if f == voice[ind_y] and j<(len(fits[ind_y])-1):  #if not: already at its worst position
                                        
                                        if voice_amounts[x] > voice_amounts[fits[ind_y][j+1]]:
                                            voice[ind_y] = fits[ind_y][j+1]
                                            voice_amounts[x] -= 1
                                            voice_amounts[fits[ind_y][j+1]] += 1
                                            break
                            
                
                end3 = timer()
                dur[3] += (end3-start3)    
                
                
                #Try to give multiple notes to other tracks that are not playing anything right now
                for x in range(0,sim_tones):
                    if voice_amounts[x] <= 1: continue
                    for y in range(1,sim_tones):
                        if y <= x: continue
                        if voice_amounts[y] < voice_amounts[x]: ##Move them as long as they can take it
                            for inz, ti in enumerate(this_index):
                                
                                if voice[inz] == x:
                                    voice[inz] = y
                                    voice_amounts[x] -= 1
                                    voice_amounts[y] += 1
                                    mid_range = (voice_ranges[y][1]-voice_ranges[y][0])*2
                                    if ti.note != mid_range and (abs(ti.note - mid_range) > 12 or ti.note < voice_ranges[y][0] or ti.note > voice_ranges[y][1]):
                                        factor = -(ti.note - mid_range) / abs(ti.note - mid_range)
                                        while abs(ti.note - mid_range) > 12 and ti.note > 12:
                                            ti.note += int(12*factor)
                                    
                                if voice_amounts[y] >= voice_amounts[x]: break   
                        
                                    
                            
                        
                

#Setting        #Preference for longest note
                if all_short == 0:
                    for x,tr in enumerate(output):
                        if len(tr) > 0:
                  
                            
                            if not tr[-1].duration < (this_index[0].index - last_final_indices[x]) and voice_amounts[x] > 0: #Only shorten, if too long - and if there is a new tone is the respective voice
                                tr[-1].duration = this_index[0].index - last_final_indices[x]
                                if tr[-1].duration < 0:
                                    tr[-1].duration = arpeggio
                        

#Setting        #Adjust voices for difficulty
                if difficulty != 0:
                    for inx,tr in enumerate(output):
                        if len(tr) > 0:
                            last_height = tr[-1].note
                            if tr[-1].type == 'event': break
                            for iny,ti in enumerate(this_index):
                                if voice[iny] == inx and ti.type != 'event':
                                    this_height = ti.note
                                    max_distance = difficulty * (180-(60000000 / current_tempo))* (tr[-1].beats*4) * 12 / 80
                                    if max_distance < 6: max_distance = 6 
                                    if abs(this_height - last_height) > max_distance:
                                        if this_height >= last_height: factor = 1
                                        if this_height < last_height: factor = -1
                                        while abs(this_height - last_height) > max_distance:
                                            this_index[iny].note -= (12*factor)
                                            this_height = this_index[iny].note
                                                                                
                                        
                                


                start4 = timer()
                
                
                if too_many_tones == 2 and len_this_index > 1: #Just keep the most important tone
                    for inx,o in enumerate(output):
                        if voice_amounts[inx] > 1:
                            _min = 100
                            _max = 0
                            for iny,ti in enumerate(this_index):
                                if voice[iny] == inx:
                                    if ti.note > _max and ti.type != 'event': _max = ti.note
                                    if ti.note < _min and ti.type != 'event': _min = ti.note
                            for iny,ti in enumerate(this_index):
                                if voice[iny] == inx:
                                    if ((voice[iny] % 2 == 0 and ti.note == _max) or ti.type == 'event') or (voice[iny] % 2 == 1 and ti.note == _min): #high tones
                                            output[voice[iny]].append(this_index[iny])
                                            
                                            if this_index[iny].index >= last_final_indices[voice[iny]]:
                                                last_final_indices[voice[iny]] = this_index[iny].index
                                            if this_index[iny].index >= last_final_index:
                                                last_final_index = this_index[iny].index

                                            
                        else:
                            for iny,ti in enumerate(this_index):
                                if voice[iny] == inx:
                                    output[voice[iny]].append(this_index[iny])
                                    if this_index[iny].index >= last_final_indices[voice[iny]]:
                                        last_final_indices[voice[iny]] = this_index[iny].index
                                    if this_index[iny].index >= last_final_index:
                                        last_final_index = this_index[iny].index
                            
                            
                elif len_this_index > 1 and too_many_tones != 2:  #If at the end of chord collection
                                
                        
                   
                    cnt_notes = 0
                    first_note = -1
                    newly_created_note = None
                    
                    for index,s in enumerate(this_index):
                        if s.type == 'note':
                            if first_note == -1:
                                first_note = index
                            cnt_notes += 1    
 
                                       
                    distance = 0
                    distance_list = {}
                    for x in range(0,sim_tones):
                        distance_list[x] = 0
                    
                    for x in range(0,len(this_index)):
                        
                        if this_index[x].type == 'event':
                            this_index[x].index += delay
                            output[0].append(this_index[x]) #events can stay at the first track(?)
                            continue
                            


                        this_index[x].index += distance_list[voice[x]]
                        this_index[x].index += delay
                        #print (this_index[x].__dict__)
                        
#Setting                 
                        #if keep_melody_long==1:
                        new_stt = copy.copy(this_index[x])
                        
                        same_time_tones.append(new_stt) 
                          
#Setting                                              
                        if too_many_tones == 1: #Arpeggiate
                            distance_list[voice[x]] += arpeggio
                
                            if arpeggio == 0:
                                this_index[x].duration = short_duration
                            else:
                                this_index[x].duration = arpeggio
                            
                    
                        output[voice[x]].append(this_index[x])
                      
                        if this_index[x].index >= last_final_indices[voice[x]]:
                            last_final_indices[voice[x]] = this_index[x].index
                        if this_index[x].index >= last_final_index:
                            last_final_index = this_index[x].index
                
                if len_this_index == 1 and too_many_tones != 2: #If there is only one simultaneous tone
                    this_index[0].index += delay
                    output[voice[0]].append(this_index[0])
                    last_final_indices[voice[0]] = this_index[0].index
                    last_final_index = this_index[0].index
#Setting                    
                    #if keep_melody_long==1:
                    same_time_tones.append(copy.copy(this_index[0]))  


                #Restore original duration, after arpeggio
                for v in range(0,sim_tones):
                    if len(output[v]) > 0:
                        output[v][-1].duration = output[v][-1].original_duration
                    
                end4 = timer()
                dur[4] += (end4-start4)




         
              ###     
                # #What happens anyway, after a new time index was reached: (if previous was chord or not)
                
#Setting
                if keep_melody_long==1:

                            
                    if len(same_time_tones) > 0 and cnt_notes > 0:
                        
                        
                        same_time_tones = sorted(same_time_tones,key=get_key)
                        
                        highest_new_tone = None
                        highest_old_tone = None
                        is_highest_overall = -1
                        if this_index[0].index >= 0 and this_index[0].index < 5000:
                            print ("")
                            print (this_index[0].index)
                            print ("*******")
                        
                        if this_index[0].index == 4320:
                            print ("debug")
                        
                        for tone in same_time_tones:
                            if this_index[0].index >= 0 and this_index[0].index < 5000:
                                print (str(tone.index)+": "+str(tone.note_name)+str(tone.octave))
                            if tone.index >= this_index[first_note].index: #If tone arrived newly at this index
                                highest_new_tone = tone                 #They are sorted, so it's always the latest
                                is_highest_overall = 1
                                
                            else:
                                highest_old_tone = tone
                                if is_highest_overall == 1:             
                                    is_highest_overall = 0              #This value will only be reached, if there is any new note
                        
                        
                        #Remove (not-highest) arpeggiated values from the list -> they will never be important
                        same_time_tones = [x for x in same_time_tones if not (x != highest_new_tone and x.index >= this_index[first_note].index)]
                        
                        
                        if this_index[0].index >= 0 and this_index[0].index < 5000:
                            if is_highest_overall == 1:
                                print ("1 - A new tone came, that is now the highest in the mix.") 
                            if is_highest_overall == 0:
                                print ("0 - A new tone came, but the old one is still higher.") 
                            if is_highest_overall == -1:
                                print ("-1 - Only old tones at this time index.") 
                                                        
                            if highest_new_tone == None:
                                print ("new = none")
                            if highest_old_tone == None:
                                print ("old = none")
                    
                        
                        
                        if is_highest_overall == 1:           
                            found1 = 0
                            found2 = 0
                            for x in range(len(output)-1,-1,-1):
                                if found1 == 1 and found2 == 1:
                                    break
                                    
                                if found1 == 0 and output[x].index == highest_new_tone.index and output[x].note == highest_new_tone.note:
                                    found1 = 1
                                    #Give that highest tone its full duration
                                    
                                    
                                    output[x].duration = highest_new_tone.duration 
                                
                                if found2 == 0 and highest_old_tone != None and output[x].index == highest_old_tone.index and output[x].note == highest_old_tone.note:
                                    found2 = 1
                                    #Stop the previous highest tone
                                
                                    output[x].duration = (this_index[first_note].index)-output[x].index
                                    
                                    same_time_tones = [x for x in same_time_tones if not (x.index == highest_old_tone.index and x.note == highest_old_tone.note)]
                                
                                    
                                
                                if highest_old_tone == None:
                                    found2 = 1
                                    
                        elif is_highest_overall == 0:
                            found = 0
                            for x in range(len(output)-1,-1,-1):
                                if found == 1:
                                    break
                        
                                if output[x].index == highest_old_tone.index and output[x].note == highest_old_tone.note and output[x].type != 'event':
                                    found = 1
                                    #Stop the previous highest tone
                                    temp = output[x].duration
                                    temp_note = copy.copy(output[x])
                                    output[x].duration = (this_index[first_note].index)-output[x].index
                                    if output[x].index == 3890:
                                        print ("huh?")
                                        print (output[x].__dict__)
                                    
                                    
                                    highest_old_tone.duration = (this_index[first_note].index)-highest_old_tone.index
                                    same_time_tones = [x for x in same_time_tones if not (x.index == highest_old_tone.index and x.note == highest_old_tone.note)]
                                    #82000 and this_index[0].index < 83155:
                                    if this_index[0].index >= 0 and this_index[0].index < 5000:
                                        for s in same_time_tones:
                                            print (s.__dict__)
                                        print ("")
                                    same_time_tones = [x for x in same_time_tones if not (x.index < this_index[0].index)]
                                    
                                
                                    #If the previous highest tone ends earlier than the new one, play the new one
                                    len_old_high = temp + output[x].index - this_index[0].index
                                    if len_old_high < 0:
                                        len_old_high = 0
                                    len_new_high = highest_new_tone.duration
                                    
                                    #If old one is still relevant, shorten all new ones
                                    if len_old_high > len_new_high:
                                        for y in range(len(output)-1,-1,-1):
                                            if output[y].index == highest_new_tone.index and output[y].note == highest_new_tone.note:
                                               
                                                output[y].duration = arpeggio
                                                same_time_tones = []
                                                break
                                            
                                        
                this_index = []    
                ci = note.index
                
            this_index.append(note)
            
            
        
        notes = []
        
        #output.append(chord_track)
        
        for tr in output:
            for i,c in enumerate(tr):
                if i > 0:
                    if tr[i].index < tr[i-1].index:
                        result = False
                        inx = i
                        while result == False and inx > 0:
                            tr[inx], tr[inx-1] = tr[inx-1], tr[inx]
                            inx -= 1
                            result = tr[inx].index > tr[inx-1].index
                            
        # for i,c in enumerate(output[3]):
        #     if i > 0:
        #         print (output[3][i].index - output[3][i-1].index)     
                        
        return output
        

        
        