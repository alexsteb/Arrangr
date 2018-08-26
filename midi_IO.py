from mido import MidiFile
from mido import Message
from mido import MidiTrack
#import guitarpro
import copy
import math



class FileIO:
    midi_file = None
    guitar_tab_list = []
    tempo_message = None #Because of bad programming  @Mido
    tonem = 60
    ticks_per_beat = 960
    beat_changes = [] #List of whenever the beat (e.g. 3/4) changes
    tempo_changes = []
    key_changes = []
    track_names = [] #Including empty track 0
    instruments = []
    instrument_channels = []
    notes_amounts = []
    ranges = []
    ranges_name = []
    who_plays_melody = []

    imported_tracks = []

    ###################################################
    #Common global Variables: (As good a place as any)#
    ##################################################

    #Preferred speeds per instrument in 32nds ([average speed in ensemble, fastest possible (e.g. in a solo)]) (smaller = faster)                                                                                                                                               #40                                                                                                                          60                                                                                                                            80
    preferred_speeds = [[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [4,3],[1,1],[5,3],[5,3],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [5,3],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[4,3],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,0.2],[1,0.2],[1,0.2],[1,0.2],[1,0.2],[1,0.2],[1,0.2],[1,0.2],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],  [1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[1,1]]
    #GM Patches not supported in this program
    not_supported = [32,97,98,99,100,101,102,103,104,113,114,116,117,118,119,120,121,122,123,124,125,126,127,128]
    #All the common names of the GM instruments (0-127)
    GM_names = ["Acoustic Grand Piano","Bright Acoustic Piano","Electric Grand Piano","Honky-tonk Piano","Electric Piano 1","Electric Piano 2","Harpsichord","Clavinet","Celesta","Glockenspiel","Music Box","Vibraphone","Marimba","Xylophone","Tubular Bells","Dulcimer","Drawbar Organ","Percussive Organ","Rock Organ","Church Organ","Reed Organ","Accordion","Harmonica","Tango Accordion","Acoustic Guitar (nylon)","Acoustic Guitar (steel)","Electric Guitar (jazz)","Electric Guitar (clean)","Electric Guitar (muted)","Overdriven Guitar","Distortion Guitar","Guitar Harmonics","Acoustic Bass","Electric Bass (finger)","Electric Bass (pick)","Fretless Bass","Slap Bass 1","Slap Bass 2","Synth Bass 1","Synth Bass 2","Violin","Viola","Cello","Contrabass","Tremolo Strings","Pizzicato Strings","Orchestral Harp","Timpani","String Ensemble 1","String Ensemble 2","Synth Strings 1","Synth Strings 2","Choir Aahs","Voice Oohs","Synth Voice","Orchestra Hit","Trumpet","Trombone","Tuba","Muted Trumpet","French Horn","Brass Section","SynthBrass 1","SynthBrass 2","Soprano Sax","Alto Sax","Tenor Sax","Baritone Sax","Oboe","English Horn","Bassoon","Clarinet","Piccolo","Flute","Recorder","Pan Flute","Blown Bottle","Shakuhachi","Whistle","Ocarina","Lead 1 (Square)","Lead 2 (Sawtooth)","Lead 3 (Calliope)","Lead 4 (Chiff)","Lead 5 (Charang)","Lead 6 (Voice)","Lead 7 (Fifths)","Lead 8 (Bass + Lead)","Pad 1 (New Age)","Pad 2 (Warm)","Pad 3 (Polysynth)","Pad 4 (Choir)","Pad 5 (Bowed)","Pad 6 (Metallic)","Pad 7 (Halo)","Pad 8 (Sweep)","FX 1 (Rain)","FX 2 (Soundtrack)","FX 3 (Crystal)","FX4(Atmosphere)","FX 5 (Brightness)","FX 6 (Goblins)","FX 7 (Echoes)","FX 8 (Sci-fi)","Sitar","Banjo","Shamisen","Koto","Kalimba","Bag Pipe","Fiddle","Shanai","Tinkle Bell","Agogo","Steel Drums","Woodblock","Taiko Drum","Melodic Tom","Synth Drum","Reverse Cymbal","Guitar Fret Noise","Breath Noise","Seashore","Bird Tweet","Telephone Ring","Helicopter","Applause","Gunshot"]
    ACOUSTIC_GRAND_PIANO=0; BRIGHT_ACOUSTIC_PIANO=1; ELECTRIC_GRAND_PIANO=2; HONKY_TONK_PIANO=3; ELECTRICPIANO_1=4; ELECTRIC_PIANO_2=5; HARPSICHORD=6; CLAVINET=7; CELESTA=8; GLOCKENSPIEL=9; MUSIC_BOX=10; VIBRAPHONE=11; MARIMBA=12; XYLOPHONE=13; TUBULAR_BELLS=14; DULCIMER=15; DRAWBAR_ORGAN=16; PERCUSSIVEORGAN=17; ROCK_ORGAN=18; CHURCH_ORGAN=19; REED_ORGAN=20; ACCORDION=21; HARMONICA=22; TANGOACCORDION=23; ACOUSTIC_GUITAR_NYLON=24; ACOUSTIC_GUITAR_STEEL=25; ELECTRIC_GUITAR_JAZZ=26; ELECTRIC_GUITAR_CLEAN=27; ELECTRIC_GUITAR_MUTED=28; OVERDRIVENGUITAR=29; DISTORTION_GUITAR=30; GUITAR_HARMONICS=31; ACOUSTIC_BASS=32; ELECTRIC_BASSFINGER=33; ELECTRIC_BASS_PICK=34; FRETLESS_BASS=35; SLAP_BASS_1=36; SLAP_BASS_2=37; SYNTH_BASS_1=38; SYNTH_BASS_2=39; VIOLIN=40; VIOLA=41; CELLO=42; CONTRABASS=43; TREMOLO_STRINGS=44; PIZZICATO_STRINGS=45; ORCHESTRAL_HARP=46; TIMPANI=47; STRING_ENSEMBLE_1=48; STRING_ENSEMBLE_2=49; SYNTH_STRINGS_1=50; SYNTH_STRINGS_2=51; CHOIR_AAHS=52; VOICE_OOHS=53; SYNTH_VOICE=54; ORCHESTRA_HIT=55; TRUMPET=56; TROMBONE=57; TUBA=58; MUTED_TRUMPET=59; FRENCH_HORN=60; BRASS_SECTION=61; SYNTHBRASS_1=62; SYNTHBRASS_2=63; SOPRANO_SAX=64; ALTO_SAX=65; TENOR_SAX=66; BARITONE_SAX=67; OBOE=68; ENGLISH_HORN=69; BASSOON=70; CLARINET=71; PICCOLO=72; FLUTE=73; RECORDER=74; PAN_FLUTE=75; BLOWN_BOTTLE=76; SHAKUHACHI=77; WHISTLE=78; OCARINA=79; LEAD_1_SQUARE=80; LEAD_2_SAWTOOTH=81; LEAD_3_CALLIOPE=82; LEAD_4_CHIFF=83; LEAD_5_CHARANG=84; LEAD_6_VOICE=85; LEAD_7_FIFTHS=86; LEAD_8_BASS_LEAD=87; PAD_1_NEW_AGE=88; PAD_2_WARM=89; PAD_3_POLYSYNTH=90; PAD_4_CHOIR=91; PAD_5_BOWED=92; PAD_6_METALLIC=93; PAD_7_HALO=94; PAD_8_SWEEP=95; FX_1_RAIN=96; FX_2_SOUNDTRACK=97; FX_3_CRYSTAL=98; FX_4_ATMOSPHERE=99; FX_5_BRIGHTNESS=100; FX_6_GOBLINS=101; FX_7_ECHOES=102; FX_8_SCI_FI=103; SITAR=104; BANJO=105; SHAMISEN=106; KOTO=107; KALIMBA=108; BAG_PIPE=109; FIDDLE=110; SHANAI=111; TINKLE_BELL=112; AGOGO=113; STEEL_DRUMS=114; WOODBLOCK=115; TAIKO_DRUM=116; MELODIC_TOM=117; SYNTH_DRUM=118; REVERSE_CYMBAL=119; GUITAR_FRET_NOISE=120; BREATH_NOISE=121; SEASHORE=122; BIRD_TWEET=123; TELEPHONE_RING=124; HELICOPTER=125; APPLAUSE=126; GUNSHOT=127
    GM_types = ["Keyboard Instrument","Keyboard Instrument","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""]
    GM_Ranges_Possible = [[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108],[21,108]]
    #GM_Grouped_With = [["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"]]
    #GM_Replaces = [["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"],["-"]]
    GM_Description = ["Simple horizontal chordophone with keyboard sounded by hammers.","Upright chordophone with keyboard sounded by hammers. Narrower sound than the Grand Piano.","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-"]
    new_time_index = 0.0
    #             Strings
    GM_groups = [[40,41,42,43]]
    def get_grouped_with(instrument):
        #returns a text in the form "Viola, Cello, and Contrabass"
        text_list = []
        for group in FileIO.GM_groups:
            if instrument in group:
                for member in group:
                    if member != instrument:
                        text_list.append(FileIO.GM_names[member])
        text=""
        for x in range(0,len(text_list)):
            text += text_list[x]
            if x < len(text_list)-1: text += ", "
            if x == len(text_list)-2: text += "and "

        if text == "": text = "-"
        return text

    #First value is the instrument, other values are the instruments it can replace (only values in groups)
    #                    tremolo           pizzicato
    GM_replace_groups = [[44,40,41,42,43],[45,40,41,42,43]]
    def get_replaces(instrument):
        text_list = []
        for group in FileIO.GM_replace_groups:
            if instrument == group[0]:
                for x in range(1,len(group)):
                    text_list.append(FileIO.GM_names[group[x]])
        text = ""
        for x in range(0,len(text_list)):
            text += text_list[x]
            if x < len(text_list)-1: text += ", "
            if x == len(text_list)-2: text += "and "

        if text == "": text = "-"
        return text


    def get_name(tone):
        tones = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

        note = tones[tone % 12]
        octave = int(tone/12) - 1
        return note+str(octave)

    def create_midi_slice(self,tracks,time_index=0,start_at_beginning=False):
        #print (time_index)
        def time_to_index(time):
            _index = 0
            last_time_index = 0.0
            last_tempo = FileIO.tempo_changes[0]['tempo']
            for tc in FileIO.tempo_changes:
                if tc['time_index'] >= time: break
                _index = tc['index']
                last_time_index = tc['time_index']
                last_tempo = tc['tempo']
            rest_time = time-last_time_index #tc['time_index']
            _index += (last_tempo*rest_time/60)*FileIO.ticks_per_beat
            #index*60/tpb/tempo = time
            return max(0,int(_index-FileIO.ticks_per_beat/8))##

        def index_to_time(index):
            _time = 0.0
            last_index = 0
            last_tempo = FileIO.tempo_changes[0]['tempo']
            for tc in FileIO.tempo_changes:
                if tc['index'] >= index: break
                _time = tc['time_index']
                last_index = tc['index']
                last_tempo = tc['tempo']
            rest_index = index-last_index
            _time += (rest_index/FileIO.ticks_per_beat)*60/last_tempo
            return max(0,_time)

        if not start_at_beginning:
            from_index = time_to_index(time_index)



        mid = copy.copy(FileIO.midi_file)
        if not 0 in tracks: tracks.insert(0,0)

        #Find the first note_on-event
        if start_at_beginning:
            from_index = math.inf
            first_note_on = 0
            for i,track in enumerate(copy.copy(mid.tracks)):

                if not i in tracks: continue
                if i==0: continue
                index = 0
                for pos,msg in enumerate(track):
                    if msg.type == 'note_on':
                        if  index < from_index: from_index = index+msg.time
                        break
                    index += msg.time
            if from_index == math.inf:
                cut_index = 0
            FileIO.new_time_index = index_to_time(from_index)
            #print ("From Index: "+str(from_index))
            #print ("NTI: "+str(FileIO.new_time_index))


        output_tracks = []
        for i,track in enumerate(copy.copy(mid.tracks)):
            if not i in tracks: continue

            index = 0
            output_track = []

            cut_index = -1
            for pos,msg in enumerate(track):
                #if i == 0: break
                if index >= from_index:
                    cut_index = pos#output_track.append(msg)
                    break
                index += msg.time

            if cut_index == -1: cut_index = pos
            distance = index - from_index
            tempo = 0
            for tc in FileIO.tempo_changes:
                if tc['index'] >from_index: break
                tempo = tc['tempo_long']

            tempo_event = FileIO.tempo_message#Message('set_tempo', tempo=tempo, time=distance)
            tempo_event.time = 0
            tempo_event.tempo = tempo
            if distance >= 0:
                note_off_event = Message('note_off', note=0, velocity=127, time=distance)

                output_track = copy.copy(track[max(0,cut_index-1):])

                #hmmmm
                new_msg = output_track[0].copy(time = min(0,output_track[0].time - from_index))
                del output_track[0]
                #new_msg.time -= from_index
                output_track.insert(0,new_msg)
                #output_track[0].time -= from_index


                if output_track[0].time <0: output_track[0].time = 0
                if i != 0:
                    output_track.insert(0,note_off_event)
                else:
                    tempo_event.time = distance

                    output_track.insert(0,tempo_event)

                if (FileIO.instruments[i] != -1):


                    program_change_event = Message('program_change',channel=max(0,FileIO.instrument_channels[i]),program=FileIO.instruments[i],time=0)
                    output_track.insert(0,program_change_event)


            output_tracks.append(copy.copy(output_track))

        mid.tracks = output_tracks
        mid.save('_temp')

    def readFile (self, filename ):
        FileIO.beat_changes = [] #List of whenever the beat (e.g. 3/4) changes
        FileIO.tempo_changes = []
        FileIO.key_changes = []
        FileIO.track_names = []
        mid = MidiFile(filename)
        FileIO.midi_file = copy.copy(mid)

        FileIO.ranges = []
        FileIO.ranges_name = []
        FileIO.notes_amounts = []

        for x in range(0,len(mid.tracks)):
            FileIO.notes_amounts.append(0)
        FileIO.instruments = []
        for x in range(0,len(mid.tracks)):
            FileIO.instruments.append(-1)
        FileIO.instrument_channels = []
        for x in range(0,len(mid.tracks)):
            FileIO.instrument_channels.append(-1)

        FileIO.ticks_per_beat = mid.ticks_per_beat
        for _track in mid.tracks:
            FileIO.track_names.append(_track.name)

        messages = []
        message_amounts = []

        #Part 1: Create 'note off' events, if not there yet + collect time signature change events
        print ("..Sanitizing MIDI file..")
        time_signature_indices = []
        set_tempo_indices = []
        key_signature_indices = []

        open_notes = []
        has_no_note_off = 1
        for i,track in enumerate(mid.tracks):

            open_notes = []
            min_note = math.inf
            max_note = 0
            index = 0
            message_amounts.append(len(track))
            for x in range(0,len(track)):


                    msg = track.__getitem__(x)
                    #print (msg.type)
                    if msg.type == 'note_off':
                        has_no_note_off = 0 #No need to adjust anything


                    if has_no_note_off == 1:
                        note = -1
                        if hasattr(msg,'note'):
                            note = msg.note
                        channel = -1
                        if hasattr(msg,'channel'):
                            channel = msg.channel
                        if hasattr(msg,'velocity'):
                            velocity = msg.velocity
                        len_before = len(open_notes)
                        if hasattr(msg,'note'):

                            open_notes0 = []
                            removed = 0
                            for x in open_notes:  #remove (only) 1 matching note_on event
                                if removed == 1 or (not (x.note == note and x.channel == channel)) or velocity > 0:
                                    open_notes0.append(x)
                                else:
                                    removed = 1
                            open_notes = open_notes0

                            #open_notes = [x for x in open_notes if not (x.note == note and x.channel == channel)]
                        len_after = len(open_notes)


                        if hasattr(msg,'velocity') and msg.velocity > 0:
                            open_notes.append(msg)


                        if len_after < len_before:

                            note_off_msg = Message('note_off')
                            note_off_msg.velocity = msg.velocity
                            note_off_msg.note = msg.note
                            note_off_msg.channel = msg.channel
                            note_off_msg.time = msg.time
                            messages.append(note_off_msg)
                            # if index >= 586279 and index <= 593279:
                            #     print (str(len_before - len_after)+" removed.")
                            #     print (note_off_msg)

                        else:
                            # if index >= 586279 and index <= 593279:
                            #     print (msg)
                            messages.append(msg)
                    else:
                        messages.append(msg)



                    index += msg.time

                    # if index >= 586279 and index <= 593279:
                        #print (index)
                        # print (msg)
                        # print ("")
                    if msg.type == 'note_on':
                        FileIO.notes_amounts[i] += 1
                        if msg.note < min_note: min_note = msg.note
                        if msg.note > max_note: max_note = msg.note
                        if FileIO.instrument_channels[i] == -1:
                            FileIO.instrument_channels[i] = msg.channel


                    if msg.type == 'time_signature':
                        time_signature_indices.append(index)
                    if msg.type == 'set_tempo':
                        set_tempo_indices.append(index)
                    if msg.type == 'key_signature':
                        key_signature_indices.append(index)
                    if msg.type == 'program_change':
                        if not msg.program in FileIO.not_supported:
                            FileIO.instruments[i] = msg.program




            if min_note == math.inf: #No notes
                FileIO.ranges.append([-1,-1])
                FileIO.ranges_name.append(["",""])
            else:
                FileIO.ranges.append([min_note,max_note])
                FileIO.ranges_name.append([FileIO.get_name(min_note),FileIO.get_name(max_note)])



        # Make a list of all time signatures (e.g. 3/4)
        cnt_tsi = 0
        last_beat_index = 0.0
        for m in messages:
            if m.type == 'time_signature':
                new_val = {}
                new_val['index'] = time_signature_indices[cnt_tsi]
                cnt_tsi = cnt_tsi + 1
                new_val['beat_index'] = new_val['index'] / mid.ticks_per_beat
                new_val['increment'] = new_val['beat_index'] - last_beat_index
                new_val['num'] = m.numerator
                new_val['denom'] = m.denominator
                new_val['beats'] = (m.numerator*4) / m.denominator
                #print (new_val)
                FileIO.beat_changes.append(new_val)
                last_beat_index = new_val['beat_index']

        #Make a list of all tempo changes
        cnt_tch = 0
        time_index = 0.0
        last_beat_index = 0.0
        last_index = 0
        last_tempo = 120
        for m in messages:
            if m.type == 'set_tempo':
                FileIO.tempo_message = copy.copy(m)
                new_val = {}
                new_val['index'] = set_tempo_indices[cnt_tch]
                new_val['index_increment'] = set_tempo_indices[cnt_tch]-last_index

                new_val['beat_index'] = new_val['index'] / mid.ticks_per_beat
                new_val['increment'] = new_val['beat_index'] - last_beat_index
                cnt_tch = cnt_tch + 1
                new_val['tempo_long'] = m.tempo
                new_val['tempo'] = 60000000/m.tempo
                new_val['time_index'] = time_index+ 60*(new_val['increment']/last_tempo) #seconds since start of song

                time_index = new_val['time_index']
                FileIO.tempo_changes.append(new_val)
                last_beat_index = new_val['beat_index']
                last_index = new_val['index']
                last_tempo = new_val['tempo']

        if len(FileIO.tempo_changes) == 0 or FileIO.tempo_changes[0]['index'] > 0:
            new_val = {}
            new_val['index'] = 0
            new_val['beat_index'] = 0
            new_val['increment'] = 0
            new_val['tempo_long'] = 500000
            new_val['tempo'] = 120
            FileIO.tempo_changes.insert(0,new_val)


        def get_note_value(text):
            notes1 = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
            notes2 = ['C','Db','D','Eb','Fb','F','Gb','G','Ab','A','Bb','Cb']
            notes3 = ['C','Bbm','D','Cm','E','Dm','Ebm','G','Fm','A','Gm','Abm']

            if text in notes1:
                return notes1.index(text)
            elif text in notes2:
                return notes2.index(text)
            else:
                return notes3.index(text)

        #Make a list of all key changes
        cnt_kch = 0
        last_beat_index = 0.0
        for m in messages:
            if m.type == 'key_signature':
                new_val = {}
                new_val['index'] = key_signature_indices[cnt_kch]
                new_val['beat_index'] = new_val['index'] / mid.ticks_per_beat
                new_val['increment'] = new_val['beat_index'] - last_beat_index
                cnt_kch = cnt_kch + 1
                new_val['key_name'] = m.key
                print (new_val['beat_index'] )
                new_val['key'] = get_note_value(m.key)
                FileIO.key_changes.append(new_val)
                last_beat_index = new_val['beat_index']

        #Part 2: Create note values incl. duration & current measure
        print ("..Transferring into internal format..")

        notes = []
        track = []
        open_notes = []
        durations = {}
        time_index = 0

        def current_beats( beat_index ):
            beats = 4
            for bc in FileIO.beat_changes:
                if bc['beat_index'] < beat_index:
                    beats = bc['beats']
            return beats

        def current_measure ( beat_index ):
            measure = 0
            last_beats = 4
            for bc in FileIO.beat_changes:

                if beat_index > bc['increment']:
                    beat_index -= bc['increment']
                    measure += bc['increment'] / last_beats
                    last_beats = bc['beats']
                else:
                    break

            return (measure+int(beat_index/last_beats))


        tones = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

        ma_index = 0
        msg_count = -1
        for msg in messages:
            msg_count += 1
            new_val = {}

            if msg_count == message_amounts[ma_index]:
                ma_index += 1
                msg_count = 0
                if len(track) > 0:
                    cnt = 0
                    for item in track:
                        if item.type == 'note':
                            if not str(item.index)+str(item.msg.note)+str(item.msg.channel) in durations:
                                item.duration = 0
                            else:
                                item.duration = durations[str(item.index)+str(item.msg.note)+str(item.msg.channel)]
                            item.original_duration = item.duration
                            item.beats = item.duration / mid.ticks_per_beat
                            cnt= cnt + 1
                    notes.append(track)
                track = []
                open_notes = []
                durations = {}
                time_index = 0


            time_index += msg.time



            if hasattr(msg,'note') and msg.type == 'note_on':

                new_val = Event(type='note',msg=msg,index=time_index, note=msg.note, octave = int(msg.note / 12),channel = msg.channel, velocity = msg.velocity)



                track.append(new_val)

                open_note = {}
                open_note['note'] = msg.note
                open_note['channel'] = msg.channel
                open_note['index'] = time_index




                open_notes.append(open_note)
            else:
                if msg.type == 'note_off':

                    deleted_open_note = [x for x in open_notes if x['note'] == msg.note and x['channel'] == msg.channel]

                    open_notes = [x for x in open_notes if not x['note'] == msg.note and x['channel'] == msg.channel]


                    if len(deleted_open_note) > 0:
                        for don in deleted_open_note:
                            #print ("Duration: "+ str(time_index - don['index']))
                            durations[str(don['index'])+str(don['note'])+str(don['channel'])] = (time_index - don['index'])
                new_val = Event(type='event',msg=msg,index=time_index)

                track.append(new_val)
        cnt = 0
        for item in track:
            if item.type== 'note':
                if str(item.index)+str(item.msg.note)+str(item.msg.channel) in durations:
                    item.duration = durations[str(item.index)+str(item.msg.note)+str(item.msg.channel)]
                else:
                    item.duration = 50
                item.original_duration = item.duration
                item.beats = item.duration / mid.ticks_per_beat
                cnt= cnt + 1
        notes.append(track)


        return notes






    def get_offset(patch):
        if patch >= 24 and patch <= 31: return -12
        if (patch >= 32 and patch <= 39) or patch == 42: return -24
        if patch == 43: return -30
        if patch == 47: return -22
        if patch == 57 or (patch >= 61 and patch <= 63) or patch == 66 or patch == 68 or patch == 69 or patch == 71: return -12
        if patch == 58 or patch == 60 or patch == 67 or patch == 70: return -24

        if patch == 72: return 24
        if patch == 73: return 12


        if patch >= 104 and patch <= 107: return -12
        return 0

    def create_single_tone(patch,note):
        mid = MidiFile()
        track=MidiTrack()

        duration = mid.ticks_per_beat

        _new_msg = Message('program_change')
        _new_msg.channel = 0
        _new_msg.program = patch
        track.append(_new_msg)

        _new_msg = Message('note_on')
        _new_msg.note = note
        _new_msg.velocity = 100
        _new_msg.channel = 0
        _new_msg.time = 0
        track.append(_new_msg)

        _new_msg = Message('note_off')
        _new_msg.note = note
        _new_msg.channel = 0
        _new_msg.velocity = 0
        _new_msg.time = int(duration)
        track.append(_new_msg)

        mid.tracks.append(track)
        mid.save("_temp")

    def create_intro(patch):
        offset = FileIO.get_offset(patch)

        mid = MidiFile()
        track=MidiTrack()
        notes = [60,67,71,72,76] #Music Visualized Intro!
        duration = mid.ticks_per_beat / 2

        _new_msg = Message('program_change')
        _new_msg.channel = 0
        _new_msg.program = patch
        track.append(_new_msg)

        for i,note in enumerate(notes):
            _new_msg = Message('note_on')
            _new_msg.note = note+offset
            _new_msg.velocity = note.velocity
            _new_msg.channel = 0
            _new_msg.time = 0
            track.append(_new_msg)

            if i == len(notes)-1: duration *= 3
            _new_msg = Message('note_off')
            _new_msg.note = note+offset
            _new_msg.channel = 0
            _new_msg.velocity = 0
            _new_msg.time = int(duration)
            track.append(_new_msg)

        mid.tracks.append(track)
        mid.save("_temp")



    def writeFile(self, fileName, notes):
        last_off = 0


        mid = MidiFile()

        mid.ticks_per_beat = FileIO.ticks_per_beat
        # for note in notes[3]:
        #     print (str(note.duration)+" - "+str(note.index))
        print ("..Writing results into '"+ fileName +"'..")

        for tr in notes:
            # print ("************************")
            # print ("************************")
            # print ("************************")

            _track = MidiTrack()
            off_list = []
            index = 0.0
            last_index = 0.0
            for no in tr:
                #Creating the note messages
                #--------------------------

                #Creating any due note_off events (of earlier iterations)
                cnt = 0

                def off_list_key(item):
                    return item['at']

                off_list = sorted(off_list,key=off_list_key)
                for o in off_list:

                    if o['at'] <= no.index:
                        _new_msg = Message('note_off')
                        _new_msg.note = o['note']
                        _new_msg.channel = o['channel']
                        #if cnt == 0:

                        _new_msg.time = (int(o['at']-last_index))
                        last_index += _new_msg.time


                            #index, duration
                            # print ("***************")
                            # print ("Note Off too short:")
                            # print ("***************")
                            #
                            # print ("Note Off: "+str(_new_msg.__dict__))

                        _track.append(_new_msg)
                        cnt = cnt + 1

                off_list = [x for x in off_list if not (x['at'] <= no.index)]

                #Writing Events back as is (according to msg attribute)
                # -> Ignoring 'Note off' events, as they will be written later acc. to duration of notes
                if no.type == 'event' and no.msg.type != 'note_off' and no.msg.type != 'unknown_meta':
                    no.msg.time = (int(no.index - last_index))
                    if no.msg.time < 0:

                        print ("***************")
                        print ("Event too short:")
                        print ("***************")

                        print (no.__dict__)
                    _track.append(no.msg)

                    last_index = no.index


                #Writing Notes
                elif no.type == 'note':

                    _new_msg = Message('note_on')
                    if no.note < 0:
                        no.note = 0
                    if no.note > 127:
                        no.note = 127

                    _new_msg.note = no.note
                    _new_msg.velocity = no.velocity
                    _new_msg.channel = no.channel
                    _new_msg.time = abs(int(no.index - last_index))

                    #print ("Note On: "+str(_new_msg.time))
                    # if no.measure == 12:
                    #     print (no.__dict__)
                    _track.append(_new_msg)
                    if _new_msg.time < 0:

                        print ("**************")
                        print ("Note too short:")
                        print ("**************")
                        print (no.__dict__)

                    #Preparing the note_off event
                    _off = {}
                    _off['note'] = no.note
                    _off['channel'] = no.channel
                    _off['at'] = no.index + no.duration
                    #print ("Diff: "+str(_off['at']-last_off))
                    last_off = _off['at']
                    #print (str(_off['at'])+":  "+str(no.index)+" - "+str(no.duration))
                    off_list.append(_off)

                    last_index = no.index



            off_list = sorted(off_list,key=off_list_key)
            for o in off_list:


                _new_msg = Message('note_off')
                _new_msg.note = o['note']
                _new_msg.channel = o['channel']

                _new_msg.time = (int(o['at']-last_index))
                last_index += _new_msg.time

                _track.append(_new_msg)
                cnt = cnt + 1

            off_list = [x for x in off_list if not (x['at'] <= no.index)]
            mid.tracks.append(_track)


        mid.save(fileName)


    def writeTabsText(self, fileName, tabs,track,settings):

        output = [] #divided into measures, into 6 guitar strings - then just a text (e.g. "|--0--6--6--0--")
        tabs_track = tabs[track]


        def current_index (measure):
            last_beats = 4
            beats = 0
            for bc in FileIO.beat_changes:
                measures_passed = bc['increment'] / last_beats
                #print (str(measures_passed)+' - '+str(measure))
                if measures_passed >= measure:

                    return (beats + (measure * last_beats)) *FileIO.ticks_per_beat
                else:
                    measure -= measures_passed
                    beats += measures_passed * last_beats
                last_beats = bc['beats']

                #print (last_beats)
            return int((beats + (measure * last_beats)) *FileIO.ticks_per_beat)


        current_measure=0
        this_measure = []


        #Make sure that we also include the last measure
        last_measure = 0
        inx = len(tabs_track)-1
        while last_measure == 0 and inx >= 0:
            if len(tabs_track[inx])>0:
                last_measure = tabs_track[inx][0].measure
            inx -= 1
        empty_measure = []
        empty_measure.append(Event(type=='event',measure=last_measure+1))
        tabs_track.append(empty_measure)
        old_next_start = 0

        for position in tabs_track:
            if len(position) == 0: continue


            if position[0].measure != current_measure: #We collected another measure

                #find the lowest common position in this measure

                next_start = current_index(current_measure+1)
                start = old_next_start
                old_next_start = next_start
                measure_length = next_start - start
                index_list = []
                new_list = []
                for pos in this_measure:
                    if len(pos)>0:
                        cnt_ele = 0
                        for ele in pos:
                            if ele.type != 'event' and not (ele.index-start) in index_list:
                                index_list.append(ele.index - start)
                                cnt_ele += 1
                                break
                        if cnt_ele != 0:
                            new_list.append(pos)
                this_measure = copy.copy(new_list)


                if len(index_list) > 0:
                    min_distance = index_list[0]
                    if min_distance == 0: min_distance = measure_length
                    for x in range(1,len(index_list)):
                        if index_list[x] - index_list[x-1] < min_distance:
                            min_distance = index_list[x] - index_list[x-1]

                    for x in range (0,len(index_list)):
                        index_list[x] = int(index_list[x] / min_distance)
                    measure_min = int(measure_length / min_distance)

                    length_list = []
                    for x in range(1,len(index_list)):
                        length_list.append(index_list[x]-index_list[x-1])
                    length_list.append((measure_min - index_list[-1]))


                    string_output = []
                    for x in range(0,len(settings[2])):
                        string_output.append ("--")
                    for intm, pos in enumerate(this_measure):

                        length_max = 0
                        for ele in pos:
                            if ele.type != 'event':
                                string_output[ele.string] += str(ele.fret)+"-"
                                length_max = len(string_output[ele.string])
                        still_short = True
                        while still_short:
                            still_short = False
                            for x in range(0,len(settings[2])):
                                if len(string_output[x]) < length_max+(2*length_list[intm])-1:
                                    string_output[x] += "-"
                                    still_short = True

                    # for x in range(0,len(settings[2])):
                    #     print (string_output[x])
                    # print ("")
                    # print ("")
                    output_measure = []
                    for x in range(0,len(settings[2])):
                        output_measure.append(string_output[x])
                    output.append(output_measure)



                current_measure = position[0].measure
                this_measure = []

            this_measure.append(position)

        final_text = ""
        cut_point = 80
        remaining_text = []
        for x in range(0,len(settings[2])):
            remaining_text.append("")
        for inop, measure in enumerate(output):
            for inme,string in enumerate(measure):
                this_text = ""
                add = 0
                if inop == 0:
                    this_text += Event.tones[int(settings[2][len(settings[2])-1-inme] % 12)]
                    if len(this_text) == 1: this_text += " "
                    this_text += "||"
                    add = len(this_text)

                if remaining_text[inme] != "": #add parts of the last measure
                    string = remaining_text[inme]+"|"+string
                    remaining_text[inme] = ""


                if len(string)+len(this_text) > cut_point: #have to cut
                    this_text += string[0:(cut_point-len(this_text))]

                    remaining_text[inme] = string[cut_point+add:]


                else:
                    this_text += string + "|"
                #if len(string)+len(this_text) < 80: #start the next measure

                final_text += this_text
                final_text += '\n'
            final_text += '\n\n'

       #Finishing the remaining text
        for x in range(0,len(remaining_text[0]),cut_point):
            for y in range(0,len(settings[2])):
                final_text += remaining_text[y][x:x+cut_point]
                if x>=len(remaining_text[0])-cut_point+2:
                    final_text += '||'
                final_text += '\n'
            if x < len(remaining_text[0])-cut_point:
                final_text += '\n\n'

        file = open(fileName,"w")
        file.write(final_text)
        file.close()



    last_tempo = 0
    cnttempo = 0
    def writeTabsGPX(self, fileName, tabs, settings):
        #curl = guitarpro.parse('Adams, Bryan - (Everything I Do) I Do It For You v2.gp3')
        resolution = int((1/4)*960)
        #TODO: Add Settings for title, author etc. (Prompt it when trying to save)
        #GP works in 960 time - have to recalculate all indices and durations
        #duration = guitarpro.models.Duration.fromTime(960)

        # for x in range(0,len(tabs[0])):
        #     print (tabs[0][x][0].index * 960 / FileIO.ticks_per_beat)


        #create Index-List for measure beginnings
        max_index = 0
        tabs = [tabs]
        settings = [settings]
        for track in tabs:
            if len(track) == 0: continue
            pos = len(track)-1
            while (max_index == 0) and pos >= 0:
                if track[pos][0].index > max_index: max_index = track[pos][0].index
                pos -= 1

        last_beats = 4
        beats = 0
        index_list = []
        old_end = 0

        for bc in FileIO.beat_changes:
            if last_beats > 0:
                measures_passed = bc['increment'] / last_beats
            else:
                measures_passed = 0

            if measures_passed == 0: last_beats = int(bc['beats'])
            for x in range (0,int(measures_passed)):
                index_list.append(x * last_beats * FileIO.ticks_per_beat + old_end)
                if x == measures_passed-1:
                    old_end = int((x+1) * last_beats * FileIO.ticks_per_beat + old_end)
                    last_beats = int(bc['beats'])
        for x in range(old_end,max_index,last_beats * FileIO.ticks_per_beat):
            index_list.append(x)
        last_measure_length = last_beats * FileIO.ticks_per_beat
        measure_index = 0 #index of measure begin

        def get_measure_index(index):
            for inil,il in enumerate(index_list):
                if il > index: return inil-1
            return len(index_list)-1

        def get_measure(index):

            for inil,il in enumerate(index_list):
                if il > index: return index_list[inil-1]
            return index_list[len(index_list)-1]

        def create_measure_header(cindex,cstart):


            _header = guitarpro.models.MeasureHeader(number=cindex+1,start=960+int(cstart*960//FileIO.ticks_per_beat))
            num = 4
            den = 4
            for bc in FileIO.beat_changes:
                if bc['index'] > cstart: break
                num = bc['num']
                den = bc['denom']

            time_signature = guitarpro.models.TimeSignature(numerator=num, denominator=guitarpro.models.Duration.fromTime(960*(4/den)))
            _header.timeSignature = time_signature
            _header.keySignature = guitarpro.models.KeySignature(value=get_key(cstart))

            return _header

        def get_key(index):
            key = ""
            for kc in FileIO.key_changes:
                if kc['index'] > index: break
                key = kc['key_name']
            if key=='Fb':return (-8,0)
            if key=='Cb':return (-7,0)
            if key=='Gb':return (-6,0)
            if key=='Db':return (-5,0)
            if key=='Ab':return (-4,0)
            if key=='Eb':return (-3,0)
            if key=='Bb':return (-2,0)
            if key=='F':return (-1,0)
            if key=='C':return (0,0)
            if key=='G':return (1,0)
            if key=='D':return (2,0)
            if key=='A':return (3,0)
            if key=='E':return (4,0)
            if key=='B':return (5,0)
            if key=='F#':return (6,0)
            if key=='C#':return (7,0)
            if key=='G#':return (8,0)
            return (0,0)


        def get_effect(index):
            tempo = 0
            for tc in FileIO.tempo_changes:
                if tc['index'] > index: break
                tempo = tc['tempo']

            if tempo > 200 or tempo < 40:
                tempo = 150
            effect=guitarpro.models.BeatEffect(mixTableChange=guitarpro.models.MixTableChange(tempo=guitarpro.models.MixTableItem(int(tempo))))
            if tempo == FileIO.last_tempo:
                effect = guitarpro.models.BeatEffect()
            FileIO.last_tempo = tempo
            #FileIO.cnttempo += 1
            # if  FileIO.cnttempo > 350:
            #
            #     if FileIO.cnttempo < 400:
            #         print (tempo)
            #     return guitarpro.models.BeatEffect()
            return effect


        output = guitarpro.models.Song()
        tracks = []
        
        for inta,track in enumerate(tabs):
            #Make sure that we also include the last measure
            empty_pos = []
            empty_pos.append(Event(type='note',index=max_index+last_measure_length))

            max_index += last_measure_length

            for x in range(index_list[-1]+last_measure_length,max_index,last_measure_length):
                index_list.append(x)
            index_list.append(max_index)
            track.append(empty_pos)

            empty_pos = []
            empty_pos.append(Event(type='note',index=max_index+last_measure_length+last_measure_length))
            track.append(empty_pos)


            _track = guitarpro.models.Track(output)
            ci = 0
            cs = 0
            measures = []
            add_empty = 0
            this_measure = []
            #print (len(track))
            remaining_length = 0
            remaining_notes = []
            for intr,position in enumerate(track):
                measure_start = get_measure(position[0].index)
                #print (measure_start)
                # print ("***")
                # print (measure_start)
                # print (cs)
                # print ("****")
                if measure_start > cs:
                    #20480
                    # if remaining_length>0 and measure_start == cs:
                    #     #in empty measure for drawing tied notes
                    #     add_empty -= 1
                    #     if len(index_list) > ci+1:
                    #         measure_start = index_list[ci+1]
                    #     else:
                    #         measure_start = measure_start + last_measure_length
                    #
                    _measure = guitarpro.models.Measure(_track)
                    _voice = guitarpro.models.Voice(_measure)
                    _empty_voice = guitarpro.models.Voice(_measure)
                    beats = []

                    if get_measure_index(position[0].index) - ci > 1:
                        add_empty = get_measure_index(position[0].index) - ci - 1

                    fill_empty_measures = False #Remaining tones

                    in_measure = 0 #index when the last sound ended (to calculate rests)
                    for mposition in this_measure:
                        _beat = guitarpro.models.Beat(_measure)

                        pos_index = mposition[0].index - cs







                        if remaining_length > 0:
                            strings_used = []
                            notes = []
                            for note in remaining_notes:
                                if note.string in strings_used: continue
                                strings_used.append(note.string)
                                dur = int(remaining_length*960 // FileIO.ticks_per_beat)
                                while guitarpro.models.Duration.fromTime(dur).time >= dur+resolution and dur > 0:
                                    dur -= resolution
                                note.duration = guitarpro.models.Duration.fromTime(dur)
                                note.type = guitarpro.models.NoteType.tie
                                notes.append(note)




                            _beat = guitarpro.models.Beat(_voice,notes=notes,duration=guitarpro.models.Duration.fromTime(dur))#,effect=get_effect(mposition[0].index)
                            beats.append(_beat)


                            #guitarpro.models.Duration.fromTime(dur).time#
                            in_measure += guitarpro.models.Duration.fromTime(dur).time*FileIO.ticks_per_beat//960##int(remaining_length*960 // FileIO.ticks_per_beat)#+int(resolution)
                            #print ("r:")
                            #print (int(remaining_length*960 / FileIO.ticks_per_beat))
                            remaining_notes = []
                            remaining_length = 0

                        #For some reason the previous note was too long
                        if in_measure > pos_index and len(beats)>0:
                            dur = pos_index*960 // FileIO.ticks_per_beat
                            while guitarpro.models.Duration.fromTime(dur).time > dur and dur >= 0:
                                dur -= resolution

                            if dur > 0:
                                beats[-1].duration = guitarpro.models.Duration.fromTime(dur)
                            else:
                                del beats[-1]
                            in_measure = pos_index



                        if pos_index > in_measure and remaining_length == 0:
                            #position further than last duration -> adding rests


                            dur = int((pos_index-in_measure)*960 // FileIO.ticks_per_beat)
                            dur = int(int(round(dur/resolution)) * resolution)
                            _beat = guitarpro.models.Beat(_voice,notes=[],duration=guitarpro.models.Duration.fromTime(dur))#,effect=get_effect(mposition[0].index)
                            beats.append(_beat)
                            in_measure = pos_index
                            # print ("")
                            # print (cs)
                            # print (in_measure)
                            # print (measure_start)

                        duration = 0 #longest duration in beat
                        for note in mposition:
                            if note.duration > duration: duration = note.duration

                        #Check if note goes beyond the measure
                        if len(index_list) > ci+1:
                            allowed_length = index_list[ci+1] - in_measure - cs
                        else:
                            allowed_length = last_measure_length - in_measure



                        remaining_length = 0
                        if duration > allowed_length:
                            #print (allowed_length)
                            remaining_length = duration - allowed_length
                            remaining_length = guitarpro.models.Duration.fromTime(remaining_length).time
                        else:
                            allowed_length = duration

                        #Check if rest of the tone will have to end in an empty measure
                        if duration > index_list[ci+1]-cs-in_measure:

                            fill_empty_measures = True

                        notes = []
                        cnt = 7
                        def note_key(item):
                            return item.string
                        mposition = sorted(mposition,key=note_key)
                        strings_used = []
                        for note in mposition:
                            if note.string in strings_used: continue
                            note.string = note.string
                            _note = guitarpro.models.Note(_beat, value=note.fret, velocity=95, string=note.string+1, durationPercent=1.0, swapAccidentals=False, type=guitarpro.NoteType.normal)
                            strings_used.append(note.string)
                            notes.append(_note)
                            if remaining_length > 0:
                                remaining_notes.append(copy.copy(_note))


                        dur0 = int(allowed_length*960 // FileIO.ticks_per_beat)
                        dur = int(int(round(dur0//resolution)) * resolution)

                        while guitarpro.models.Duration.fromTime(dur).time >= dur+resolution and dur>0:
                            dur -= resolution

                        _beat = guitarpro.models.Beat(_voice,notes=notes,duration=guitarpro.models.Duration.fromTime(dur),effect=get_effect(mposition[0].index))
                        # if len(measures) == 48 and len(beats) == 4:
                        #     continue
                        # if len (measures) == 3:
                        #     print ("d")
                        if dur != 0:
                            beats.append(_beat)

                        final_add_value = guitarpro.models.Duration.fromTime(dur).time*FileIO.ticks_per_beat//960
                        # if guitarpro.models.Duration.fromTime(dur).time >= dur+resolution:
                        #     final_add_value = dur*FileIO.ticks_per_beat//960

                        in_measure += final_add_value




                    _voice = guitarpro.models.Voice(_measure,beats)
                    voices = []
                    voices.append(_voice)
                    voices.append(_empty_voice)

                    _header = create_measure_header(ci,cs)

                    _measure = guitarpro.models.Measure(_track,header=_header,voices=voices)
                    measures.append(_measure)

#Create empty measures / Measures with just the remaining tied sounds of old tones
                    empty_measure_start = cs
                    empty_measure_end = cs+last_measure_length

                    for x in range (0,add_empty):
                        if len(index_list) > ci+x+1:
                            empty_measure_start = index_list[ci+x+1]
                        else:
                            empty_measure_start += last_measure_length

                        if len(index_list) > ci+x+2:
                            empty_measure_end = index_list[ci+x+2]
                        else:
                            empty_measure_end += last_measure_length

                        empty_length = empty_measure_end - empty_measure_start

                        empty_voices = []
                        if fill_empty_measures:
                            notes = []
                            _new_voice = guitarpro.models.Voice(_measure)
                            strings_used = []
                            beats = []


                            for note in remaining_notes:
                                if note.string in strings_used: continue
                                strings_used.append(note.string)
                                used_length = remaining_length
                                if remaining_length > empty_length:
                                    used_length = empty_length
                                remaining_length -= used_length
                                dur = int(used_length*960 // FileIO.ticks_per_beat)
                                while guitarpro.models.Duration.fromTime(dur).time >= dur+resolution and dur > 0:
                                    dur -= resolution
                                note.duration = guitarpro.models.Duration.fromTime(dur)
                                note.type = guitarpro.models.NoteType.tie

                                notes.append(note)

                            _beat = guitarpro.models.Beat(_new_voice,notes=notes,duration=guitarpro.models.Duration.fromTime(dur))#,effect=get_effect(empty_measure_start)
                            beats.append(_beat)
                            # print ("d")

                            if remaining_length <= 0:
                                remaining_notes = []
                                remaining_length = 0
                            _new_voice = guitarpro.models.Voice(_measure,beats)
                            empty_voices.append(_new_voice)
                        else:
                            empty_voices.append(_empty_voice)


                        empty_voices.append(_empty_voice)
                        empty_measure = guitarpro.models.Measure(_track,header=_header,voices=empty_voices)
                        measures.append(copy.copy(empty_measure))

                    fill_empty_measures = False

                    add_empty = 0
                    # print ("")
                    if len(measures) == 144:
                        print ("d")
                    # print (get_measure_index(position[0].index) - ci)
                    # if get_measure_index(position[0].index) - ci > 1:
                    #     #Create empty measures
                    #     measures.append(guitarpro.models.Measure(_track))
                    cs = measure_start
                    # print ("#####")
                    # print (ci)
                    # print (position[0].index)
                    ci = get_measure_index(position[0].index)
                    # print (ci)
                    this_measure = []
                this_measure.append(position)

            if measures == []:
                _header = guitarpro.models.MeasureHeader(number=0,start=960)
                measures.append(guitarpro.models.Measure(_track,header=_header,voices=voices))

            gstrings = []
            for inse,s in enumerate(settings[inta][2]):
                gstrings.append(guitarpro.models.GuitarString(inse, s))
            # gstrings = [guitarpro.models.GuitarString(n, v)
            #     for n, v in [(0,64),(1, 64), (2, 59), (3, 55)]]
            _track = guitarpro.models.Track(output, number=1, fretCount=24, offset=0, isPercussionTrack=False, is12StringedGuitarTrack=False, isBanjoTrack=False, isVisible=True, isSolo=False, isMute=False, indicateTuning=True, name='Track 1', measures=measures, strings=gstrings, port=1, color=guitarpro.Color(r=255, g=0, b=255, a=1), useRSE=False)
            tracks.append(_track)
        output = guitarpro.models.Song(title=fileName, subtitle='', artist='', album='', words='', music='', copyright='', tab='', instructions='', tempo=200, hideTempo=True,tracks=tracks)






        guitarpro.write(output, fileName, version=None, encoding='cp1252')




class Event:
    tones = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']


    last_beats_value = 4
    def current_measure ( beat_index ):
        measure = 0
        last_beats = 4
        for bc in FileIO.beat_changes:

            if beat_index > bc['increment']:
                beat_index -= bc['increment']
                measure += bc['increment'] / last_beats
                last_beats = bc['beats']
            else:
                break

        Event.last_beats_value = last_beats
        return (measure+(beat_index/last_beats))




    def current_beat (measure, beats_in):
        last_beats = 4
        beats = 0
        for bc in FileIO.beat_changes:
            measures_passed = bc['increment'] / last_beats
            #print (str(measures_passed)+' - '+str(measure))
            if measures_passed >= measure:

                return beats + (measure * last_beats) + beats_in
            else:
                measure -= measures_passed
                beats += measures_passed * last_beats
            last_beats = bc['beats']
            #print (last_beats)
        return 0

    def __init__(self,note=0,octave=0,channel=0,beats=0,measure=0,beats_in_measure=0,index=-1,beat_index=-1,type='note', msg=Message('note_on'),duration = 0, velocity=64): #Most realistic init

        self.velocity = velocity
        self.ticks = FileIO.ticks_per_beat
        self.note = note
        self.note_name = Event.tones[self.note % 12]
        self.octave = octave
        self.channel = channel
        self.type = type
        self.measure = measure
        self.beats_in_measure = beats_in_measure

        if index == -1:
            if beat_index == -1:
                self.beat_index = Event.current_beat(self.measure, self.beats_in_measure)
            else:
                self.beat_index = beat_index
            self.index = self.beat_index * FileIO.ticks_per_beat
        else:
            self.index = index
            self.beat_index = index / FileIO.ticks_per_beat

        self.original_index = self.index
        #Index value beats measure value (if existing):
        cm = Event.current_measure(self.beat_index)
        self.measure = int(cm)
        self.beats_in_measure = (cm % 1) * Event.last_beats_value



        self.beats = beats
        if duration > 0:
            self.duration = duration
        else:
            self.duration = self.beats * FileIO.ticks_per_beat
        self.original_duration = self.duration
        self.msg = msg

        #Guitar related information
        self.base_fret = 0
        self.string = 0 #originally sorted
        self.fret = 0 #i.e. 20 (not base+x)

        #Rhythm Group related
        self.rg = -1




