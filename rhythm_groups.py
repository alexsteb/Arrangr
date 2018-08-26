from mido import MidiFile
from mido import Message
from mido import MidiTrack
from midi_IO import FileIO
from midi_tools import *
import sys
import copy
import math

class Create_Rhythm_Groups:

    
    def create (notes, combine_tracks = False):
        max_distance = 12
        
        def get_key(item):
            return item.note*100000 - item.duration
        
        #Check whether some old tones and some new tones might be related (depending on tone height)
        #[[rg1-tones],[rg2-tones], ...]
        def find_simple_matches(tones1,tones2):
            
            matches = []
            for t1 in tones1:
                found = False
                new_matches = []
                for t2 in tones2:
                    if t2.rg >= 0: continue
                    if abs(t1.note - t2.note) <= max_distance:
                        found = True
                        new_matches.append(t2)
                    if found and abs(t1.note - t2.note) > max_distance:
                        break
                matches.append(new_matches)
            rgs = []
            new_rg = []
            for inm,m in enumerate(matches):
                if len(m) > 0:
                    connected = False
                    for nm in m:
                        if nm in new_rg:
                            connected = True
                            break
                    if not connected and len(new_rg) > 0:
                        rgs.append(new_rg)
                        new_rg = []
                    new_rg.append(tones1[inm])
                    for nm in m:
                        if not nm in new_rg:
                            new_rg.append(nm)
                else:
                    if len(new_rg) > 0:
                        rgs.append(new_rg)
                        new_rg = []
            if len(new_rg) > 0:
                rgs.append(new_rg)
            return rgs
        
        rg_average = 0 #Updated before calling the sort function!
        def get_potentials_key(item):
            return abs(item.note - rg_average)
        
        def get_rhythm_key(item):
            return item.index
            
        def get_rhythm(tones):
            if len(tones) == 0: return []
            rg0 = copy.copy(tones)
            rg0 = sorted(rg0,key=get_rhythm_key)
            rg = []
            rg.append(rg0[0])
            #Delete duplicate indices
            for x in range(1,len(rg0)):
                if rg0[x].index != rg0[x-1].index:
                    rg.append(rg0[x])
            rhythm = []
            start = rg[0].index
            
            for _note in rg:
                rhythm.append(_note.index - start)
            # for _note in rg:
            #     # if last_end < _note.index:
            #     #     rhythm.append(-(_note.index - last_end))
            #     #     last_end = note.index
            #     rhythm.append(_note.duration)
            #     last_end += _note.duration
            return rhythm
       
        def fits_short_rhythm (index,group):
            ret_val = False
            if index == group.next_sr_index: 
                ret_val = True
                #Update the short_rhythm indices to the next future checkpoint
                group.next_sr_which += 1
                if group.next_sr_which == len(group.short_rhythm)-1:
                    group.next_sr_which = 0
                group.next_sr_index = index + group.short_rhythm[group.next_sr_which+1] - group.short_rhythm[group.next_sr_which]
            return ret_val
            
            
            # start = group.start_index
            # dists = []  
            # for x in range(1,len(group.short_rhythm)):
            #     dists.append(group.short_rhythm[x]-group.short_rhythm[x-1])
            # while start < index:
            #     for sr in dists:
            #         start += sr
            #         if start == index:
            #            return True
            # return False
            #          
                
       
        notes = Tools.unify_lengths(notes)
        notes = copy.copy(Tools.separate_melody(copy.copy(notes)))
        
        groups = []
        groups.append([0])
        _groups = []
        for x in range (1,len(notes)):
            _groups.append(x)
        groups.append(_groups)
        notes = Tools.combine_tracks_groups(notes,groups)
       
        
        output = []
        this_index = []
        ci = 0
        virgin_tones = []
        rg_cnt = 0
        rg_list = {}
        occupied_list = []
        #Main Loop
        for inno, note in enumerate(copy.copy(notes[1])):
        
            if note.index > ci:
                
                #Remove events
                tones_list = []
                
                for ti in this_index:
                    if ti.type != 'event':
                        tones_list.append(ti)
                        
                        
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
                tones_list = new_list
                
                
                #Check if any short rhythm's rhythm has been passed without a tone
                for rg in rg_list:
                    if rg_list[rg].next_sr_index < ci:
                        rg_list[rg].finalized = True
                
               
                #Try to put (remaining) new tones into existing rhythm groups
                #Put new tones in various combinations into rgs:
                    #average note value should not differ by more than max_distance
                #amount of notes should not differ by more than 1 tone
                    #variance should not grow (?) - (maybe try a maximum value here later)
                #rhythm matters ONCE short_rhythm has been found then it allows only the tones to be longer, but not the indices
                #if not found yet, add to the rhythm mix and try to find short_rhythm
                #If new tone(s) allowed into group, update the groups values
                should_match_list = []
                for rg in rg_list:
                    rg_list[rg].found_new_one = False
                    if rg_list[rg].finalized == True: continue
                  
                    
                    if rg_list[rg].short_rhythm != []:
                        # if rg_list[rg].short_rhythm == [0, 480, 720, 960]:
                        #     print ("d")
                        if not fits_short_rhythm(ci,rg_list[rg]): 
                            continue
                        else:
                            
                            should_match_list.append(rg)
                        
                    potentials = [] #List of notes that together might continue the rg
                    for tl in tones_list:
                        if tl.rg > -1: continue
                        if tl.note > rg_list[rg].allowed_highest_note or tl.note < rg_list[rg].allowed_lowest_note: continue
                        if (tl.note - rg_list[rg].average_note_value) > max_distance: continue
                        potentials.append(tl)
                    
                    if len(potentials) < rg_list[rg].allowed_lowest_amount: continue
                    if len(potentials) > rg_list[rg].allowed_highest_amount:
                        #Too many candidates for this rg - keep only the most fitting ones
                        rg_average = rg_list[rg].average_note_value
                        potentials = sorted(potentials,key=get_potentials_key)
                        potentials = potentials[0:rg_list[rg].allowed_highest_amount]
                    
                    #Now add all remaining tones finally to the rhythm group
                    for p in potentials:
                        p.rg = rg
                        rg_list[rg].my_tones.append(p)
                        
                    #Update the RG's values
                    rg_list[rg].add_to_rhythm(potentials[0])
                    rg_list[rg].create_short_rhythm()
                    rg_list[rg].found_new_one = True
                    rg_list[rg].notes_cnt += len(potentials)
                    
                #Finalize all Rhythm Groups that should have had a match with their short rhythm here, but didn't
                for rg in rg_list:
                    if not rg_list[rg].found_new_one and rg in should_match_list: 
                        rg_list[rg].finalized = True
                        rg_list[rg].finalized_at = ci  
                
                
                #Try to find a match for virgin tones and update the tones' states
                if len(virgin_tones) > 0:
                    rgs = find_simple_matches(virgin_tones,tones_list)
                    for inrgs, rg in enumerate(rgs):
                        note_vals = 0
                        amt_notes = 0
                        min_index = math.inf
                        max_index = 0
                        
                        rg_list[inrgs+rg_cnt] = Rhythm_Group()
                        rg_list[inrgs+rg_cnt].my_tones= [] 
                        for _note in rg:
                            if _note.index < min_index:
                                min_index = _note.index
                            if _note.index > max_index:
                                max_index = _note.index
                            _note.rg = inrgs+rg_cnt
                            note_vals += _note.note
                            amt_notes += 1
                            rg_list[inrgs+rg_cnt].my_tones.append(_note)
                        avg = note_vals / len(rg)
                        
                        variance = 0
                        for _note in rg:
                            variance += (_note.note-avg)**2
                                                
                        #Defnining the initial rhythm groups
                       
                        rg_list[inrgs+rg_cnt].start_index = min_index
                        rg_list[inrgs+rg_cnt].follows = -1
                        rg_list[inrgs+rg_cnt].last_index = max_index
                        
                        rg_list[inrgs+rg_cnt].average_note_value = avg
                        rg_list[inrgs+rg_cnt].average_amount_notes = amt_notes / 2
                        rg_list[inrgs+rg_cnt].note_variance = variance / (len(rg)-1)
                        rg_list[inrgs+rg_cnt].rhythm = get_rhythm(rg)
                        rg_list[inrgs+rg_cnt].short_rhythm = []
                                                
                        rg_list[inrgs+rg_cnt].notes_cnt = amt_notes
                        rg_list[inrgs+rg_cnt].set_allowed_range()  
                        rg_list[inrgs+rg_cnt].set_allowed_amounts()  
                        rg_list[inrgs+rg_cnt].finalized = False   
                        rg_list[inrgs+rg_cnt].finalized_at = math.inf   
                        rg_list[inrgs+rg_cnt].next_sr_index = math.inf
                        rg_list[inrgs+rg_cnt].next_sr_which = math.inf
                                                     
                        
                        rg_list[inrgs+rg_cnt].rg_index = inrgs+rg_cnt
                        
                              
           
                    rg_cnt += len(rgs)
                    virgin_tones = [x for x in virgin_tones if not (x.rg >= 0)]
                    #print (ci)
                    #if ci > 24000:
                        

               
               
                
                
                
                
                
                
                #Put all (remaining) new tones into virgin tones list
                for tl in tones_list:
                    if tl.rg == -1:
                        virgin_tones.append(tl)
             

                ci = note.index
                this_index = []
            
            this_index.append(note)
        
        output = []
        
        def rg_by_average_note_key(item):
            return rg_list[item].average_note_value
        
        def similar_rhythm(rh1,rh2):
            if len(rh1) != len(rh2): return False
            
            dists1 = []
            dists2 = []
            for x in range(1,len(rh1)):
                dists1.append(rh1[x]-rh1[x-1])
                dists2.append(rh2[x]-rh2[x-1])
            
            for x in range (0,len(dists1)):
                if dists1 == dists2: return True
                dists2.insert(0,dists2[-1])
                dists2 = dists2[0:len(dists2)-1]
            return False
                                
        
        
        
        #=======================================================================
        # for _note in notes[1]:
        #     #Put rg-free tones onto any rg that has a fitting range
        #     if _note.rg == -1:
        #         for rg in rg_list:
        #             if _note.note < rg_list[rg].allowed_highest_note and _note.note > rg_list[rg].allowed_lowest_note:
        #                 _note.rg = rg
        #                 break
        #=======================================================================
        
        #Create follow values (Have similar rgs on the same track) -> Use this code in later stages. Not in this class.
        if combine_tracks:
            for rg in rg_list:
                
                for x in range (0,rg):
                    if rg_list[x].finalized_at != rg_list[rg].start_index:
                        if abs(rg_list[x].average_note_value -rg_list[rg].average_note_value) < 6:
                            if abs(rg_list[x].average_amount_notes -rg_list[rg].average_amount_notes) < 2:
                                #if similar_rhythm(rg_list[x].short_rhythm, rg_list[rg].short_rhythm):
                                rg_list[rg].follows = x
                                rg_list[x].finalized_at = rg_list[rg].finalized_at #So not more than 1 rg immediately follows the old one
                                break
        
        
        
        for rg in rg_list:
            if rg_list[rg].follows == -1: continue
            for _tone in rg_list[rg].my_tones:
                _tone.rg = rg_list[rg].follows
                                
            
        for x in range(0,len(rg_list)+1):
            output.append([])
        for _note in notes[1]:
            
            
            output[_note.rg+1].append(_note)
        
        
             
        # rg_sorted = sorted(rg_list,key=rg_by_average_note_key)
        # 
        # for rgin,rg in enumerate(rg_sorted):
        #     for _note in rg_list[rg].my_tones:
        #         if _note.rg != -1:
        #             print (rgin)
        #             output[rgin].append(_note)
        
        output =  [x for x in output if not x == []]    
        output.insert(0,notes[0])    
        return output
        #return notes
    
    
class Rhythm_Group:
    def __init__(self):
        #. Save average tone height, average amount of tones + each plus a floating average, tone variance, rhythmic history
       
        start_index = 0
        last_index = 0  #index of last note
        
        rg_index = 0
        follows = -1
        
        my_tones = [] #holds a reference to all tones in this group
       
        average_note_value = -1.0
        average_amount_notes = -1.0
        note_variance = -1.0
        # fl_average_note_value = -1.0
        # fl_average_amount_notes = -1.0
        # fl_note_variance = -1.0
        
        notes_cnt = 0
        
        allowed_highest_note = 0
        allowed_lowest_note = 0
        allowed_highest_amount = 0
        allowed_lowest_amount = 0
        
        rhythm = [] #in beats: 1.0,0.5 = quarter,quarter rest, eigth [But using the index format. It won't change anyway]
        short_rhythm = [] #any identified repeating rhythm
        
        next_sr_index = 0
        next_sr_which = 0 #Which element of short_rhythm is to be expected at next_sr_index? If that time is passed, without any tone, finalize the rg
        
        finalized = False #If short_rhythm could not be confirmed
        finalized_at = 0  #starting here, this channel is free
        found_new_one = False
        
    def set_allowed_range(self):
        if self.note_variance < 0: return
        sd = math.sqrt(self.note_variance)
        distance = sd*math.sqrt(1+(1/self.notes_cnt))+5
        self.allowed_highest_note = math.ceil(self.average_note_value + distance)
        self.allowed_lowest_note = math.floor(self.average_note_value - distance)
        return
    
    def set_allowed_amounts(self):
        self.allowed_highest_amount = math.ceil(self.average_amount_notes + 1)
        self.allowed_lowest_amount = math.floor(self.average_amount_notes - 1)
        if self.allowed_lowest_amount < 1: self.allowed_lowest_amount = 1
        return
        
    def add_to_rhythm(self,note):
        self.rhythm.append(note.index - self.start_index)
        self.last_index = note.index
        return
        
    def create_short_rhythm(self):
        if len (self.short_rhythm) > 0: return
        if len(self.rhythm) < 4: return
        if len(self.rhythm) > 8: 
            #He tried multiple times to find a short-rhythm. Now it's too late:
            for _tone in self.my_tones:
                _tone.rg = -1
                self.my_tones = []
                self.finalized = True
                self.finalized_at = 0
            return
        

        dists = []
        for x in range(1,len(self.rhythm)):
            dists.append(self.rhythm[x]-self.rhythm[x-1])
        
        short_length = len(dists)
        for x in range (len(dists)-1,0,-1):
            fits = True
            inx = 0
            for y in range (x,len(dists)):
                if dists[x+inx] != dists[inx]: 
                    fits = False
                    break
                inx += 1
            if fits: short_length = x
        
        # self.short_rhythm.append(0)
        # for x in range(0,short_length):
            
        self.short_rhythm = self.rhythm[0:short_length+1]
        if len(self.short_rhythm)>len(self.rhythm)-1 or len(self.short_rhythm) < 2:
            self.short_rhythm = []
        else:
            self.next_sr_which = (len(self.rhythm)-1) % short_length
            self.next_sr_index = self.start_index + self.rhythm[-1] + (self.rhythm[self.next_sr_which+1] - self.rhythm[self.next_sr_which])
       
        if self.rg_index == 0:
            print ("Rhythm: "+str(self.rhythm))
            print ("Short-Rhythm: "+str(self.short_rhythm))
            print ("next index: "+str(self.next_sr_index))
            print ("next which: "+str(self.next_sr_which))
            
       
        return
        
                
        