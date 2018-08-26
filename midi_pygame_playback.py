import pygame
import threading
import time
import tkinter
from asyncio.tasks import wait

class PlaybackThread(threading.Thread):
    time_index = 0.0
    last_time_index = 0.0 #When last paused
    
    index_str_list = []
    
    def __init__(self, threadID, name, fileName):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.fileName = fileName
        self.start_time = 0
        self.exit_flag = False
        self.remember_time = False
        self.exited = True
        self.next_instance = None
        
        
    def run(self):
        freq = 44100    # audio CD quality
        bitsize = -16   # unsigned 16 bit
        channels = 2    # 1 is mono, 2 is stereo
        buffer = 1024    # number of samples
        pygame.mixer.init(freq, bitsize, channels, buffer)
        # optional volume 0 to 1.0
        pygame.mixer.music.set_volume(0.8)
        self.start_time = time.time()

        self.exited = False
        print ("Started "+str(self))
        print ("exit flag: "+str(self.exit_flag))
        self.play(self.fileName)
        print ("Ended " +str(self))
        
    def play(self, music_file):
        print ("Im here")
        clock = pygame.time.Clock()
        try:
            pygame.mixer.music.load(music_file)

        except pygame.error:
            print ("File %s not found! (%s)" % (music_file, pygame.get_error()))
            return
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy() and self.exit_flag == False:
            #print ("alex "+str(self.exit_flag))
            # check if playback has finished
            clock.tick(30)
            time_val = PlaybackThread.time_index + time.time() - self.start_time
            PlaybackThread.last_time_index = time_val
            secs = str(int(time_val % 60))
            if len(secs)==1: secs = "0"+secs
            millis = str(time_val % 1)[2:]
            if len(millis)==1: millis += "00"
            if len(millis)==2: millis += "0"
            if len(millis)>3: millis = millis[:3]
            
            time_str = str(int(time_val / 60))+"."+secs+":"+millis

            if len(PlaybackThread.index_str_list)>0:
                PlaybackThread.index_str_list[0].set(time_str)
        
        if self.exit_flag == True:
            pygame.mixer.music.stop()
            
            print ("Exiting: "+str(PlaybackThread.time_index))
            if self.remember_time: PlaybackThread.time_index += (time.time() - self.start_time)
            
            if PlaybackThread.time_index == 0.0:
                PlaybackThread.index_str_list[0].set("0.00:000")
            
            self.remember_time = False
            self.exit_flag = False
            self.exited = True
            if self.next_instance != None:
                self.next_instance.start()