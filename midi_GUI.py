import MidiMagic
#import image_test

#import guitarpro
#curl = guitarpro.parse('Santana - Samba Pa Ti (guitar pro).gp5')

from midi_IO import *
from midi_tools import *
from midi_brain import *
from midi_brain_guitar import *
from midi_brain_piano import *
from midi_cc import *
from rhythm_groups import *

import sys
from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
import Pmw
import tkinter.ttk as ttk
from functools import partial
import time
from tkinter import font
import os



#from midi_playback import Playback
from midi_pygame_playback import PlaybackThread
from asyncio.tasks import wait
#from sf2utils import preset



    #
    #m = Munkres()
    #
    #matrix = [[1, 9, 1],
    #          [10, 3, 2],
    #          [8, 7, 4]]
    #m = Munkres()
    #indexes = m.compute(matrix)
    #total = 0
    #for row, column in indexes:
    #    value = matrix[row][column]
    #    total += value
    #    print ('(%d, %d) -> %d' % (row, column, value))
    #print ('total cost: %d' % total)                    


io = FileIO()

notes = []
#notes = io.readFile("Kirbys Dream Land - Green Greens.mid"       )
#notes = Create.arrange(notes)
#notes = Create_Piano.arrange(notes)
#io.writeFile('output.mid',notes)
PROGRAM_NAME_LONG = " Arrangr - Let's get Creative!"
PROGRAM_NAME = "Arrangr"

root = Tk()
root.geometry('1000x600')
root.minsize(1000,600)
root.config(bg='white')
root.title(PROGRAM_NAME_LONG)
root.option_add('*ScrolledFrame*background', 'white')
helv20 = font.Font(family="Helvetica",size=20,weight="bold")
helv15 = font.Font(family="Helvetica",size=15,weight="bold")
####################
#End Program       #
####################
def end_program():
    root.destroy()

input_file_name = ""

################
#Main Menu Init#
################
tk_input_file_name = StringVar(root,"-")
tk_selected = StringVar(root,"-")
tk_keep_all_short = BooleanVar()
tk_create_chords = BooleanVar()

all_tracks_list = []
instruments_list = [] #GM-Number, bool:treat as ensemble instrument,maximum stt, create arpeggios, [range_low,range_high],[combining_group],(guitar settings:) [patch,strings,[base tones top-down],highest fret,hand-with,same time tones] -> Empty if not applicable

####################
#Open New Midi File#
####################
playing_amount = 0
play_all_state = False
playthread = None

def open_midi_file(skip_file=False,event=None, do_next=""):
    global input_file_name
    global all_tracks_list
    global notes
    no_notes = True
    if skip_file and input_file_name == '':
        tkinter.messagebox.showinfo(
                "Track Selection",
                "You need to select a MIDI file first!"
            )
        skip_file = False

    while no_notes and not skip_file:
        file_name = ""
        file_name = tkinter.filedialog.askopenfilename(defaultextension=".mid",filetypes=[("MIDI Files", "*.mid"), ("MIDI Files", "*.midi")])

        if file_name == '': return

        input_file_name = file_name
        notes = io.readFile(input_file_name)


        for na in FileIO.notes_amounts:
            if na > 0:
                no_notes = False
                break

        if no_notes:
            tkinter.messagebox.showerror(
                "Importing",
                "This MIDI file is empty!"
            )

    file_name = os.path.basename(input_file_name)
    if len(file_name) > 50:
        file_name = file_name[:45] + "~"+ file_name[-4:]
    tk_input_file_name.set(file_name)

    play_all_buttons = []
    play_all_images = []

    play_button_states = []

    play_buttons = []
    play_button_images = []

    checkbox_states = []

    PlaybackThread.index_str_list = [StringVar(),StringVar()]


    def press_play(track):
        global playing_amount
        global playthread
        global play_all_state

        #print (PlaybackThread.time_index)
        amount_before = playing_amount

        if track != -1:
            play_button_states[track] = not play_button_states[track]
            if play_button_states[track]:
                play_button_images[track] = PhotoImage(file="icons/pause.png").subsample(2)

                playing_amount += 1
            if not play_button_states[track]:
                play_button_images[track] = PhotoImage(file="icons/play.png").subsample(2)
                playing_amount -= 1
            play_buttons[track].config(image=play_button_images[track])


        if playing_amount > 0:
            play_all_state = True
        else:
            play_all_state = False
        if play_all_state:
            play_all_images[0] = PhotoImage(file="icons/pause.png")
        else:
            play_all_images[0] = PhotoImage(file="icons/play.png")
        play_all_buttons[0].config(image=play_all_images[0])


        tracks = []
        for i,state in enumerate(play_button_states):
            if state: tracks.append(i+1)

        #Possible states:
        #playthread None or STH -> None = New or rewound, STH = Something is playing or is paused
        #amount_before -> >0 = There was already a song playing (we need to pause now and remember the time), =0 -> a song was paused or new (see playthread)
        #len(tracks) -> >0 = Something should be created now, =0 -> Everything should be stopped

        #playthread-None -> 0-time_index, start playing from beginning
        #playthread-STH,len(tracks)>0,amount_before>0 -> (sth changed), stop song, remember time_index, create new song from last_time_index(?),sab=False
        #playthread-STH,len(tracks)==0 -> (now all is paused), stop song, remember time_index, don't create new song
        #playthread-STH,len(tracks)>0,amount_before==0 -> (Resumed after Pause), create new song from last_time-index, sab=False

        #Little adjustment for the following code, in case of pressing "Play all"
        if track == -1 and amount_before == 0:
            amount_before = 1
        if track == -1 and amount_before > 0:
            amount_before = 0


        #MIDI is new, or rewound -> Play from beginning
        if playthread == None:
            PlaybackThread.time_index = 0.0

            if len(tracks) == 0: return #Shouldn't happen
            io.create_midi_slice(tracks, start_at_beginning=True)
            playthread = PlaybackThread(1,"Thread","_temp")
            PlaybackThread.time_index = FileIO.new_time_index
            playthread.exit_flag = False
            playthread.start()
            return

        #MIDI is currently playing or paused
        if len(tracks) == 0:

            playthread.exit_flag = True
            playthread.remember_time = True

            return

        #There is at least one track active
        playthread2 = PlaybackThread(1,"Thread","_temp")
        playthread2.exit_flag = False
        playthread.next_instance = playthread2

        if amount_before > 0:

            playthread.exit_flag = True
            playthread.remember_time = True

        io.create_midi_slice(tracks, time_index=PlaybackThread.last_time_index,start_at_beginning=False)

        playthread = playthread2

        if amount_before == 0:
            playthread.start()


        #playthread.start()




    def press_play_all():
        global play_all_state
        global playing_amount


        play_all_state = not play_all_state
        if play_all_state:
            play_all_images[0] = PhotoImage(file="icons/pause.png")
        else:
            play_all_images[0] = PhotoImage(file="icons/play.png")
        play_all_buttons[0].config(image=play_all_images[0])

        for x in range(0,len(play_button_states)):
            if play_all_state and play_button_states[x] == False:
                play_button_images[x] = PhotoImage(file="icons/pause.png").subsample(2)
                play_button_states[x] = True
                playing_amount += 1
            if not play_all_state and play_button_states[x] == True:
                play_button_images[x] = PhotoImage(file="icons/play.png").subsample(2)
                play_button_states[x] = False
                playing_amount -= 1
            play_buttons[x].config(image=play_button_images[x])
        press_play(-1)

    def press_rewind():
        global play_all_state
        global playing_amount
        global playthread

        PlaybackThread.time_index = 0
        if playthread == None:
            return
        playthread.exit_flag = True
        for x in range(0,len(play_button_states)):
            if play_button_states[x] == True:
                play_button_images[x] = PhotoImage(file="icons/play.png").subsample(2)
                play_button_states[x] = False
                playing_amount -= 1
                play_buttons[x].config(image=play_button_images[x])
        play_all_images[0] = PhotoImage(file="icons/play.png")
        play_all_buttons[0].config(image=play_all_images[0])
        play_all_state = False
        playthread = None

        #press_play(-1)
        PlaybackThread.index_str_list[0].set("0.00:000")

    def select_all():
        for x,state in enumerate(checkbox_states):
            if FileIO.notes_amounts[x+1] > 0:
                state.set(1)

    def deselect_all():
        for state in checkbox_states:
            state.set(0)
    def import_midi():
        global all_tracks_list
        global playthread
        import_list = [0]
        for x,state in enumerate(checkbox_states):
            if state.get() == 1:
                import_list.append(x+1)
        if len(import_list) == 1:
            tkinter.messagebox.showinfo(
                "Importing",
                "Choose at least one track!"
            )
            return
        else:
            FileIO.imported_tracks = copy.copy(import_list)
            FileIO.who_plays_melody = []
            s = "s"
            if len(import_list) == 2: s = ""
            tk_selected.set(str(len(import_list)-1) + " Instrument"+s)
            new_track_list = ['Auto-Detect']
            for x,il in enumerate(import_list):
                if x==0: continue
                new_track_list.append(str(x)+" - "+FileIO.track_names[il])

            if len(new_track_list)>1: all_tracks_list = copy.copy(new_track_list[1:]) #global list

            cb_where_is_melody.config(values=new_track_list)
            cb_where_is_melody.current(0)
            if playthread != None:
                playthread.exit_flag = True
            playthread = None


            open_midi.destroy()

            if do_next == 'add instrument':
                add_new_instrument()

    def do_destroy():
        global playthread
        if playthread != None:
            playthread.exit_flag = True
        playthread = None
        open_midi.destroy()

    open_midi = Toplevel(root, bg='white')
    open_midi.grab_set()
    open_midi.title(PROGRAM_NAME+" - Import MIDI Tracks")
    open_midi.protocol('WM_DELETE_WINDOW', do_destroy)

    open_midi.geometry('800x500+200+200')
    open_midi.resizable(False, False)
    open_midi.transient(root)
    open_midi.focus_force()
    index_frame = Frame(open_midi, bg='white',padx=20,pady=10)


    e = Entry(index_frame, textvariable=PlaybackThread.index_str_list[0])
    e.config(state='disabled', disabledbackground='white',disabledforeground='black', relief='groove', font=helv20, width='10',justify='center')
    PlaybackThread.index_str_list[0].set("0.00:000")
    e.pack(side='right')
    index_frame.pack(side='top', fill='x')


    middle_part = Frame(open_midi,bg='white')


    control_buttons_frame = Frame(middle_part, bg='white', padx=30)
    two_buttons = Frame(control_buttons_frame, bg='white')
    play_all_images.append(PhotoImage(file="icons/play.png"))
    play_all_buttons.append(Button(two_buttons,image=play_all_images[-1],compound='top', bg='white',relief=GROOVE, command=press_play_all))
    play_all_buttons[-1].pack(side='top',pady = 3)
    rewind_image = PhotoImage(file="icons/return_to_start.png")
    rewind_button = Button(two_buttons,image=rewind_image,compound='top', bg='white',relief=GROOVE, command=press_rewind)
    rewind_button.pack(side='top',pady = 3)
    two_buttons.pack(side='left')
    control_buttons_frame.pack(side='left',fill='y')

    label_frame = Frame(middle_part, bg='white')
    label1 = Label(label_frame,text="Instrument",bg='white',width=27)
    label2 = Label(label_frame,text="Track Name",bg='white',width=30)
    label2b = Label(label_frame,text=" ",bg='white',width=11)
    label3 = Label(label_frame,text="Import",bg='white',width=10)


    label1.pack(side='left')
    label2.pack(side='left')
    label2b.pack(side='left')

    label3.pack(side='left')


    label_frame.pack(side='top', fill='x')


    #Scrollable Frame
    #scroll_frame = Frame(open_midi)# #ScrolledFrame - pmw library / Frame(open_midi)
    scroll_frame0 = Pmw.ScrolledFrame(middle_part)
    scroll_frame0.config(width=5000)
    scroll_frame0.config(bg='white')
    scroll_frame = scroll_frame0.interior()



    for x in range(1,len(FileIO.track_names)):
        if FileIO.instruments[x] == -1 or FileIO.notes_amounts[x] == 0:
            if FileIO.instrument_channels[x] == 9  or FileIO.notes_amounts[x] == 0:
                play_button_images.append(PhotoImage())
                play_buttons.append(Button())
                play_button_states.append(False)
                checkbox_states.append(IntVar())

                continue
            else:
                FileIO.instruments[x] = 0 #Default to Piano


        row = Frame(scroll_frame, bg='white')



        _label2 = Message(row, text=FileIO.GM_names[FileIO.instruments[x]],bg='white',fg='black',width=200)
        _label2.grid(row=0,column=0)



        _instrument_pic = PhotoImage(file="icons/instruments/"+str(FileIO.instruments[x]+1)+".png")
        _instrument_pic = _instrument_pic.subsample(14)
        _photo_field = Label(row,image=_instrument_pic,borderwidth="0",highlightthickness="0", bg='white')
        _photo_field.image = _instrument_pic # keep a reference!
        _photo_field.grid(row=0,column=1)


        play_button_images.append(PhotoImage(file="icons/play.png").subsample(2))
        play_buttons.append(Button(row,image=play_button_images[-1],compound='top', bg='white',relief=GROOVE, command=partial(press_play, x-1)))
        play_button_states.append(False)
        play_buttons[-1].grid(row=0,column=2)


        _label = Message(row, text='"'+FileIO.track_names[x]+'"', bg='white', fg='black',width=200)
        _label.grid(row=0,column=3)#.pack(side='left',fill='x',expand='yes')#.

        _infogroup = Label(row, text='Notes: '+str(FileIO.notes_amounts[x])+'\nRange: '+FileIO.ranges_name[x][0]+' - '+FileIO.ranges_name[x][1])
        _infogroup.grid(row=0,column=4)

        checkbox_states.append(IntVar())
        _checkbox = Checkbutton(row,variable=checkbox_states[-1],onvalue=1,offvalue=0)
        if FileIO.notes_amounts[x] > 0:
            _checkbox.select()
        else:
            _checkbox.config(state='disabled', disabledforeground='grey')
        _checkbox.grid(row=0,column=5,sticky='E')

        Grid.columnconfigure(row,0, weight=4, uniform='a')
        Grid.columnconfigure(row,1, weight=1, uniform='a')
        Grid.columnconfigure(row,2, weight=1, uniform='a')
        Grid.columnconfigure(row,3, weight=4, uniform='a')
        Grid.columnconfigure(row,4, weight=4, uniform='a')
        Grid.columnconfigure(row,5, weight=1, uniform='a')


        row.pack(side='top',fill='both',padx = 5,pady = 3)#,fill='x',expand='yes')
        if x < len(FileIO.track_names)-1:
            ttk.Separator(scroll_frame,orient=HORIZONTAL).pack(side='top',fill='x',padx=5)

    scroll_frame0.pack(side='left',fill='both',expand='yes', padx = 5, pady = 3)

    Label(middle_part,text="                             ",bg='white').pack(side='left')
    middle_part.pack(side='top', fill='both', expand='yes')


    button_row = Frame(open_midi,bg='white')

    Button(button_row,text="Select all", bg='white', relief='groove', font=helv15, command=select_all).pack(side='left',padx = 15,pady = 3)
    Button(button_row,text="Deselect all", bg='white', relief='groove', font=helv15, command=deselect_all).pack(side='left',padx = 15,pady = 3)
    Button(button_row,text="Import!", bg='white', relief='groove', font=helv15, command=import_midi).pack(side='right',padx = 15,pady = 3)

    button_row.pack(side='top',fill='both',expand='yes')
    #box.pack(side='top',fill='x',expand='yes')
    open_midi.mainloop()
    #open_midi.grab_release()




####################################################################################################################################################
right_half_elements = []
photo_image = None
play_button_img = PhotoImage(file="icons/play.png")
selected_instrument = 1
new_instrument = None
def add_new_instrument(event=None):
    global selected_instrument
    global right_half_elements
    global input_file_name
    global new_instrument

    if input_file_name == "":
        tkinter.messagebox.showinfo(
                "Adding Instruments",
                "Please select an input MIDI file first!"
            )
        open_midi_file(do_next="add instrument")
        return

    def do_destroy():
        global playthread
        if playthread != None:
            playthread.exit_flag = True
        playthread = None
        new_instrument.destroy()

    new_instrument = Toplevel(root, bg='white')
    new_instrument.grab_set()
    new_instrument.title(PROGRAM_NAME+" - Add a New Instrument")
    new_instrument.protocol('WM_DELETE_WINDOW', do_destroy)

    new_instrument.geometry('640x500+200+200')
    new_instrument.resizable(False, False)
    new_instrument.transient(root)
    new_instrument.focus_force()

    def play_intro(patch=-1):
        global selected_instrument
        if patch == -1:
            patch = selected_instrument-1
        FileIO.create_intro(patch)
        playthread = PlaybackThread(1,"Thread","_temp")
        playthread.exit_flag = False
        playthread.start()
    scrollbar = ttk.Scrollbar(new_instrument, orient=VERTICAL)


    selected_instrument = 1

    def listbox_doubleclick(event=None):
        global selected_instrument

        if (selected_instrument >= 25 and selected_instrument <= 40) or selected_instrument == 106:
            add_guitar_instrument(selected_instrument)
            return
        add_piano_instrument(selected_instrument)

    lbl_instrument_name = Message(new_instrument,text=FileIO.GM_names[selected_instrument-1],font=helv20,bg='white', width=170)

    photo_image = PhotoImage(file="icons/instruments/"+str(selected_instrument)+".png").subsample(4)
    lbl_instrument = Label(new_instrument,image=photo_image,borderwidth="0",highlightthickness="0",bg="white")

    btn_play_now = Button(new_instrument,image=play_button_img, relief='groove', command=play_intro)

    lbl_type_d = Label(new_instrument,text="Type:",font=helv12b, bg='white')
    lbl_type = Label(new_instrument,text=FileIO.GM_types[selected_instrument-1],font=helv12,bg='white')

    lbl_range_p_d = Label(new_instrument,text="Range:",font=helv12b, bg='white')
    lbl_range_p = Label(new_instrument,text=FileIO.get_name(FileIO.GM_Ranges_Possible[selected_instrument-1][0])+" - "+FileIO.get_name(FileIO.GM_Ranges_Possible[selected_instrument-1][1]),font=helv12,bg='white')

    lbl_grouped_d = Label(new_instrument,text="Grouped With:",font=helv12b, bg='white')
    lbl_grouped = Label(new_instrument,text=FileIO.get_grouped_with(selected_instrument-1),font=helv12,bg='white')

    lbl_replaces_d = Label(new_instrument,text="Can Substitute:",font=helv12b, bg='white')
    lbl_replaces = Label(new_instrument,text=FileIO.get_replaces(selected_instrument-1),font=helv12,bg='white')


    lbl_desc_d = Label(new_instrument,text="Description:",font=helv12b, bg='white')
    lbl_desc = Message(new_instrument,text=FileIO.GM_Description[selected_instrument-1],font=helv12,bg='white', width=200)

    btn_add_instrument = Button(new_instrument,image=green_plus, text="  Select Instrument  ",compound=LEFT, relief='groove',bg='white', font=helv12, command=listbox_doubleclick)


    right_half_elements = []
    right_half_elements.append(lbl_instrument_name)
    right_half_elements.append(lbl_instrument)
    right_half_elements.append(btn_play_now)
    right_half_elements.append(lbl_type_d)
    right_half_elements.append(lbl_type)

    right_half_elements.append(lbl_range_p_d)
    right_half_elements.append(lbl_range_p)
    right_half_elements.append(lbl_grouped_d)
    right_half_elements.append(lbl_grouped)
    right_half_elements.append(lbl_replaces_d)
    right_half_elements.append(lbl_replaces)
    right_half_elements.append(lbl_desc_d)
    right_half_elements.append(lbl_desc)

    def listbox_changed(event):
        global selected_instrument
        global right_half_elements
        global photo_image


        #Get real index of instrument
        bar_list = [8,17,26,34,43,52,61,70,79,88,97,106]
        index = int(event.widget.curselection()[0])
        real_index = index
        for x in bar_list:
            if x <= index:
                real_index -= 1
        for x in FileIO.not_supported:
            if x-1 <= real_index:
                real_index += 1
        if (index in bar_list):return

        #Display instrument's info on right side
        #play_intro(real_index)#
        selected_instrument = real_index + 1

        lbl_instrument_name = Message(new_instrument,text=FileIO.GM_names[real_index],font=helv20,bg='white', width=180)
        right_half_elements[0] = lbl_instrument_name

        photo_image = PhotoImage(file="icons/instruments/"+str(real_index+1)+".png").subsample(6)
        lbl_instrument = Label(new_instrument,image=photo_image,borderwidth="0",highlightthickness="0",bg="white")
        right_half_elements[1] = lbl_instrument

        right_half_elements[4].config(text=FileIO.GM_types[selected_instrument-1])
        right_half_elements[6].config(text=FileIO.get_name(FileIO.GM_Ranges_Possible[selected_instrument-1][0])+" - "+FileIO.get_name(FileIO.GM_Ranges_Possible[selected_instrument-1][1]))
        right_half_elements[8].config(text=FileIO.get_grouped_with(selected_instrument-1))
        right_half_elements[10].config(text=FileIO.get_replaces(selected_instrument-1))
        right_half_elements[12].config(text=FileIO.GM_Description[selected_instrument-1])

        right_half_elements[0].grid(row=0,column=2,columnspan=2,sticky=N+E+W+S)
        right_half_elements[1].grid(row=0,column=4,sticky=N+E+W+S)
        right_half_elements[2].grid(row=0,column=5)



    listbox = Listbox(new_instrument, font=helv12, relief='groove',activestyle='none',yscrollcommand=scrollbar.set)
    listbox.grid(row=0,column=0,columnspan=1,rowspan=10,sticky=N+E+W+S)#pack(side='left',expand='yes',fill='y')#


    bar_list = [8,16,24,32,40,48,56,64,72,80,88,96,104] #Separators
    for i,instrument in enumerate(FileIO.GM_names):
        if i+1 in FileIO.not_supported:
            continue
        if i in bar_list:
            listbox.insert(END,"------")
        listbox.insert(END, instrument)
    listbox.bind("<<ListboxSelect>>",listbox_changed)
    listbox.bind("<Double-Button-1>", listbox_doubleclick)
    scrollbar.config(command=listbox.yview)
    scrollbar.grid(row=0, column=1,rowspan=10,sticky=N+W+S)#pack(side='left')#
    listbox.selection_set(0)

    right_half_elements[0].grid(row=0,column=2,columnspan=2,sticky=N+E+W+S)

    right_half_elements[1].grid(row=0,column=4,sticky=N+E+W+S)
    right_half_elements[2].grid(row=0,column=5)

    right_half_elements[3].grid(row=1,column=2,sticky=W)
    right_half_elements[4].grid(row=1,column=3, columnspan=3,sticky=W)

    right_half_elements[5].grid(row=2,column=2,sticky=W)
    right_half_elements[6].grid(row=2,column=3, columnspan=3,sticky=W)

    right_half_elements[7].grid(row=3,column=2,sticky=W)
    right_half_elements[8].grid(row=3,column=3, columnspan=3,sticky=W)

    right_half_elements[9].grid(row=4,column=2,sticky=W)
    right_half_elements[10].grid(row=4,column=3, columnspan=3,sticky=W)

    right_half_elements[11].grid(row=5,column=2,sticky=N+W)
    right_half_elements[12].grid(row=5,column=3, columnspan=3,rowspan=3,sticky=N+W)
    btn_add_instrument.grid(row=8,column=2, columnspan=3)

    Grid.rowconfigure(new_instrument,0, weight=4, uniform='a')
    Grid.rowconfigure(new_instrument,1, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,2, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,3, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,4, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,5, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,6, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,7, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,8, weight=1, uniform='a')
    Grid.rowconfigure(new_instrument,9, weight=1, uniform='a')
    Grid.columnconfigure(new_instrument,0, weight=12, uniform='a')
    Grid.columnconfigure(new_instrument,1, weight=1, uniform='a')
    Grid.columnconfigure(new_instrument,2, weight=6, uniform='a')
    Grid.columnconfigure(new_instrument,3, weight=3, uniform='a')
    Grid.columnconfigure(new_instrument,4, weight=6, uniform='a')
    Grid.columnconfigure(new_instrument,5, weight=2, uniform='a')
    Grid.columnconfigure(new_instrument,6, weight=1, uniform='a')

    new_instrument.mainloop()

####################################################################################################################################################
tones = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
list_string = []
for x in range(0,10):
    for y in range(0,12):
        list_string.append(tones[y]+str(x))

selection_list = []
tk_piano_normal = BooleanVar()
tk_arpeggio = BooleanVar()
tk_melody = BooleanVar()
def add_piano_instrument(selected_instrument=1,guitar_settings=[],preset=[],preset_index=-1):
    print (selected_instrument)
    print(preset)
    print(preset_index)
    
    global list_string
    global all_tracks_list
    global new_instrument
    global selection_list
    if preset != []:
        selection_list = copy.copy(preset[5])

    def do_destroy():
        global playthread
        if playthread != None:
            playthread.exit_flag = True
        playthread = None
        new_piano.destroy()

    new_piano = Toplevel(root, bg='white')
    new_piano.grab_set()
    new_piano.title(PROGRAM_NAME+" - Configure "+FileIO.GM_names[selected_instrument-1])
    new_piano.protocol('WM_DELETE_WINDOW', do_destroy)
    
    add_height = 0
    if guitar_settings == []: add_height += 120
    new_piano.geometry('440x'+str(400+add_height)+'+250+150')
    new_piano.resizable(False, False)
    new_piano.transient(root)
    new_piano.focus_force()
    
    def listbox_changed(event):
        global selection_list
        indices = (event.widget.curselection())
        selection_list = list(indices)

    def cb_changed(event):
        global selection_list
        for x in selection_list:
                listbox.select_set(x)

    def clicked_normal(event=None):
        if tk_piano_normal.get():
            listbox.config(state='disabled')
        else:
            listbox.config(state='normal')


    frm_listbox = Frame(new_piano,bg='white')
    scrollbar = ttk.Scrollbar(frm_listbox, orient=VERTICAL)
    listbox = Listbox(frm_listbox, font=helv12, relief='groove',activestyle='none',yscrollcommand=scrollbar.set, selectmode='multiple')
    listbox.bind("<<ListboxSelect>>",listbox_changed)
    for track in all_tracks_list:
        listbox.insert(END, track)
    scrollbar.config(command=listbox.yview)

    def save_piano(event=None):
        global new_instrument
        global instruments_list
        global selection_list
        #global selected_instrument

        if len(selection_list) == 0 and tk_piano_normal.get() == False:
            tkinter.messagebox.showinfo(
                "Adding New Instrument",
                "Please choose the tracks this instrument should combine and play -\nor you can choose to treat it as part of the ensemble!"
            )
            return
        _new = []
    
        _new.append(selected_instrument)
        _new.append(tk_piano_normal.get())
        if guitar_settings == []:
            _new.append(int(cb_simul.get()))
            _new.append(tk_arpeggio.get())
        else:
            _new.append(int(guitar_settings[5]))
            _new.append(False)
        _ranges = []
        _ranges.append(cb_string1.current()+12)
        _ranges.append(cb_string2.current()+12)
        
        
        _new.append(_ranges)#FileIO.GM_Ranges_Possible[selected_instrument-1])
        _new.append(selection_list)

        _new.append(guitar_settings)
        

        if preset_index == -1:
            instruments_list.append(_new)
            if tk_melody.get():
                if not len(instruments_list)-1 in FileIO.who_plays_melody: FileIO.who_plays_melody.append(len(instruments_list)-1)
            else:
                if len(instruments_list)-1 in FileIO.who_plays_melody: FileIO.who_plays_melody.remove(len(instruments_list)-1)
        else:
            instruments_list[preset_index] = _new
            if tk_melody.get():
                if not preset_index in FileIO.who_plays_melody: FileIO.who_plays_melody.append(preset_index)
            else:
                if preset_index in FileIO.who_plays_melody: FileIO.who_plays_melody.remove(preset_index)
       
        print (FileIO.who_plays_melody)
        selection_list = []

        update_instruments()
        if not new_instrument is None: new_instrument.destroy()
        new_piano.destroy()
        tk_arpeggio.set(False)
        tk_melody.set(False)
        

    lbl_info1 = Label (new_piano,text="Choose which tracks this instrument should combine:", bg='white',font=helv12)
    lbl_info2 = Label (new_piano,text="OR", bg='white',font=helv12b)
    tk_piano_normal.set(True)
    ch_normal = Checkbutton(new_piano, bg='white', variable=tk_piano_normal, command=clicked_normal, text="Treat as ensemble instrument",font=helv12,justify=LEFT)
    clicked_normal()

    ch_melody = Checkbutton(new_piano, bg='white', variable=tk_melody, text="Play melody on this instrument",font=helv12, justify=LEFT)


    frm_simul = Frame(new_piano,bg='white')
    lbl_simul = Label(frm_simul,text="Maximum\n simultaneous tones: ",bg='white',font=helv12)
    cb_simul = ttk.Combobox(frm_simul,values=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],font=helv12,width=3)
    cb_simul.current(0)
    cb_simul.bind("<<ComboboxSelected>>",cb_changed)
    

    ch_arpeggio = Checkbutton(new_piano, bg='white', variable=tk_arpeggio, text="Create arpeggios for remaining tones",font=helv12, justify=LEFT)


    btn_ok = Button (new_piano,text="OK",command=save_piano,bg='white', font=helv12, width = 20)


    ch_normal.pack(side='top')
    lbl_info2.pack(side='top')
    lbl_info1.pack(side='top',pady=5)
    listbox.pack(side='left',expand='yes')
    scrollbar.pack(side='left', expand='yes',fill=BOTH)
    frm_listbox.pack(side='top',pady=10)
    ch_melody.pack(side='top')
    
    if guitar_settings == []:
        lbl_simul.pack(side='left')
        cb_simul.pack(side='left')
        frm_simul.pack(side='top')
        ch_arpeggio.pack(side='top',pady=10)
    
    
    def range_selected(which,temp):
        note = 0
        if which == 0:
            note = cb_string1.current()+12
        else:
            note = cb_string2.current()+12
        FileIO.create_single_tone(selected_instrument-1,note)
        playthread = PlaybackThread(1,"Thread","_temp")
        playthread.exit_flag = False
        playthread.start()
            
    
    frm_range = Frame(new_piano)

    Label(frm_range,text="Range: ",bg='white', font=helv12).pack(side='left')
    cb_string1 = ttk.Combobox(frm_range,values=list_string,state='readonly',font=helv12, width=4)
    cb_string2 = ttk.Combobox(frm_range,values=list_string,state='readonly',font=helv12, width=4)
    
    cb_string1.pack(side='left')
    Label(frm_range,text="-",font=helv12b, bg='white').pack(side='left',padx=3)
    cb_string2.pack(side='left')
    
    cb_string1.current(FileIO.GM_Ranges_Possible[selected_instrument-1][0]-12)
    cb_string2.current(FileIO.GM_Ranges_Possible[selected_instrument-1][1]-12)
    cb_string1.bind("<<ComboboxSelected>>",partial(range_selected,0))
    cb_string2.bind("<<ComboboxSelected>>",partial(range_selected,1))
    

    
    #FileIO.GM_Ranges_Possible[instrument[0]-1][0]
    if guitar_settings == []:
        frm_range.pack(side='top',pady=5)
        
    btn_ok.pack(side='top', pady=10)
    
    #If editing settings
    if preset != []:
        if preset[1] == False: #combining groups
            tk_piano_normal.set(False)
            listbox.config(state='normal')
            for x in preset[5]:
                listbox.select_set(x)
            
        cb_simul.current(preset[2]-1)
        tk_arpeggio.set(preset[3])
        cb_string1.current(preset[4][0]-12)
        cb_string2.current(preset[4][1]-12)
        
    
    new_piano.mainloop()


####################################################################################################################################################

guitar_strings = [40,45,50,55,59,64,-100]
string_amount = 6
def add_guitar_instrument(selected_instrument=1,preset=[],preset_index = -1):
    global all_tracks_list
    global new_instrument
    global guitar_strings
    global list_string



    def do_destroy():
        global playthread
        if playthread != None:
            playthread.exit_flag = True
        playthread = None
        new_guitar.destroy()

    def save_guitar():
        #Build Guitar Settings [patch,strings,[base tones top-down],highest fret,hand-with,same time tones]
        global selected_instrument
        global string_amount
        guitar_strings[0] = cb_string1.current()+12
        guitar_strings[1] = cb_string2.current()+12
        guitar_strings[2] = cb_string3.current()+12
        guitar_strings[3] = cb_string4.current()+12
        if int(string_amount) >= 5:
            guitar_strings[4] = cb_string5.current()+12
        else: guitar_strings[4] = -100
        if int(string_amount) >= 6:
            guitar_strings[5] = cb_string6.current()+12
        else: guitar_strings[5] = -100
        if int(string_amount) >= 7:
            guitar_strings[5] = cb_string7.current()+12
        else: guitar_strings[5] = -100
     

        capo = int(cb_capo.get())

        if capo >= int(cb_frets.get()):
            tkinter.messagebox.showwarning(
                    "String Instrument Settings",
                    "The capo can't be higher than the amount of frets!"
                )
            return

        _s = []
        _s.append(selected_instrument)
        _s.append(string_amount)
        _strings = []

        for s in range (len(guitar_strings)-1,-1,-1):
            if guitar_strings[s] == -100: continue

            _strings.append(int(guitar_strings[s])+int(capo))
        _s.append(_strings)
        _s.append(int(cb_frets.get())-capo)
        _s.append(int(cb_hand_width.get()))
        _s.append(int(cb_simul.get()))
        _s.append(int(cb_capo.get()))
        new_guitar.destroy()
        add_piano_instrument(selected_instrument,copy.copy(_s),preset=preset,preset_index = preset_index)






    def preset_selected(code=0):
        global guitar_strings
        global string_amount

        new_fret = 12
        simul = 5

        #Acoustic Guitar / Electric Guitar
        if code == 11 or code == 21: guitar_strings = [40,45,50,55,59,64,-100] #Turn it around when giving it to the midi_brain_guitar
        if code == 12 or code == 22: guitar_strings = [39,44,49,54,58,63,-100]
        if code == 13 or code == 23: guitar_strings = [38,43,48,53,57,62,-100]
        if code == 14 or code == 24: guitar_strings = [36,43,48,53,57,62,-100]
        if code == 15 or code == 25: guitar_strings = [38,45,50,55,59,64,-100]
        if code == 16 or code == 26: guitar_strings = [38,45,50,55,59,62,-100]
        if code == 17 or code == 27: guitar_strings = [38,47,50,55,59,62,-100]
        if code == 18 or code == 28: guitar_strings = [64,59,55,50,45,40,-100]


        #Bass Guitar
        if code == 31: guitar_strings = [28,33,38,43,-100,-100,-100]
        if code == 32: guitar_strings = [27,32,37,42,-100,-100,-100]
        if code == 33: guitar_strings = [26,31,36,41,-100,-100,-100]
        if code == 34: guitar_strings = [26,33,38,43,-100,-100,-100]
        if code == 35: guitar_strings = [43,38,33,28,-100,-100,-100]

        if code == 36: guitar_strings = [23,28,33,38,43,-100,-100]
        if code == 37: guitar_strings = [22,27,32,37,42,-100,-100]
        if code == 38: guitar_strings = [21,26,31,36,41,-100,-100]
        if code == 39: guitar_strings = [43,38,33,28,23,-100,-100]

        if code >= 21 and code <= 39:
            new_fret = 24
            simul = 1


        #Banjo
        if code == 41: guitar_strings = [36,43,50,57,-100,-100,-100]
        if code == 42: guitar_strings = [31,38,45,52,-100,-100,-100]
        if code == 43: guitar_strings = [38,43,47,52,-100,-100,-100]
        if code >= 41 and code <= 43:
            new_fret = 17
            simul = 4

        if code == 44: guitar_strings = [67,50,55,59,62,-100,-100]
        if code == 45: guitar_strings = [67,48,55,59,62,-100,-100]
        if code == 46: guitar_strings = [67,48,55,60,62,-100,-100]
        if code == 47: guitar_strings = [67,50,55,60,62,-100,-100]
        if code >= 44 and code <= 47:
            new_fret = 22
            simul = 4

        #Ukulele
        if code == 51: guitar_strings = [67,60,64,69,-100,-100,-100]
        if code == 52: guitar_strings = [69,62,66,71,-100,-100,-100]
        if code == 53: guitar_strings = [55,60,64,69,-100,-100,-100]
        if code >= 51 and code <= 53:
            simul = 4

        cb_frets.current(new_fret-5)

        cb_string1.current(guitar_strings[0]-12)
        cb_string2.current(guitar_strings[1]-12)
        cb_string3.current(guitar_strings[2]-12)
        cb_string4.current(guitar_strings[3]-12)
        cb_string5.config(state='readonly')
        cb_string6.config(state='readonly')
        cb_string7.config(state='readonly')

        if guitar_strings[6] != -100:
            cb_string7.current(guitar_strings[6]-12)
        else:
            cb_string7.config(state='disabled')
            cb_string7.set('')
            string_amount = 6
        if guitar_strings[5] != -100:
            cb_string6.current(guitar_strings[5]-12)
        else:
            cb_string6.config(state='disabled')
            cb_string6.set('')
            string_amount = 5
        if guitar_strings[4] != -100:
            cb_string5.current(guitar_strings[4]-12)
        else:
            cb_string5.config(state='disabled')
            cb_string5.set('')
            string_amount = 4
        cb_strings.current(string_amount-4)

        cb_simul.current(simul-1)

    def strings_selected(event=None):
        global string_amount

        if int(cb_strings.get()) <= 6:  cb_string7.config(state='disabled'); cb_string7.set('')
        if int(cb_strings.get()) <= 5:  cb_string6.config(state='disabled'); cb_string6.set('')
        if int(cb_strings.get()) <= 4:  cb_string5.config(state='disabled'); cb_string5.set('')
        if int(cb_strings.get()) >= 5 and int(string_amount) < 5: cb_string5.config(state='readonly'); cb_string5.current(cb_string4.current())
        if int(cb_strings.get()) >= 6 and int(string_amount) < 6: cb_string6.config(state='readonly'); cb_string6.current(cb_string5.current())
        if int(cb_strings.get()) >= 7 and int(string_amount) < 7: cb_string7.config(state='readonly'); cb_string7.current(cb_string6.current())


        string_amount = int(cb_strings.get())







    new_guitar = Toplevel(root, bg='white')
    new_guitar.grab_set()
    new_guitar.title(PROGRAM_NAME+" - Configure String Instrument")
    new_guitar.protocol('WM_DELETE_WINDOW', do_destroy)

    new_guitar.geometry('440x220+250+250')
    new_guitar.resizable(False, False)
    new_guitar.transient(root)
    new_guitar.focus_force()

    menu_bar = Menu(new_guitar, bg='white',font=helv20)
    instruments_menu = Menu(menu_bar, tearoff=0, bg='white')
    menu_bar.add_cascade(label='Presets...', menu=instruments_menu)
    acoustic_guitar_menu = Menu(instruments_menu,tearoff=0, bg='white')
    instruments_menu.add_cascade(label="Acoustic Guitar", menu=acoustic_guitar_menu)
    acoustic_guitar_menu.add_command(label="Standard Tuning - E A D G B E", command=lambda:preset_selected(11))
    acoustic_guitar_menu.add_command(label="Half Note Tuned Down - Eb Ab Db Gb Bb Eb", command=lambda:preset_selected(12))
    acoustic_guitar_menu.add_command(label="Full Note Tuned Down - D G C F A D", command=lambda:preset_selected(13))
    acoustic_guitar_menu.add_command(label="Dropped C - C G C F A D", command=lambda:preset_selected(14))
    acoustic_guitar_menu.add_command(label="Dropped D - D A D G B E", command=lambda:preset_selected(15))
    acoustic_guitar_menu.add_command(label="Double Dropped D - D A D G B D", command=lambda:preset_selected(16))
    acoustic_guitar_menu.add_command(label="Open G Tuning - D B D G B D", command=lambda:preset_selected(17))
    acoustic_guitar_menu.add_command(label="Reverse / Left-Hand - E B G D A E", command=lambda:preset_selected(18))
    electric_guitar_menu = Menu(instruments_menu, tearoff=0, bg='white')
    instruments_menu.add_cascade(label="Electric Guitar", menu=electric_guitar_menu)
    electric_guitar_menu.add_command(label="Standard Tuning - E A D G B E", command=lambda:preset_selected(21))
    electric_guitar_menu.add_command(label="Half Note Tuned Down - Eb Ab Db Gb Bb Eb", command=lambda:preset_selected(22))
    electric_guitar_menu.add_command(label="Full Note Tuned Down - D G C F A D", command=lambda:preset_selected(23))
    electric_guitar_menu.add_command(label="Dropped C - C G C F A D", command=lambda:preset_selected(24))
    electric_guitar_menu.add_command(label="Dropped D - D A D G B E", command=lambda:preset_selected(25))
    electric_guitar_menu.add_command(label="Double Dropped D - D A D G B D", command=lambda:preset_selected(26))
    electric_guitar_menu.add_command(label="Open G Tuning - D B D G B D", command=lambda:preset_selected(27))
    electric_guitar_menu.add_command(label="Reverse / Left-Hand - E B G D A E", command=lambda:preset_selected(28))
    bass_guitar_menu = Menu(instruments_menu, tearoff=0, bg='white')
    instruments_menu.add_cascade(label="Bass",menu=bass_guitar_menu)
    bass_guitar_menu.add_command(label="4 Strings - Standard Tuning - E A D G", command=lambda:preset_selected(31))
    bass_guitar_menu.add_command(label="4 Strings - Half Note Tuned Down - Eb Ab Db Gb", command=lambda:preset_selected(32))
    bass_guitar_menu.add_command(label="4 Strings - Full Note Tuned Down - D G C F", command=lambda:preset_selected(33))
    bass_guitar_menu.add_command(label="4 Strings - Dropped D - D A D G", command=lambda:preset_selected(34))
    bass_guitar_menu.add_command(label="4 Strings - Reverse / Left-Hand - G D A E", command=lambda:preset_selected(35))
    bass_guitar_menu.add_separator()
    bass_guitar_menu.add_command(label="5 Strings - Standard Tuning - B E A D G", command=lambda:preset_selected(36))
    bass_guitar_menu.add_command(label="5 Strings - Half Note Tuned Down - Bb Eb Ab Db Gb", command=lambda:preset_selected(37))
    bass_guitar_menu.add_command(label="5 Strings - Full Note Tuned Down - A D G C F", command=lambda:preset_selected(38))
    bass_guitar_menu.add_command(label="5 Strings - Reverse / Left-Hand - G D A E B", command=lambda:preset_selected(39))
    banjo_menu = Menu(instruments_menu, tearoff=0, bg='white')
    instruments_menu.add_cascade(label="Banjo", menu=banjo_menu)
    banjo_menu.add_command(label="4 Strings - Tenor - C G D A", command=lambda:preset_selected(41))
    banjo_menu.add_command(label="4 Strings - Irish Tenor - G D A E", command=lambda:preset_selected(42))
    banjo_menu.add_command(label="4 Strings - Chicago Tenor - D G B E", command=lambda:preset_selected(43))
    banjo_menu.add_separator()
    banjo_menu.add_command(label="5 Strings - Standard - G D G B D", command=lambda:preset_selected(44))
    banjo_menu.add_command(label="5 Strings - Dropped C - G C G B D", command=lambda:preset_selected(45))
    banjo_menu.add_command(label="5 Strings - Double C - G C G C D", command=lambda:preset_selected(46))
    banjo_menu.add_command(label="5 Strings - G Modal - G D G C D", command=lambda:preset_selected(47))
    ukulele_menu = Menu(instruments_menu, tearoff=0, bg='white')
    instruments_menu.add_cascade(label='Ukulele',menu=ukulele_menu)
    ukulele_menu.add_command(label="Standard C - G C E A", command=lambda:preset_selected(51))
    ukulele_menu.add_command(label="Standard D - A D Gb B", command=lambda:preset_selected(52))
    ukulele_menu.add_command(label="Low G - G C E A", command=lambda:preset_selected(53))
    ukulele_menu.add_command(label="Reverse / Left-Hand - A E C G", command=lambda:preset_selected(54))







    new_guitar.config(menu=menu_bar)

    

    frm_top = Frame(new_guitar)

    cb_string1 = ttk.Combobox(frm_top,values=list_string,state='readonly',font=helv12, width=4)
    cb_string2 = ttk.Combobox(frm_top,values=list_string,state='readonly',font=helv12, width=4)
    cb_string3 = ttk.Combobox(frm_top,values=list_string,state='readonly',font=helv12, width=4)
    cb_string4 = ttk.Combobox(frm_top,values=list_string,state='readonly',font=helv12, width=4)
    cb_string5 = ttk.Combobox(frm_top,values=list_string,state='readonly',font=helv12, width=4)
    cb_string6 = ttk.Combobox(frm_top,values=list_string,state='readonly',font=helv12, width=4)
    cb_string7 = ttk.Combobox(frm_top,values=list_string,state='disabled',font=helv12, width=4)

    cb_string1.current(40+12)
    cb_string2.current(45+12)
    cb_string3.current(50+12)
    cb_string4.current(55+12)
    cb_string5.current(59+12)
    cb_string6.current(64+12)#40,45,50,55,59,64

    cb_string1.pack(side='left')
    cb_string2.pack(side='left')
    cb_string3.pack(side='left')
    cb_string4.pack(side='left')
    cb_string5.pack(side='left')
    cb_string6.pack(side='left')
    cb_string7.pack(side='left')
    frm_top.pack(side='top',padx=10,pady=10)

    frm_below=Frame(new_guitar,bg='white')
    lbl_strings = Label(frm_below,text="Strings: ",bg='white',font=helv12)
    cb_strings = ttk.Combobox(frm_below, values=[4,5,6,7],state='readonly',font=helv12, width=3)
    cb_strings.current(2)
    cb_strings.bind("<<ComboboxSelected>>",strings_selected)

    lbl_strings.grid(row=0, column=0, sticky=W)
    cb_strings.grid(row=0, column=1, sticky=W)


    lbl_frets = Label(frm_below,text="     Frets: ",bg='white',font=helv12)
    cb_frets = ttk.Combobox(frm_below, state='readonly', values=[5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36],font=helv12, width=3)
    cb_frets.current(7)

    lbl_frets.grid(row=0, column=2, sticky=W)
    cb_frets.grid(row=0, column=3, sticky=W)

    lbl_hand_width = Label(frm_below,text="     Hand Width: ",bg='white',font=helv12)
    cb_hand_width = ttk.Combobox(frm_below, values=[2,3,4,5,6],font=helv12, width=3)
    cb_hand_width.current(1)

    lbl_hand_width.grid(row=1, column=2, sticky=W)
    cb_hand_width.grid(row=1, column=3, sticky=W)

    lbl_capo = Label(frm_below,text="Capo: ",bg='white',font=helv12)
    cb_capo = ttk.Combobox(frm_below, values=[0,1,2,3,4,5,6,7,8,9,10,11,12],font=helv12, width=3)
    cb_capo.current(0)

    lbl_capo.grid(row=1, column=0, sticky=W)
    cb_capo.grid(row=1, column=1, sticky=W)

    lbl_simul = Label(frm_below,text="Maximum\n simultaneous tones: ",bg='white',font=helv12)
    cb_simul = ttk.Combobox(frm_below,values=[1,2,3,4,5],font=helv12,width=3)
    cb_simul.current(4)

    lbl_simul.grid(row=2,column=0,columnspan=2,sticky=W)
    cb_simul.grid(row=2,column=2,sticky=W)



    frm_below.pack(side='top', fill=BOTH, expand='yes', padx=10, pady=10)
    btn_ok = Button (new_guitar,text="OK",command=save_guitar,bg='white', font=helv12, width = 20).pack(side='top', pady=15)

    #Select the presets according to midi instrument
    if selected_instrument == 25 or selected_instrument == 26: preset_selected(11) #Acoustic Guitar
    if selected_instrument >= 27 and selected_instrument <= 31: preset_selected(21) #Electric Guitar
    if selected_instrument >= 33 and selected_instrument <= 40: preset_selected(31) #Bass
    if selected_instrument == 106: preset_selected(44)

    #Changing existing instrument
    if preset != []:
        gs = preset[6]
        cb_strings.current(gs[1]-4)
        strings_selected()
        cb_frets.current(gs[3]-5+gs[6]) #+ capo amount
        cb_capo.current(gs[6])
        cb_hand_width.current(gs[4]-2)
        cb_simul.current(gs[5]-1)
        cb_string1.current(gs[2][-1]-12-gs[6])
        cb_string2.current(gs[2][-2]-12-gs[6])
        cb_string3.current(gs[2][-3]-12-gs[6])
        cb_string4.current(gs[2][-4]-12-gs[6])
        if (len(gs[2])>=5): cb_string5.current(gs[2][-5]-12-gs[6])
        if (len(gs[2])>=6): cb_string6.current(gs[2][-6]-12-gs[6])
        if (len(gs[2])>=7): cb_string7.current(gs[2][-7]-12-gs[6])


    new_guitar.mainloop()



####################################################################################################################################################
#Icons
new_file_icon = PhotoImage(file='icons/new_file.gif')
open_file_icon = PhotoImage(file='icons/open_file.gif')
open_file_icon_large = PhotoImage(file='icons/open_file_large.gif')
save_file_icon = PhotoImage(file='icons/save.gif')
about_icon = PhotoImage(file='icons/about.gif')
green_plus = PhotoImage(file='icons/green_plus.png')
red_x = PhotoImage(file='icons/red_x.png')
up_arrow = PhotoImage(file='icons/up_arrow.png').subsample(2)
down_arrow = PhotoImage(file='icons/down_arrow.png').subsample(2)


#########
#Fonts  #
#########
helv12 = font.Font(family="Helvetica",size=12)
helv12b = font.Font(family="Helvetica",size=13,weight="bold")
helv10u = font.Font(family="Helvetica",size=12,underline=True)
cour10 = font.Font(family="Courier New",size=10)

#Menu Bar
def apply_preset(index=0,is_custom=False):
    FileIO.who_plays_melody = []
    global instruments_list
    if not is_custom: 
        if index==0: #PC Speaker
            instruments_list = [[81,True,1,True,[24,100],[],[]]]
        if index==1: #8-Bit Sound
            instruments_list = [[81, True, 1, True, [24, 100], [], []],
                                [81, True, 1, True, [24, 100], [], []],
                                [82, True, 1, True, [24, 100], [], []]]
        if index==2: #Chiptune
            instruments_list = [[81, True, 1, True, [24, 100], [], []],
                                [82, True, 1, True, [24, 100], [], []],
                                [80, True, 1, True, [24, 100], [], []]]
        if index==3: #Choir
            instruments_list = [[53, True, 1, False, [60, 84], [], []],
                                [53, True, 1, False, [53, 76], [], []],
                                [53, True, 1, False, [47, 69], [], []],
                                [53, True, 1, False, [40, 64], [], []]]
        if index==4: #Rock Band
            instruments_list = [[53, True, 1, False, [40, 69], [], []],
                                [28, True, 4, False, [40, 83], [], [28, 6, [59, 55, 50, 45, 40], 24, 3, 4, 0]],
                                [35, True, 1, False, [28, 67], [], [35, 4, [43, 38, 33, 28], 24, 3, 1, 0]]]    
        if index==5: #Woodwind Quartet
            instruments_list = [[74, True, 1, False, [60, 96], [], []], [69, True, 1, False, [59, 89], [], []], [72, True, 1, False, [50, 95], [], []], [71, True, 1, False, [34, 76], [], []]]
        if index==6: #Woodwind Quintet
            instruments_list = [[74, True, 1, False, [60, 96], [], []], [69, True, 1, False, [59, 89], [], []], [72, True, 1, False, [50, 95], [], []], [71, True, 1, False, [34, 76], [], []],[61, True, 1, False, [29, 77], [], []]]
        if index==7: #DEBUG
            instruments_list = [[41, True, 1, False, [55, 84], [], []], [41, True, 1, False, [55, 84], [], []]]
        if index==8: #DEBUG
            instruments_list = [[41, True, 1, False, [55, 84], [], []], [43, True, 1, False, [36, 55], [], []]]
        if index==17: #String Quartet
            instruments_list = [[41, True, 1, False, [55, 84], [], []],[41, True, 1, False, [55, 84], [], []],[42, True, 1, False, [48, 77], [], []], [43, True, 1, False, [36, 55], [], []]]
            
        update_instruments()

menu_bar = Menu(root)

file_menu = Menu(menu_bar, tearoff=0)
file_menu.config(bg='white')
file_menu.add_command(label='New Project', accelerator='Ctrl+N',
                      compound='left', image=new_file_icon, underline=0)
file_menu.add_command(label='Open MIDI File', accelerator='Ctrl+O',
                      compound='left', image=open_file_icon, underline=0, command=open_midi_file)
file_menu.add_separator()
file_menu.add_command(label='Exit', accelerator='Alt+F4', underline=1, command=end_program)
menu_bar.add_cascade(label='File', menu=file_menu)

presets_menu = Menu(menu_bar, tearoff=0)
presets_menu.config(bg='white')
presets_menu.add_command(label="Save Current Settings...",compound='left', image=save_file_icon, underline=0)
load_preset_menu = Menu(presets_menu, tearoff=0)
load_preset_menu.add_command(label='My Preset 1')
load_preset_menu.add_command(label='My Preset 2')
load_preset_menu.add_separator()
load_preset_menu.add_command(label='PC Speaker / Mobile Ringtone',command=partial(apply_preset,0,False))
load_preset_menu.add_command(label='8-Bit Sound',command=partial(apply_preset,1,False))
load_preset_menu.add_command(label='Chiptune',command=partial(apply_preset,2,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Choir',command=partial(apply_preset,3,False))
load_preset_menu.add_command(label='Rock Band',command=partial(apply_preset,4,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Woodwind Quartet',command=partial(apply_preset,5,False))
load_preset_menu.add_command(label='Woodwind Quintet',command=partial(apply_preset,6,False))
load_preset_menu.add_command(label='Saxophone Quartet',command=partial(apply_preset,7,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Brass Trio',command=partial(apply_preset,8,False))
load_preset_menu.add_command(label='Brass Quartet',command=partial(apply_preset,9,False))
load_preset_menu.add_command(label='Brass Quintet',command=partial(apply_preset,10,False))
load_preset_menu.add_command(label='Brass Sextet',command=partial(apply_preset,11,False))
load_preset_menu.add_command(label='Horn Quartet',command=partial(apply_preset,12,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Solo Violin',command=partial(apply_preset,13,False))
load_preset_menu.add_command(label='Piano Trio',command=partial(apply_preset,14,False))
load_preset_menu.add_command(label='String Trio',command=partial(apply_preset,15,False))
load_preset_menu.add_command(label='Piano Quartet',command=partial(apply_preset,16,False))
load_preset_menu.add_command(label='String Quartet',command=partial(apply_preset,17,False))
load_preset_menu.add_command(label='Piano Quintet',command=partial(apply_preset,18,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Baroque Trio',command=partial(apply_preset,19,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Chamber Orchestra',command=partial(apply_preset,20,False))
load_preset_menu.add_command(label='Symphony Orchestra',command=partial(apply_preset,21,False))
load_preset_menu.add_separator()
load_preset_menu.add_command(label='Japanese Trio',command=partial(apply_preset,22,False))



#load_preset_menu.add_command(label='Big Band',command=partial(apply_preset,1,False))
#load_preset_menu.add_command(label='Gameboy',command=partial(apply_preset,2,False))
#load_preset_menu.add_command(label='PC Speaker')
load_preset_menu.config(bg='white')
presets_menu.add_cascade(label='Load Preset', menu=load_preset_menu)
presets_menu.add_command(label="Delete Preset(s)...",compound='left', image=red_x, underline=0)

menu_bar.add_cascade(label='Presets', menu=presets_menu)

help_menu = Menu(menu_bar, tearoff=0)
help_menu.add_command(label='Manual', accelerator='F1',compound='left',underline=0)
help_menu.add_command(label='About', image=about_icon, compound='left',underline=0)
help_menu.config(bg='white')
menu_bar.add_cascade(label='Help',menu=help_menu)
root.config(menu=menu_bar)



#########
#Frames #
#########
fra_midi_file = Frame(root, bg='white')
fra_selected_track = Frame(root,bg='white')
fra_keep_all_short = Frame(root,bg='white')
fra_duration = Frame(root,bg='white')
fra_a_duration = Frame(root,bg='white')

#########
#Labels #
#########
lbl_instruments = Label(text='Instruments', bg='white')
lbl_midi_file = Label(fra_midi_file, text='MIDI file:', bg='white',font=helv12)
lbl_midi_file_name = Message(fra_midi_file, textvariable=tk_input_file_name, bg='white',font=cour10, width=200)
lbl_selected_tracks = Label(fra_selected_track, text='Selected tracks:', bg='white',font=helv12)
lbl_selected_tracks_number = Message(fra_selected_track, textvariable=tk_selected, bg='white',font=cour10, width=200)
lbl_global_settings = Label (text="Global Settings:",bg='white',font=helv10u)
lbl_where_is_melody = Label(text='Melody location:', bg='white',font=helv12)
lbl_create_chords = Label(text='Create Additional Tones:', bg='white', font=helv12)
#lbl_too_many_tones = Message(text='Multiple tones in one instrument:', bg='white',font=helv12, width=500)
#lbl_arpeggio_duration = Label(text='Arpeggio length (1-8):', bg='white',font=helv12, state='disabled')
#lbl_keep_all_short = Label(fra_keep_all_short, text='Shorten all notes:', bg='white',font=helv12)#
#lbl_duration = Label(fra_duration, text='Short duration (1-8):', bg='white',font=helv12, state='disabled')
#lbl_too_few_tones = Label(text='Distributing tones:', bg='white',font=helv12)

#########
#Images #
#########
img_64th = PhotoImage(file='icons/64th.png')
lbl_img_64th = Label(fra_a_duration,image=img_64th,borderwidth="0",highlightthickness="0", bg='white',state='disabled')
lbl_img_64th_2 = Label(fra_duration,image=img_64th,borderwidth="0",highlightthickness="0", bg='white', state='disabled')

note = PhotoImage(file='icons/note.png')

#########
#Buttons#
#########
#def shorten_selected(event=None):
    #print (tk_keep_all_short.get())
#    if tk_keep_all_short.get():
#        lbl_duration.config(state='normal')
#        lbl_img_64th_2.config(state='normal')
#        cb_duration.config(state='normal')
#    else:
#        lbl_duration.config(state='disabled')
#        lbl_img_64th_2.config(state='disabled')
#        cb_duration.config(state='disabled')

def arrange_clicked(event=None):
    global instruments_list
    global notes
    settings_list = []
    settings_list.append(cb_where_is_melody.current())
    settings_list.append(tk_create_chords.get())
    arranged = arrange_midi(notes,instruments_list,settings_list)
    io.writeFile('aaa_output.mid',arranged)
    #io.writeTabsGPX('aaoutput.gp3',Create_Guitar.tabs,instruments_list[0][6])
    tkinter.messagebox.showinfo(
                    "aaa_output.mid",
                    "Export-Datei erstellt!"
                )

btn_open_midi = Button(fra_midi_file,image=open_file_icon_large, bg='white', relief='groove',command=lambda: open_midi_file(skip_file=False))
btn_select_track = Button(fra_selected_track,text="...",bg='white', relief='groove',font=helv12,command=lambda: open_midi_file(skip_file=True))
btn_add_new_instrument = Button(text='   Add New Instrument   ',image=green_plus, font=helv12, bg='white',compound=LEFT, command=add_new_instrument)
btn_arrange = Button(image=note, text=' Create ',font=helv20, bg='white', compound=LEFT, command=arrange_clicked)

#ch_keep_all_short = Checkbutton(fra_keep_all_short, bg='white', variable=tk_keep_all_short, command=shorten_selected)
ch_create_chords = Checkbutton(bg='white',variable=tk_create_chords)


###########
#Dropdowns#
###########
#def arpeggio_selected(event=None):
#    if cb_too_many_tones.current() == 1:
#        lbl_arpeggio_duration.config(state='normal')
#        lbl_img_64th.config(state='normal')
#        cb_a_duration.config(state='normal')
#    else:
#        lbl_arpeggio_duration.config(state='disabled')
#        lbl_img_64th.config(state='disabled')
#        cb_a_duration.config(state='disabled')



list_where_is_melody = ['Auto-Detect']
cb_where_is_melody = ttk.Combobox(values=list_where_is_melody, state='readonly',font=helv12)
cb_where_is_melody.current(0)
#

#list_too_many_tones = ['Keep all','Create Arpeggios']
#cb_too_many_tones = ttk.Combobox(values=list_too_many_tones, state='readonly',font=helv12)
#cb_too_many_tones.current(0)
#cb_too_many_tones.bind("<<ComboboxSelected>>",arpeggio_selected)

#list_too_few_tones = ['Alternate between groups','Duplicate notes']
#cb_too_few_tones = ttk.Combobox(values=list_too_few_tones, state='readonly', font=helv12)
#cb_too_few_tones.current(0)

#list_duration = [1,2,3,4,5,6,7,8]
#cb_duration = ttk.Combobox(fra_duration,values=list_duration,state='disabled',font=helv12, width=1)
#cb_duration.current(0)
#
#list_a_duration = [1,2,3,4,5,6,7,8]
#cb_a_duration = ttk.Combobox(fra_a_duration,values=list_a_duration,state='disabled',font=helv12, width=1)
#cb_a_duration.current(0)


#############
#ScrollFrame#
#############
def up_clicked(which):
    if which == 0: return
    instruments_list[which], instruments_list[which-1] = instruments_list[which-1], instruments_list[which]
    update_instruments()

def down_clicked(which):
    if which == len(instruments_list)-1: return
    instruments_list[which], instruments_list[which+1] = instruments_list[which+1], instruments_list[which]
    update_instruments()

def del_clicked(which):
    del instruments_list[which]
    update_instruments()

def settings_clicked(which):
    if input_file_name == "":
        tkinter.messagebox.showinfo(
                "Instrument Settings",
                "You need to select a MIDI file first!"
            )
        open_midi_file(skip_file=False)
        
        return
    
    if instruments_list[which][6] == []: #Not a guitar
        add_piano_instrument(selected_instrument=instruments_list[which][0], preset=instruments_list[which], preset_index = which)
    else:
        add_guitar_instrument(selected_instrument=instruments_list[which][0], preset=instruments_list[which], preset_index = which)


instruments_frame = Pmw.ScrolledFrame(root)
inner_frame = instruments_frame.interior()
def update_instruments():
    for widget in inner_frame.winfo_children():
        widget.destroy()
    for enin,instrument in enumerate(instruments_list):
        row = Frame(inner_frame,bg='white')
        _instrument_pic = PhotoImage(file="icons/instruments/"+(str(instrument[0])+".png")).subsample(12)

        _photo_field = Label(row,image=_instrument_pic,borderwidth="0",highlightthickness="0", bg='white')
        _photo_field.image = _instrument_pic # keep a reference!
        _photo_field.pack(side="left",padx=10)



        Button(row,image=red_x,bg='white',relief='groove', command=partial(del_clicked,enin)).pack(side='right',padx=5)

        frm_arrows = Frame(row,bg='white')
        Button(frm_arrows,image=up_arrow,bg='white',relief='groove', command=partial(up_clicked,enin)).pack(side='top')
        Button(frm_arrows,image=down_arrow,bg='white',relief='groove', command=partial(down_clicked,enin)).pack(side='bottom')
        frm_arrows.pack(side="right",padx=10)

        Button(row,text='Settings..', command=partial(settings_clicked,enin)).pack(side='right',padx=5)

        Label(row,text=FileIO.GM_names[instrument[0]-1],bg='white',font=helv12).pack(side="left",padx=5)
        if instrument[6] == []:
            Label(row,text=FileIO.get_name(instrument[4][0])+" - "+FileIO.get_name(instrument[4][1]),font=helv12b,bg='white').pack(side="right",padx=5)
        else:
            Label(row,text=FileIO.get_name(min(instrument[6][2]))+" - "+FileIO.get_name(max(instrument[6][2]) + instrument[6][3]),font=helv12b,bg='white').pack(side="right",padx=5)


        row.pack(side="top",pady=5, fill=X,expand='yes')
        ttk.Separator(inner_frame).pack(side="top",pady=3,fill=X,expand='yes')
        #Label(inner_frame,text="Alex").pack(side="top",pady=15)

#################
#Grid everything#
#################
lbl_instruments.grid(row=0,column=0,sticky=W)
instruments_frame.grid(row=1,column=0,columnspan=2,rowspan=9,sticky=N+E+S+W,padx=15)

lbl_midi_file.pack(side='left', padx=15)
lbl_midi_file_name.pack(side='left')
btn_open_midi.pack(side='left',padx=5)
fra_midi_file.grid(row=1,column=2,columnspan=2,sticky=W)


lbl_selected_tracks.pack(side='left', padx=15)
lbl_selected_tracks_number.pack(side='left')
btn_select_track.pack(side='left',padx=5)
fra_selected_track.grid(row=2,column=2,columnspan=2,sticky=W)

lbl_global_settings.grid(row=4,column=2, columnspan=2,sticky=S+W)

lbl_where_is_melody.grid(row=5,column=2,sticky=W, padx=15)
cb_where_is_melody.grid(row=5,column=3,sticky=W)

lbl_create_chords.grid(row=6,column=2,sticky=W, padx=15)
ch_create_chords.grid(row=6,column=3,sticky=W)


#lbl_too_many_tones.grid(row=6,column=2,sticky=W, padx=15)
#cb_too_many_tones.grid(row=6,column=3,sticky=W)

#lbl_arpeggio_duration.grid(row=7,column=2,sticky=W, padx=15)

#cb_a_duration.pack(side='left')
#lbl_img_64th.pack(side='left')
#fra_a_duration.grid(row=7,column=3,sticky=W)

#lbl_keep_all_short.pack(side='left')
#ch_keep_all_short.pack(side='left')
#fra_keep_all_short.grid(row=7,column=2,sticky=W,padx=15)

#lbl_duration.pack(side='left')
#cb_duration.pack(side='left')
#lbl_img_64th_2.pack(side='left')
#fra_duration.grid(row=7,column=3,sticky=W)

#lbl_too_few_tones.grid(row=8,column=2,sticky=W,padx=15)
#cb_too_few_tones.grid(row=8,column=3,sticky=W)

btn_add_new_instrument.grid(row=10,column=0,columnspan=2, sticky=N+E+W+S, padx=15)
btn_arrange.grid(row=11,column=0, rowspan=2,columnspan=4, sticky=N+E+W+S, padx=250,pady=15)

Grid.columnconfigure(root,0, weight=2, uniform='a')
Grid.columnconfigure(root,1, weight=2, uniform='a')
Grid.columnconfigure(root,2, weight=2, uniform='a')
Grid.columnconfigure(root,3, weight=2, uniform='a')

Grid.rowconfigure(root,1,weight=1,uniform='a')
Grid.rowconfigure(root,2,weight=1,uniform='a')
Grid.rowconfigure(root,3,weight=1,uniform='a')
Grid.rowconfigure(root,4,weight=1,uniform='a')
Grid.rowconfigure(root,5,weight=1,uniform='a')
Grid.rowconfigure(root,6,weight=1,uniform='a')
Grid.rowconfigure(root,7,weight=1,uniform='a')
Grid.rowconfigure(root,8,weight=1,uniform='a')
Grid.rowconfigure(root,9,weight=1,uniform='a')
Grid.rowconfigure(root,10,weight=1,uniform='a')
Grid.rowconfigure(root,11,weight=1,uniform='a')
Grid.rowconfigure(root,12,weight=1,uniform='a')



root.mainloop()


