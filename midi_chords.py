from midi_split import *
import math

def create_chord_track(notes,style=0):
    #Styles: 0-normal,1-Pop,2-Jazz,3-Dance,4-Simple
    
    
     #Get amount of segments (each 1/16th note long)
    notes = copy.copy(Tools.combine_tracks(notes))
    final_index = notes[0][-1].index
    segments = int(math.ceil(final_index / (FileIO.ticks_per_beat/4) )) #beat/4 = 1/16th
    segment_size = FileIO.ticks_per_beat/4
    
    #Get all note values in segments
    all_segments = get_segment_data(notes, segments, segment_size,only_values=False, check_stt=True)
    
    #Get all keys including major/minor
    segment_keys = []
    segment_is_major = [] #List of booleans
    for x in range(0,len(all_segments)):
        segment_keys.append(0)
        segment_is_major.append(True)
    tones_list = []
    
    
    #The MIDI file contains maintained keys (but not major/minor distinction) -> Just find the positions
    segment_amounts = []
    if len(FileIO.key_changes) > 1 or (len(FileIO.key_changes) == 1 and FileIO.key_changes[0]['key'] != 0):
        
        last_index = 0
        for kc in FileIO.key_changes:
            if kc['index'] == 0: continue
            this_index = int(kc['index'] / segment_size)
            segment_amounts.append(this_index-last_index)
            last_index = this_index
        segment_amounts.append(len(all_segments) - last_index)    
    else:
        segment_amounts.append(len(all_segments))
    
    #Using the Krumhansl Algorithm
    last_end = 0
    major_profile = [6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]
    minor_profile = [6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17]
    for part in segment_amounts:
        #For each part find the note durations (simply use MIDI ticks, only relative length matters)
        durations = []
        for x in range(0,12): durations.append(0)
        for x in range(last_end,last_end+part):
            segment = all_segments[x]
            for track in segment:
                for note in track:
                    durations[note.note%12] += note.duration
        
        #Test the part for all 24 possible keys
        max = 0
        is_major = True
        key = 0
        for x in range (0,11):
            val = corr(durations,major_profile)
            
            if val > max:
                max = val
                is_major = True
                key = x
            
            val = corr(durations,minor_profile)
            
            if val > max:
                max = val
                is_major = False
                key = x
            durations.append(durations[0])
            del durations[0]
        
        
        
        for x in range(last_end,last_end+part):
            segment_keys[x] = key
            segment_is_major[x] = is_major
            
        last_end = last_end+part


   
    find_distance = True
    collected_segments = []
    begin_of_collection = 0
    
    output = []
    
    for inas,segment in enumerate(all_segments):
        if find_distance:
            collected_segments = []
            begin_of_collection = inas
            measure_width = get_measure_width_in_segments(inas,segment_size)
        
            #Place a chord every half measure
            chord_distance = measure_width/2
            
            find_distance = False
            
        collected_segments.append(segment[0])
        if len(collected_segments) >= chord_distance:
            collected_segments = [item for sublist in collected_segments for item in sublist] #Flatten list
            if collected_segments != []:
                chord_info = find_chord(collected_segments,segment_keys[begin_of_collection],segment_is_major[begin_of_collection],style)
                for x in range(0,int(chord_distance)):
                    output.append(chord_info)
                #print (chord_info)
                #new_val = Event(type='note',msg=Message('note_on'),index=begin_of_collection*segment_size, duration=chord_distance*segment_size,note=36+chord_info[1], octave = int((36+chord_info[1]) / 12),channel = 15, velocity = 100)
                #output_track.append(new_val)    
                #for tone in chord_info[0]:
                #    new_val = Event(type='note',msg=Message('note_on'),index=begin_of_collection*segment_size,duration=chord_distance*segment_size, note=48+tone, octave = int((36+chord_info[1]) / 12),channel = 15, velocity = 100)
                #    output_track.append(new_val)    
            else:
                for x in range(0,int(chord_distance)):
                    output.append([[],-1,'x'])
            
            find_distance = True
    
   
    
    return output


def find_chord(notes,key,is_major,style):
    #Check which of all 12 possible chords has the most tones in common - Create Sum of fitting tones
    #Add to sum 1.5, for every base tone (CCDEFFGA -> C-E-G = 3+1+1, D-F-A = 1.5+2+1)

    #Styles: 0-normal,1-Pop,2-Jazz,3-Dance,4-Simple

    #C0,C#,D2,D#,E4,F5,F#,G7,G#,A9,A#,B11
    chords = []
    chord_ending = []
    tones = []
    for note in notes:
        tones.append(note.note % 12)
    style=0
    
    #Normal
    if style == 0:
        if is_major: 
            chords=[[0,4,7],[1,4,7],[2,5,9],[3,7,10],[4,7,11],[5,9,0],[6,9,0],[7,11,2,5],[8,11,2],[9,0,4],[10,2,5],[11,2,7]]
            chord_ending=['','dim','m','','m','','dim','7','dim','m','','x']
        if not is_major: 
            chords=[[0,4,7],[1,4,7],[2,5,9],[3,6,9,0],[4,8,11,2],[5,9,0],[6,9,0],[7,11,2,5],[8,11,2,4],[9,0,4],[10,2,5],[11,2,5,9]]    
            chord_ending=['','dim','m','dim7','7','','dim','7','y','m','','m7b5']
    #Pop
    if style == 1:
        if is_major: 
            chords=[[0,4,7,2],[1,4,7,10],[2,5,9,0],[3,6,9,0],[4,7,11,2],[5,9,0,4],[6,9,0],[7,11,2,5],[8,11,2],[9,0,4,7],[10,2,5],[11,2,7]]
            chord_ending=['add9','dim7','m7','dim7','m7','M7','dim','7','dim','m7','','x']
        if not is_major: 
            chords=[[0,4,7],[1,4,7,10],[2,5,9,0],[3,6,9,0],[4,8,11,2],[5,9,0,4],[6,9,0],[7,11,2,5],[8,11,2,4],[9,0,4,7],[10,2,5],[11,2,7]]
            chord_ending=['','dim7','m7','dim7','7','M7','dim','7','y','m7','','x']
    #Jazz
    if style == 2:
        if is_major: 
            chords=[[0,4,7,11,2],[1,4,7,11],[2,5,9,0,4],[3,6,9,0],[4,7,11,2],[5,9,0,2,7],[6,9,0,3],[7,11,2,5,9],[8,11,2],[9,0,4,7,2],[10,2,5,8],[11,2,5,9]]
            chord_ending=['M7/9','dim7','m7/9','dim7','m7','6/9','dim7','7/9','dim','m7/11','7','m7b5']
        if not is_major: 
            chords=[[0,4,7,11,2],[1,4,7,11],[2,5,9,0,4],[3,6,9,0],[4,8,11,2],[5,9,0,4,7],[6,9,0,4],[7,11,2,5,9],[8,0,3,6],[9,0,4,7,11],[10,2,5,8],[11,2,5,9]]
            chord_ending=['M7/9','dim7','m7/9','dim7','7','M7/9','m7b5','7/9','7','add9','7','m7b5']
    #Dance
    if style == 3:
        if is_major: 
            chords=[[0,4,7],[1,4,7],[2,5,9],[3,7,10],[4,7,11],[5,9,0],[6,9,0],[7,11,2],[8,11,2],[9,0,4],[10,2,5],[11,2,7]]
            chord_ending=['','dim','m','','m','','dim','','dim','m','','x']
        if not is_major: 
            chords=[[0,3,7],[1,4,8],[2,5,9],[3,6,10],[4,7,11],[5,8,0],[6,9,1],[7,10,2],[8,0,3],[9,0,4],[10,2,5],[11,2,6]]
            chord_ending=['m','m','m','m','m','m','m','m','','m','','m']
    #Simple
    if style == 4:
        if is_major: 
            chords=[[0,4,7],[1,4,7],[2,5,9],[3,7,10],[4,11],[5,0],[6,9,0],[7,11,2,5],[8,11,2],[9,0,4],[10,2,5],[11,2,7]]
            chord_ending=['','dim','m','','5','5','dim','7','dim','m','','x']
        if not is_major: 
            chords=[[0,4,7],[1,4,7],[2,5,9],[3,6,9,0],[4,11],[5,9,0],[6,9,0],[7,11,2,5],[8,11,2,4],[9,0,4],[10,2,5],[11,2,5,9]]
            chord_ending=['','dim','m','dim7','5','','dim','7','y','m','','m7b5']
    #Adjust chords to fit key
    for inch,chord in enumerate(chords):
        for inch2,tone in enumerate(chord):
            if is_major: chords[inch][inch2] = (tone+key)%12
            if not is_major: chords[inch][inch2]  = (tone+key+3)%12 #The chords are listed for C-Major and A-Minor
    
    scores = []
    
    for chord in chords:
        score = 0
        weight = 1
        for tone in tones:
            weight -= 1/len(tones)
            if tone in chord:
                if chord[0] == tone: 
                    score += 2 * weight
                else:
                    score += 1.0 * weight
                
        scores.append(score)
    
    
    #print (tones)
    #print (scores)
    index_of_highest = max(range(len(scores)), key=scores.__getitem__) 
    
    #Check how many tones the best fit did NOT find in the tones list
    best_chord = chords[index_of_highest]
    not_fit = len(best_chord)
    for chord_tone in best_chord:
        if chord_tone in tones: not_fit -= 1 
    
    #If not fitting tones > 0, try if any non-standard chord is a good fit
    scores_major_minor = []
    dominant_score = 0
    if not_fit >= 1:
        major = [0,4,7]
        minor = [0,3,7]
        #dominant = [(key+11)%12,(key+5)%12] #check for dominant feeling (e.g. G7, in key C)        
        #
        #
        #for tone in tones:
        #    if tone in dominant:
        #        dominant_score += 1
        #    else:
        #        dominant_score -= 0.5
        
        for x in range(0,12):
            score_maj = 0; score_min = 0
            for tone in tones:
                if tone in major: score_maj += 1
                if tone in minor: score_min += 1
                if tone not in major: score_maj -= 0.5
                if tone not in minor: score_min -= 0.5
            scores_major_minor.append(score_maj)
            scores_major_minor.append(score_min)
                
            
            major[0] = (major[0]+1)%12;major[1] = (major[1]+1)%12;major[2] = (major[2]+1)%12
            minor[0] = (minor[0]+1)%12;minor[1] = (minor[1]+1)%12;minor[2] = (minor[2]+1)%12
        
            
            
        #print (scores_major_minor)
        #print (dominant_score)

    adjust = 0
    if is_major: adjust = key
    if not is_major: adjust = key+3
    
    tones_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    chord_base = tones_names[(index_of_highest+adjust)%12]
    
    if chord_ending[index_of_highest] == 'x': #e.g. B -> G/B
        chord_ending[index_of_highest] = ""
        chord_base = tones_names[(index_of_highest+adjust+8)%12] + "/" + chord_base
    if chord_ending[index_of_highest] == 'y': #e.g. G# -> G#/E7
        chord_ending[index_of_highest] = "/" + tones_names[(index_of_highest+adjust+8)%12]+"7"
        
    final_chord = chords[index_of_highest]
    base_tone = (index_of_highest+adjust)%12
    chord_name = chord_base+chord_ending[index_of_highest]
   
    #print ("BEFORE: ["+str(final_chord)+","+str(base_tone)+","+chord_name+"]")
   
    #If there is one unique maximum with alternative chords - use this chord instead
    if not_fit >= 1:
        max_val = max(scores_major_minor)
        if dominant_score > max_val: #Found a dominant chord
            base_tone = key
            chord_name = tones_names[(7+base_tone)%12]+"7"
            final_chord=[(7+key)%12,(11+key)%12,(14+key)%12,(17+key)%12]
        else:
            amount = scores_major_minor.count(max_val)
            if amount == 1:
                index_max = max(range(len(scores_major_minor)), key=scores_major_minor.__getitem__)
                key = math.floor(index_max / 2)
                base_tone = key
                chord_name = tones_names[base_tone]
                if index_max % 2 == 0: #Major
                    final_chord = [key,(4+key)%12,(7+key)%12]
                if index_max % 2 == 1: #Minor
                    final_chord = [key,(3+key)%12,(7+key)%12]
                    chord_name += "m"
            
        
   
    return [final_chord,base_tone,chord_name]

def get_scale_from_distribution(tones_list):
    scales = [[1,0,1,0,1,1,0,1,0,1,0,1],#C / am
              [1,1,0,1,0,1,1,0,1,0,1,0],
              [0,1,1,0,1,0,1,1,0,1,0,1],#D
              [1,0,1,1,0,1,0,1,1,0,1,0],
              [0,1,0,1,1,0,1,0,1,1,0,1],#E
              [1,0,1,0,1,1,0,1,0,1,1,0],#F
              [0,1,0,1,0,1,1,0,1,0,1,1],
              [1,0,1,0,1,0,1,1,0,1,0,1],#G
              [1,1,0,1,0,1,0,1,1,0,1,0],
              [0,1,1,0,1,0,1,0,1,1,0,1],#A
              [1,0,1,1,0,1,0,1,0,1,1,0],
              [0,1,0,1,1,0,1,0,1,0,1,1]]#H
    max = 0
    ret_val = 0
    for insc,scale in enumerate(scales):
        sum = 0
        for x in range(0,12):
            sum += tones_list[x] * scale[x]
        if sum > max:
            max = sum
            ret_val = insc
       
    return ret_val 
            
        


def get_measure_width_in_segments(segment, segment_size):
    index_of_segment = segment * segment_size
    
    beats = 4
    for bc in FileIO.beat_changes:
        if bc['index'] <= index_of_segment:
            beats = bc['beats']
        else: break
    return beats*4

def corr(list1,list2):
    #Returns the correlation coefficient between two lists
    size = min(len(list1),len(list2))
    
    avg1 = math.fsum(list1)/len(list1)
    avg2 = math.fsum(list2)/len(list2)
    sum_top = 0
    sum_bottom_left = 0
    sum_bottom_right = 0
    for x in range(0,size):
        sum_top += (list1[x]-avg1)*(list2[x]-avg2)
        sum_bottom_left += (list1[x]-avg1)*(list1[x]-avg1)
        sum_bottom_right += (list2[x]-avg2)*(list2[x]-avg2)
    bottom = sum_bottom_left * sum_bottom_right
    
    return sum_top / math.sqrt(bottom)
        
    
    
    