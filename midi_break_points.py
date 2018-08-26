from midi_IO import FileIO
from pydub.effects import low_pass_filter
from random import randint
#

def get_big_break_points(notes):
    segment_size = FileIO.ticks_per_beat/4
    segments = get_simple_segments(notes,segment_size)
    
    
    x = 0
    scores = []
    while x < len(segments):
        measure_width = get_measure_width_in_segments(x, segment_size)
        
        score = calculate_score(segments[x:x+int(measure_width)])
        scores.append(score)    
        x += int(measure_width)
    
    break_points = [] #starting measures
    
    last_score = 0
    for insc,score in enumerate(scores):
        #Test if bigger
        if score > last_score:
            if (score-last_score)/(last_score+0.001) >= 0.25:
                #Considerably bigger
                break_points.append(insc)
        elif score < last_score:
            if insc < len(scores)-1:
                if scores[insc+1] == score: break_points.append(insc)
        
        
        last_score = score   

    final = []
    for inbp,bp in enumerate(break_points):
        if inbp > 0:
            if bp - break_points[inbp-1] != 1:
                final.append(bp)
        else:
            final.append(bp)
    final.append(len(scores))
    return final

def get_small_break_points(big):
    output = []
    for inbi,bp in enumerate(big):
        if inbi == 0: continue
        low = big[inbi-1]
        distance = bp - low
        if distance <= 5: continue #length of < 6 is big enough
        
        parts = int(round(distance / 3.5))
        parts_arr = []
        for x in range(0,parts):
            parts_arr.append(3)
        while sum(parts_arr) < distance:
            where = randint(0,len(parts_arr)-1)
            parts_arr[where] += 1
        
        index = low
        for inpa,p in enumerate(parts_arr):
            if inpa == len(parts_arr)-1: break
            index += p
            output.append(index)
    return output    
        
def calculate_score(segments):
    score = 0
    for inse,segment in enumerate(segments):
        if len(segment) > 0:
            if inse % 2 == 0:
                score += 1
            else:
                score += 0.5
            score += (len(segments)-inse)/len(segments)
    return score 

def get_simple_segments(tracks,segment_size):
    #Does not distinguish for instruments
    segments = []
    
    current_start = 0
    current_end = segment_size
    segment = []
    for track in tracks:
        for note in track:
            if note.type == 'event': continue
            while note.index >= current_end:
                current_start = current_end
                current_end = current_start + segment_size
                segments.append(segment)
                segment = []
            
            segment.append(note)
    return segments
      
def get_measure_width_in_segments(segment, segment_size):
    index_of_segment = segment * segment_size
    
    beats = 4
    for bc in FileIO.beat_changes:
        if bc['index'] <= index_of_segment:
            beats = bc['beats']
        else: break
    return beats*4 