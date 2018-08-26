from midi_break_points import *
import math, copy
from random import shuffle
from pickle import INST

#midi arrange:
#1. Retrieve all break points
#2. Between each break point / for each segment decide which instruments to silence -> simply empty them
#2.5. At the break point measure create a transition 
#3. Put Melody back onto the music but keep a reference

def arrange(segments, tracks, melody, instruments,groups,averages,ranges,channels,dont_add_melody):
    #1.) Get Break Points
    big_break_points = get_big_break_points(tracks)
    small_break_points = get_small_break_points(big_break_points) #Just for some variation
    last_measure = big_break_points[-1]
    del big_break_points[-1]
    
    breakpoints = big_break_points + small_break_points
    breakpoints.sort()
    print (breakpoints)
    
    #Get playing instruments per measure
    remix = get_remix(breakpoints,instruments,groups,averages)
    print (remix)
    #remix = [[4, 2], [0, 2, 3], [1, 3], [3, 4, 1, 2], [0, 3, 1], [2, 4, 3, 0, 1], [1, 4]]
    #Create list of instruments that have to take the melody voice (always the one playing that is closest to the melody's range)
    melody_list = get_melody_list(breakpoints,last_measure,remix,melody,averages,ranges)
    print (melody_list[0])
    
   
    #Get amount of notes per instrument per part between breakpoints + how to adjust tones if trying to move them between different instruments
    note_amounts_and_how_to_transpose = get_note_amounts(segments,breakpoints,instruments,last_measure,averages)
    note_amounts = note_amounts_and_how_to_transpose[0]
    how_to_transpose = note_amounts_and_how_to_transpose[1]
    
    #Create a list for each instrument (per part) where his tones should be copied to (not in remix -> into remix) (if the in-remix instrument has too few tones)
    copy_list = create_copy_list(note_amounts,remix,melody_list[0])
    
    #Add Melody to the best fitting instruments
    if not dont_add_melody:
        for inml,mel in enumerate(melody_list[1]):
            transpose_melody = get_offset_for_moving_tones(mel,ranges[melody_list[0][inml]])
            
            for note in range(0,len(mel)):
                mel[note].velocity = 100
                mel[note].note += transpose_melody
                move_into(tracks,channels,averages,ranges,melody_list[0][inml],mel[note],may_move=False)
    
    alex = []
    for note in melody:
        alex.append(note.note)
    print (alex)
    
    
    #Remove tones from segments list
    x = 0
    bp_index = 0
    measure = 0
    while x < len(segments) and bp_index < len(remix):

        start_part = breakpoints[bp_index]
        if bp_index < len(breakpoints)-1:
            end_part = breakpoints[bp_index+1] 
        else:
            end_part = last_measure
        width_of_part = 0
        _x = x
        while measure < end_part:
            measure_width = get_measure_width_in_segments(_x, FileIO.ticks_per_beat/4)
            _x += int(measure_width)
            width_of_part += int(measure_width)
            measure += 1

        for y in range(0,width_of_part):
            #replace_who = []
            #
            ##Find instruments that are empty, although it's their turn
            #for z in range(0,len(instruments)):
            #    if z in remix[bp_index]:
            #        if len(segments[x+y][z]) == 0:
            #            replace_who.append(z)
            #replaced_by = []
            #for x in replace_who:
            #    replaced_by.append(-1)
            ##Find instruments that have notes, but it's not their turn
            #for z in range(0,len(instruments)):
            #    if not z in remix[bp_index] and not z in replace_who and segments[x+y][z] != 0:
            #        for inrw,a in enumerate(replace_who):
            #            if replaced_by[inrw] == -1: 
            #                replaced_by[inrw] = z
            #                continue
            #            if abs(averages[replaced_by[inrw]] - averages[a]) > abs(averages[z] - averages[a]): replaced_by[inrw] = z
           
            
            if x+y >= len(segments): break
            
            donor_index = 0
            donation_list = copy_list[bp_index]
            
            #Remove notes if they are not played in this part
            for z in range(0,len(instruments)):
                is_donor = False
                if not z in remix[bp_index] or melody_list[0][bp_index] == z:
                    is_donor = True
                if not z in remix[bp_index]:
                    #Check if they need to be instead moved to a playing instrument (that is empty)
                    #if z in replaced_by:
                    #    who = replace_who[replaced_by.index(z)]
                    #    print ("At segment "+str(x+y)+" I moved notes from "+str(z)+" to "+str(who))
                    #    for note in segments[x+y][z]:
                    #        move_into(tracks, channels, averages, ranges, who, note)
                    #        #tracks[z].remove(note)
                    #        #segments[x+y][z] = []
                    #else:
                                        
                    for note in range(0,len(segments[x+y][z])):
                        if is_donor and len(donation_list) > donor_index:
                            recipients = donation_list[donor_index]
                            for recipient in recipients:
                                segments[x+y][z][note].note += how_to_transpose[bp_index][z][recipient]
                                move_into(tracks, channels, averages, ranges, recipient, segments[x+y][z][note], may_move=False)
                                print ("I moved a note from "+str(z)+" to "+str(recipient)+" and changed the octave by "+str(how_to_transpose[bp_index][z][recipient]))
                            donor_index += 1
                            
                            #if len(recipients) == 0:
                            #    tracks[z].remove(segments[x+y][z][note])
                        #else:
                        tracks[z].remove(segments[x+y][z][note])
                    segments[x+y][z] = []
        
        bp_index += 1
        x += width_of_part
        

    return tracks

def get_offset_for_moving_tones(tones,my_range):
    _max = 0
    _min = math.inf
    for tone in tones:
        if tone.note > _max: _max = tone.note
        if tone.note < _min: _min = tone.note
    
    distance = _max - _min
    overlap =  min(_max, my_range[1]) - max(_min, my_range[0])
    if overlap >= distance:
        return 0
    diff = 0
    if _min > my_range[0]: #lower range
        done = False
        while done == False:    
            diff -= 12
            new_overlap =  min(_max+diff, my_range[1]) - max(_min+diff, my_range[0])
            if new_overlap <= overlap:
                diff += 12
                done = True
            overlap = new_overlap
    if _min < my_range[0]: #higher range
        done = False
        while done == False:    
            diff += 12
            new_overlap =  min(_max+diff, my_range[1]) - max(_min+diff, my_range[0])
            if new_overlap <= overlap:
                diff -= 12
                done = True
            overlap = new_overlap
    return diff
 
def create_copy_list(note_amounts,remix,melody_list):
    #print (len(remix))
    #print (len(note_amounts))
    #print (len(melody_list))
    output = []
    for inna,part in enumerate(note_amounts):
        recipients = [inin for inin,instr in enumerate(part) if inin in remix[inna] and inin != melody_list[inna]]
        donors = [inin for inin,instr in enumerate(part) if (not inin in remix[inna] or inin == melody_list[inna])]
        #print ("R+D:")
        #print (recipients)
        #print (donors)
        _copy_list = []
        
        #Add all recipient / donor pairs, if donor has 3 times or more tones
        for donor in donors:
            _donation_list = []
            for recipient in recipients:
                if part[donor] >= 3*part[recipient]: 
                    _donation_list.append(recipient)
            _copy_list.append(_donation_list)
        output.append(_copy_list)
    print (output)
    return output


def get_note_amounts(segments,breakpoints,instruments,last_measure,averages):
    amounts = []
    x = 0
    bp_index = 0
    measure = 0
    my_ranges = []
    while x < len(segments) and bp_index < len(breakpoints):
        _amount = []
        for z in range(0,len(instruments)): _amount.append(0)
        

        start_part = breakpoints[bp_index]
        if bp_index < len(breakpoints)-1:
            end_part = breakpoints[bp_index+1] 
        else:
            end_part = last_measure
        width_of_part = 0
        _x = x
        while measure < end_part:
            measure_width = get_measure_width_in_segments(_x, FileIO.ticks_per_beat/4)
            _x += int(measure_width)
            width_of_part += int(measure_width)
            measure += 1
        if x == 352 and y == 31:
            print ("")
        this_range = []
        for z in range(0,len(instruments)): this_range.append([math.inf,0])
        for y in range(0,width_of_part):
            if y+x >= len(segments): break
            _min = math.inf
            _max = 0
            for z in range(0,len(instruments)):
                for note in segments[x+y][z]:
                    if note.note < this_range[z][0]: this_range[z][0] = note.note
                    if note.note > this_range[z][1]: this_range[z][1] = note.note
                _amount[z] += len(segments[x+y][z])
        my_ranges.append(this_range)
        bp_index += 1
        x += width_of_part
        amounts.append(_amount)
    #print ("AMOUNTS:")
    #print (amounts)
    
    #clean up the ranges
    for part in my_ranges:
        for inrs,_range in enumerate(part):
            if _range[1] == 0: #no tones in this instrument / part
                _range[0] = averages[inrs]-10
                _range[1] = averages[inrs]+10
                
    
    #print (my_ranges)
    
    #Build array with values of how to transpose one instrument to another, for each part
    how_to_transpose = [] #Dimensions: 1. Part, 2. Source Instrument, 3. Target Instrument
    for part in my_ranges: 
        _part = []
        for instr1 in range(0,len(part)):
            _instr1 = []
            distance = part[instr1][1] - part[instr1][0]
            for instr2 in range(0,len(part)):
                #Same instrument
                if instr1 == instr2:
                    _instr1.append(0)
                    continue
            
                overlap =  min(part[instr1][1], part[instr2][1]) - max(part[instr1][0], part[instr2][0])
                #Full overlap
                if overlap >= distance: 
                    _instr1.append(0)
                    continue
                
                diff = 0
                if part[instr1][0] > part[instr2][0]: #lower range
                    done = False
                    while done == False:    
                        diff -= 12
                        new_overlap =  min(part[instr1][1]+diff, part[instr2][1]) - max(part[instr1][0]+diff, part[instr2][0])
                        if new_overlap <= overlap:
                            diff += 12
                            done = True
                        overlap = new_overlap
                if part[instr1][0] < part[instr2][0]: #higher range
                    done = False
                    while done == False:    
                        diff += 12
                        new_overlap =  min(part[instr1][1]+diff, part[instr2][1]) - max(part[instr1][0]+diff, part[instr2][0])
                        if new_overlap <= overlap:
                            diff -= 12
                            done = True
                        overlap = new_overlap
                
                _instr1.append(diff)
                        
                
            _part.append(_instr1)
        how_to_transpose.append(_part)
    #print (how_to_transpose)           
    return [amounts,how_to_transpose]



    
def get_remix(breakpoints,instruments,groups,averages):

    #Make list of instrument amounts - one amount for each part(here: segment) between breakpoints
    segments = []
    for x in range(0,len(breakpoints)-1): segments.append([])
    iii = len(instruments)
    sss = len(segments)
    segments_per_amount =   (iii-1) / sss  #Play at least 2 instruments always
    
    amounts = [2]
    amount = 2
    val = 0
    for x in range(0,sss):
        val_before = math.floor(val)
        val += segments_per_amount
        val_after = math.floor(val)
        amount_change = val_after - val_before
        amount = amount+amount_change
        amounts.append(amount)
    if amounts[-1] < iii:
        diff = iii - amounts[-1]
        amounts = [x+diff for x in amounts]
    if len(amounts) > 1 and amounts[-1] == amounts[-2]:
        amounts[-1] = 2
    _amounts = []
    #Mix it up a little bit
    for inam,a in enumerate(amounts):
        if inam == len(amounts)-1: 
            _amounts.append(a)
            break
        change1 = randint(0,1)
        change2 = randint(-1,1)
        if not (a + change1 * change2 <= 1) and not (a + change1 * change2 > iii):
            _amounts.append(a + change1 * change2)
        else:
            _amounts.append(a)
    amounts = _amounts
    
    
    in_groups = get_sorted_in_groups(groups,instruments,averages) #in_groups are sorted by average note (low to high)
    
    
    
    #Randomly select instruments for each amount
    instrument_selections = [] #index of 'instruments' list
    for amount in amounts:
        candidates = []
        #1.)Find a group that has exactly N instruments
        choices = [group for group in in_groups if len(group) == amount]
        which = 0
        if len(choices) > 1:
            which = randint(0,len(choices)-1)
        if len(choices) != 0:   
            candidates.append(choices[which])
                
            
        #2.) Find a group that has > N instruments, add one possibility (with highest tone included)
        choices = [group for group in in_groups if len(group) > amount]
        which = 0
        if len(choices) > 1:
            which = randint(0,len(choices)-1)
        if len(choices) != 0:        
            _candidate = []   
            _candidate.append(choices[which][-1])
            others = choices[which][0:len(choices[which])-1]    
            shuffle(others)
            _candidate.extend(others[0:amount-1])
            candidates.append(_candidate)
            
        #3.) Get a random selection of one tone per group, one has to be the highest of its group
       
        if len(in_groups) >= amount:
            #get highest tone
            _candidate = []
            highest_group = randint(0,len(in_groups)-1)
            _candidate.append( in_groups[highest_group][-1] )
            others = copy.copy(in_groups)
            del others[highest_group]
            shuffle(others)
            for group in others:
                if len(group) > 1:
                    _candidate.append(group[randint(0,len(group)-1)])
                else:
                    _candidate.append(group[0])
                if len(_candidate) == amount: break
            candidates.append(_candidate)
        #4.) N-1 from a group with at least N-1 instruments (avoid highest if possible) + 1 random highest tone
        others = [group for group in in_groups if len(group) >= amount-1]
        if len(others) != 0:
            shuffle(others)
            _candidate = copy.copy(others[0])
            while len(_candidate) > amount-1:
                del _candidate[randint(0,len(_candidate)-1)]
            
            rest = others[1:]
            rest.extend([group for group in in_groups if len(group) < amount-1])
            if len(rest) > 1: 
                which = randint(0,len(rest)-1)
            else: 
                which = 0
            if len(rest) > 0:
                if len(rest[which]) > 0: 
                    which2 = 0
                    if len(rest[which]) > 1:
                        which2 = randint(0,len(rest[which])-1)
                        
                    _candidate.append(rest[which][which2])
                    candidates.append(_candidate)
        
        #5.) Total mix, if empty so far
        if len(candidates) == 0:
            _candidate = []
            for group in in_groups:
                _candidate.extend(group)
            shuffle(_candidate)
            _candidate = _candidate[0:amount]
            candidates.append(_candidate)
            
            
        #print ("AMOUNT - "+str(amount)+":")
        #print (candidates)
        
        which = 0
        if len(candidates) > 1:
            which = randint(0,len(candidates)-1)
        instrument_selections.append(candidates[which])

        if FileIO.who_plays_melody != []:
            if [x for x in FileIO.who_plays_melody if x in instrument_selections[-1]] == []:
                #At least one melody instrument should be included
                if len(FileIO.who_plays_melody) == 1: 
                    instrument_selections[-1].append(FileIO.who_plays_melody[0])
                else:
                    instrument_selections[-1].append(FileIO.who_plays_melody[randint(0,len(FileIO.who_plays_melody)-1)]) 
                    instrument_selections[-1].sort()
    return instrument_selections
        
def get_sorted_in_groups(groups,instruments_list,averages):
    #list of instrument indices per group
    def get_key(item):
        return averages[item]
    
    in_groups = []
    for group in groups:
        _group = []
        for inil,instrument in enumerate(instruments_list):
            if instrument[0] in group: _group.append(inil)
        _group = sorted(_group,key=get_key)
        in_groups.append(_group)
    return in_groups

def get_melody_list(breakpoints,last_measure,remix,melody,averages,ranges):
    #returns a list with instruments + the melody separated by part
    melody_index = 0
    melody_parts = []
    averages_list = []
    fitting_instruments = []
    for inre,part in enumerate(remix):
        melody_list = []
        start_measure = breakpoints[inre]
        if inre+1 == len(breakpoints):
            end_measure = last_measure
        else:
            end_measure = breakpoints[inre+1]
        
        #index_start = index_of_measure(start_measure)
        index_end = index_of_measure(end_measure)
        sum = 0
        while  melody_index < len(melody) and melody[melody_index].index < index_end:
            melody_list.append(melody[melody_index])
            sum += melody[melody_index].note
            melody_index += 1 
        if len(melody_list) == 0:
            averages_list.append(0)
            fitting_instruments.append(0)
            continue
        average = sum / len(melody_list)
        averages_list.append(average)
        
        
    
        #Choose for each part of the remix the instrument that is best able to play the melody
        min = math.inf
        which = 0
        for instrument in part:
            if len(FileIO.who_plays_melody) != 0 and not instrument in FileIO.who_plays_melody: continue 
            if abs(averages[instrument] - average) < min:
                min = abs(averages[instrument] - average)
                which = instrument
        fitting_instruments.append(which)
        
        #Adjust the melody tones to fit the fitting instrument's range 
        note_list = []
        for note in melody_list:
            note_list.append(note.note)
        
        def amount_in_range(note_list,range,adjust=0):
            sum = 0
            for note in note_list:
                if note+adjust >= range[0] and note+adjust <= range[1]: sum += 1
            return sum
            
        best_fit = False
        
        diff = 0
        how_often = 0
        while best_fit == False and how_often <= 3:
            how_often += 1
            best_fit = True
            if amount_in_range(note_list, ranges[which], 12) > amount_in_range(note_list, ranges[which], 0):
                diff += 12
                best_fit = False
                
            if amount_in_range(note_list, ranges[which], -12) > amount_in_range(note_list, ranges[which], 0):
                diff -= 12
                best_fit = False
                
            note_list = [note+diff for note in note_list]
       
        
        if diff != 0:
            for note in melody_list:
                note.note += diff
        
        
        melody_parts.append(melody_list)
        
    return [fitting_instruments,melody_parts]
        
        
def index_of_measure ( measure ):
    last_beats = 4
    last_index = 0
    measures_passed = 0
    for bc in FileIO.beat_changes:
        if last_beats > 0:
            measures_passed += bc['increment'] / last_beats
 
        if measures_passed >= measure:
            break
            
        last_index = int(bc['index'])
        last_beats = int(bc['beats'])
    
    if measures_passed < measure:
        return last_index + (measure-measures_passed)*last_beats*FileIO.ticks_per_beat
    
    if measures_passed > measure:
        return last_index + (measures_passed-measure)*int(bc['beats'])*FileIO.ticks_per_beat
    if measures_passed == measure:
        return last_index
    
       # beat_index = index / FileIO.ticks_per_beat
       # measure = 0
       # last_beats = 4
       # for bc in FileIO.beat_changes:
       #
       #     if beat_index > bc['increment']:
       #         beat_index -= bc['increment']
       #         measure += bc['increment'] / last_beats
       #         last_beats = bc['beats']
       #     else:
       #         break
       #     
       # return (measure+int(beat_index/last_beats))
        
def move_into(tracks,channels,averages,ranges,where,event, may_move = True):
    #When copying a note, the index has to be in order in the new track

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
    if previous_note != event.note and may_move:
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

       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        