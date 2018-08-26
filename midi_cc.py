from midi_combine import *
from midi_split import *
from midi_melody import *
from midi_chords import *
from midi_brain_guitar import Create_Guitar
import copy
from midi_IO import FileIO 


#This function takes the instrument information collected by the GUI
#and organizes the Midi creation using the different arranger classes
def arrange_midi(notes,instruments_list, settings_list):
    #GM-Number, bool:treat as ensemble instrument,maximum stt, bool:create arpeggios, [range_low,range_high],[combining_group],(guitar settings:) [patch,strings,[base tones top-down],highest fret,hand-with,same time tones] -> Empty if not applicable
    print (instruments_list)
    #int:where_is_melody, bool:create_chords
    print (settings_list)
    
    #Ignore unused / not imported tracks
    _notes = []
    for inno,track in enumerate(notes):
        if inno in FileIO.imported_tracks:
            _notes.append(copy.copy(track))
    notes = _notes
    
    #-1.) separate 0-track and add back later
    zero_track = copy.copy(notes[0])
    notes = notes[1:]
    old_notes = notes #Before removing melody
    
    #0.) Create additional chord list (if selected)
    chords = []
    if settings_list[1]: chords = create_chord_track(notes,style=0)
    
    #1.) Find melody and separate it from the rest
    melody_and_rest = separate_melody(notes,settings_list[0]) #Melody | Track 1 ... Settings Track rausfiltern
    melody = melody_and_rest[0]
    alex = []
    for note in melody:
        alex.append(note.note)
    print (alex)
    
    if len(melody_and_rest) >= 2:
        amount_non_melody = 0
        for x in range(1,len(melody_and_rest)):
            amount_non_melody += sum(1 for y in melody_and_rest[x] if y.type == 'note')
        amount_melody = sum(1 for y in melody if y.type == 'note')
        div = 1
        if amount_melody != 0:
            div = (amount_non_melody/amount_melody)
        if div <= 0.1:
             notes = [copy.copy(melody)] #Almost only melody -> give melody to the other voices.
             ###!!!Change this for if there is a chord track demanded (then we don't need to give the melody) 
        else:
            notes = melody_and_rest[1:]
    else:
        notes = [copy.copy(melody)] #Midi consists only of a melody

    #Weg?
    #notes.append(chord_track)
   
    
    tab_list = [] #Collect all guitar tabs
    
    #2.) Process all non-ensemble instruments:
    non_ensemble_tracks = []
    for instrument in instruments_list:
        if instrument[1] == False: #non-ensemble
            _notes = []
            for inno,track in enumerate(old_notes):
                if inno in instrument[5]:
                    _notes.append(copy.copy(track)) #Notes of particular combining group
            _notes_one = Tools.combine_tracks(_notes)
            _track = split_music(notes=_notes_one,melody=melody,chords=chords,instruments_list=[instrument],dont_add_melody=True)[0]
            if instrument[6] != []:
                tab_list.append(Create_Guitar.tabs)
            
                #combine_music(notes=_notes_one,instrument=instrument[0],arpeggio=instrument[3],stt=instrument[2])
            #else: #Guitar Instrument
            #    _track = Create_Guitar.combine_guitar_music(notes=_notes_one,instrument=instrument[0],guitar_settings=instrument[6])
            non_ensemble_tracks.append(_track)
     
    #Create sub-instruments_list consisting of only ensemble instruments
    ensemble_instrument_list = []
    for instrument in instruments_list:
        if instrument[1] == True: #ensemble
            ensemble_instrument_list.append(instrument)       
    #3.) Process all ensemble instruments and add melody:
    split_tracks = split_music(notes=notes,melody=melody,chords=chords,instruments_list=ensemble_instrument_list) #returns list (only) of the ensemble instruments
    
    print (len(split_tracks))
    
    #4.) Combine the split tracks
    ensemble_tracks = []
    for inst,track in enumerate(split_tracks):
        _track_list = []
        _track_list.append(track)
        
       # if ensemble_instrument_list[inst][6] == []:
        ensemble_tracks.append(track)#combine_music(notes=_track_list,instrument=ensemble_instrument_list[inst][0],arpeggio = ensemble_instrument_list[inst][3],stt=ensemble_instrument_list[inst][2]))
        if ensemble_instrument_list[inst][6] != []: #Guitar Instrument
            #ensemble_tracks.append(Create_Guitar.combine_guitar_music(notes=_track_list,instrument=ensemble_instrument_list[inst][0],guitar_settings=ensemble_instrument_list[inst][6]))
            tab_list.append(Create_Guitar.tabs)
    
    #5.) Prepare return list
    index_en = 0
    index_non = 0
    output = []
    output.append(zero_track)

    #output.append(melody)
    
    for instrument in instruments_list:
        if instrument[1] == True: #ensemble
            output.append(ensemble_tracks[index_en])
            index_en+=1
        else:
            output.append(non_ensemble_tracks[index_non])
            index_non+=1
    
    FileIO.guitar_tab_list = copy.copy(tab_list)
    
    return output
    
    
    
    
    
    
    
 
    