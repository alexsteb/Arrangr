
from mido import MidiFile
import mido



from midi_GUI import * #Run the GUI loop
from midi_IO import *
from midi_tools import *
from midi_brain import *
from midi_brain_guitar import *


#import tkinter as tk


io = FileIO()

#fileName = input("MIDI file name: ")
  #Queen_-_Bohemian_Rhapsody
#Super_Mario_World_-_Air_Platform_Theme_by_Gori_Fater
#The_Legend_of_Zelda_-_A_Link_to_the_Past_-_Kakariko_Village_by_Gori_Fater
#Monkey_Island_1_-_The_Secret_of_Monkey_Island_-_Elaine_Marley_by_w3sp
#Kirbys Dream Land - Green Greens
#COMI_Wally_Crying
#sergei_prokofiev_-_montagues_and_capulets
#Castlevania medley by Verdegrand
#######################################################################################################

#notes = io.readFile("StarTrek NextGeneration.mid"       )
#notes = Create_Guitar.arrange(notes)
#notes = Create.arrange(notes)

#io.writeFile('output_new.mid',notes)












#Output the internal tabs in text-format:
#########################################E
#io.writeTabsText('output.txt',Create_Guitar.tabs,0,Create_Guitar.guitar_settings[0])

#Output the internal tabs in gp3-5-format:
#########################################

#io.writeTabsGPX('aaoutput.gp3',Create_Guitar.tabs,Create_Guitar.guitar_settings)

#TODO: GUI:
#After Guitar Settings, don't allow selection of arpeggio and STT anymore
#Checkboxes at selected tracks should be set if already once imported

#TODO: GuitarPro-Export:
#Tuning umdrehen (besonders Ukulele)
#There are still some red measures (with pirates.mid)
#Create trioles out of 16-16-(16)-16
#Fill up tones, if there is only a 16th or 8th pause
#Difficulty level -> Removing certain tones that are difficult to reach / removing fret changes if they can be easily replaced?
#Red measures and weird rhythm with Hook - Flight To Neve.mid
#Option to create chords

#TODO: Midi_tools:
#Make Combine Tracks Groups much faster

#TODO: Midi brain:
#Suddenly PC Speaker doesn't work correctly anymore..

#TODO: midi_split:
#Apply tone lists for timpani etc. (filter)





