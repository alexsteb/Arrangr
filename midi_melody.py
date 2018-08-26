import copy
from midi_tools import Tools
#Separates the melody from the original file
#def separate_melody(notes,where):
#    #if where > 0: #Melody is a specific track
#    print (len(notes))   
#    return notes

def separate_melody (notes,where):
    _notes = copy.copy(notes)
    
    if where > 0: #Melody is a specific track -> switch it to the beginning and return
        if where > 1:
            notes[0],notes[where-1] = notes[where-1],notes[0]
        
        return notes
    
    
    track = Tools.combine_tracks(copy.copy(_notes))[0]

    melody = []
    this_index = []
    ci = 0
    note_end = 0
    last_height = 0
    total_notes_height = 0
    total_notes_amount = 0
    for note in track:
        if note.index > ci:
            tones_list = []
            for _note in this_index:
                if _note.type != 'event':
                    tones_list.append(_note)
            max_val = 0
            max_note = None
            for _note in tones_list:
                if _note.note > max_val:
                    max_val = _note.note
                    max_note = _note
                    total_notes_height += max_val
                    total_notes_amount += 1
                    
            if max_note != None and (note_end < (max_note.index+max_note.duration) or (note_end >= (max_note.index+max_note.duration) and last_height < max_val)):
                melody.append(max_note)
            if max_note != None:
                note_end = max_note.index + max_note.duration
                last_height = max_val
            
            ci = note.index
            this_index = []
        this_index.append(note)
    
    #Remove tones that don't fit the melody
    avg = total_notes_height / total_notes_amount
    print ("Average:")
    print (avg)
    new_melody = []
    first_good_tone = 0
    current_pos = 0
    for inme,_note in enumerate(melody):
        if _note.note > avg-12 and _note.note < avg+12:
            first_good_tone = inme
            current_pos = _note.note
            break
    
    for x in range (first_good_tone-1,-1,-1):
        if melody[x].note > current_pos -12 and melody[x].note < current_pos +12:
            current_pos = melody[x].note
            first_good_tone = x
        else:
            break
    print (first_good_tone)
    print (melody[first_good_tone].__dict__)
    skipped = False
    last_pos = 0
    for x in range(first_good_tone,len(melody)):
        if (melody[x].note > current_pos - 12):
            new_melody.append(melody[x])
            current_pos = melody[x].note
            if skipped:
                _current = current_pos
                insert_pos = len(new_melody)-1
                for y in range (x-1,-1,-1):
                    if y == last_pos: break
                    if melody[y].note > _current - 12 and melody[y].note < _current + 12:
                        _current = melody[y].note
                        new_melody.insert(insert_pos,melody[y])
                    else:
                        break
                skipped = False
            last_pos = x
        else:
            skipped = True
    # new_melody = melody
    
    output = []
    #melody =  [x for x in melody if not x == None] 
    output.append(copy.copy(new_melody))
    for tr in _notes:
        tr =  [x for x in tr if not (x in new_melody)] 
        output.append(copy.copy(tr))
    return output  