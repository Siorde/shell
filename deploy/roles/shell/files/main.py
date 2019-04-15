#!/usr/bin/env python
# -*- coding: utf-8 -*-

import snowboy.snowboydecoder as snowboydecoder
import sys
import os
import signal
import wave
import pyaudio
import shutil
import logging
from logging.handlers import RotatingFileHandler

###############################################################################
# Init logger
###############################################################################

# Set the level for the logs, it can be : DEBUG, INFO, WARNING or ERROR
LOG_LEVEL = logging.DEBUG
LOG_FILE = "/var/log/shell/shell.log"

# Create logger object
logger = logging.getLogger()
# We set the debug level
logger.setLevel(LOG_LEVEL)

# Create the formater for the logging messages
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
# Create the handler
file_handler = RotatingFileHandler(LOG_FILE, 'a', 1000000, 1)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info('Shell starting')

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

logger.debug('Variables initialized')

###############################################################################
# Functions
###############################################################################

# signal_handler is the functions that get the crt-c signal
def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    logger.info('Kill signal handled')

# This function is called when the keyword is detected. It set the mic to
# record instead of listening for the hotkey
def set_record():
    global recording
    recording = True
    logger.debug('Recording set to true')
    # if the temporary directory exist it delete it
    if os.path.isdir(TMP_DIR):
        shutil.rmtree(TMP_DIR)
        logger.info('Temporary folder deleted')
    # then it recreate the tmp directory
    os.makedirs(TMP_DIR)
    logger.info('Temporary folder created')

# This function is used to exit the hotword listening when the key is detected
def interrupt_callback():
    global recording
    return recording

###############################################################################
# Main
###############################################################################

# We set the interceptor for the stop signal
signal.signal(signal.SIGINT, signal_handler)
logger.debug('Set the signal handler')

# We create the detector with the MODEL
detector = snowboydecoder.HotwordDetector(MODEL, sensitivity=0.5)
logger.debug('Create the detector with the hotword model')

# While we don't stop the script...
while interrupted == False:
    if recording == False:
        logger.info('"recording" is false, so we start the detector')
        # If we don't record, we listen to the keyword
        detector.start(detected_callback=set_record,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)
        detector.terminate()
        logger.info('hotword detected, we stop the listening')
        # Reset the index
        i = 0
    else:
        # Else we record every 2 second in wav files
        # We create pyaudio instantiation
        audio = pyaudio.PyAudio()
        logger.debug('instantiate "pyaudio"')

        # create pyaudio stream
        stream = audio.open(format = FORM,rate = RATE,channels = CHANELS, \
                            input_device_index = DEV_INDEX,input = True, \
                            frames_per_buffer=CHUNK)
        logger.debug('pyaudio stream created')
        
        frames = []
        # loop through stream and append audio CHUNKs to frame array
        for ii in range(0,int((RATE/CHUNK)*REC_TIME)):
            data = stream.read(CHUNK)
            frames.append(data)
        logger.debug('append audio chunk')

        # stop the stream, close it, and terminate the pyaudio instantiation
        stream.stop_stream()
        stream.close()
        audio.terminate()
        logger.debug('stream closed')

        # save the audio frames as .wav file
        wavefile = wave.open(TMP_DIR+"/record_"+str(i)+".wav",'wb')
        wavefile.setnchannels(CHANELS)
        wavefile.setsampwidth(audio.get_sample_size(FORM))
        wavefile.setframerate(RATE)
        wavefile.writeframes(b''.join(frames))
        wavefile.close()
        logger.debug('Saved the  audio to '+TMP_DIR+'/record_'+str(i)+'.wav')

        # Increment the index for the files name
        i+=1

# Delete temporary directory
if os.path.isdir(TMP_DIR):
    shutil.rmtree(TMP_DIR)
    logger.info('Temporary folder deleted')