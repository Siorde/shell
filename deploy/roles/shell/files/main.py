#!/usr/bin/env python
# -*- coding: utf-8 -*-

import snowboy.snowboydecoder as snowboydecoder
import sys
import os
import signal
import wave
import pyaudio
import shutil

###############################################################################
# Variables
###############################################################################

# interrupted is used to know if the user press ctrl-c
interrupted = False

# recording is used to set the mic to the recording instead of listening to the
# hotkey
recording = False

# Path to the temporary directory where the records will be stored
TMP_DIR = "/tmp/shell"

# Path to model file
MODEL = "/opt/shell/snowboy/resources/Hey Shell.pmdl"

# These values are the recording parameters
FORM = pyaudio.paInt16
CHANELS = 1
RATE = 44100
CHUNK = 4096
REC_TIME = 2
DEV_INDEX = 2

###############################################################################
# Functions
###############################################################################

# signal_handler is the functions that get the crt-c signal
def signal_handler(signal, frame):
    global interrupted
    interrupted = True

# This function is called when the keyword is detected. It set the mic to
# record instead of listening for the hotkey
def set_record():
    global recording
    recording = True
    # if the temporary directory exist it delete it
    if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
    # then it recreate the tmp directory
    os.makedirs(TMP_DIR)

# This function is used to exit the hotword listening when the key is detected
def interrupt_callback():
    global recording
    return recording

###############################################################################
# Main
###############################################################################

# We set the interceptor for the stop signal
signal.signal(signal.SIGINT, signal_handler)

# We create the detector with the MODEL
detector = snowboydecoder.HotwordDetector(MODEL, sensitivity=0.5)

# While we don't stop the script...
while interrupted == False:
    if recording == False:
        # If we don't record, we listen to the keyword
        detector.start(detected_callback=set_record,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)
        detector.terminate()
        # Reset the index
        i = 0
    else:
        # Else we record every 2 second in wav files
        # We create pyaudio instantiation
        audio = pyaudio.PyAudio()

        # create pyaudio stream
        stream = audio.open(format = FORM,rate = RATE,channels = CHANELS, \
                            input_device_index = DEV_INDEX,input = True, \
                            frames_per_buffer=CHUNK)
        
        frames = []
        # loop through stream and append audio CHUNKs to frame array
        for ii in range(0,int((RATE/CHUNK)*REC_TIME)):
            data = stream.read(CHUNK)
            frames.append(data)

        # stop the stream, close it, and terminate the pyaudio instantiation
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # save the audio frames as .wav file
        wavefile = wave.open(TMP_DIR+"/records/record_"+str(i)+".wav",'wb')
        wavefile.setnchannels(CHANELS)
        wavefile.setsampwidth(audio.get_sample_size(FORM))
        wavefile.setframerate(RATE)
        wavefile.writeframes(b''.join(frames))
        wavefile.close()

        # Increment the index for the files name
        i+=1

# Delete temporary directory
if os.path.isdir(TMP_DIR):
        shutil.rmtree(TMP_DIR)