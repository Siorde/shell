#!/usr/bin/env python
# -*- coding: utf-8 -*-

import snowboy.snowboydecoder as snowboydecoder
import sys
import os
import signal
import subprocess

interrupted = False
recording = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

def record():
    global recording
    if recording == False:
        recording = True
        i = 0
        if os.path.isdir("/tmp/shell_records/"):
            os.rmdir("/tmp/shell_records/")
        os.makedirs("/tmp/shell_records/")
        while recording == True:
            os.system("rec /tmp/shell_records/record_"+str(i)+".wav trim 0 2")
            i+=1
        os.rmdir("/tmp/shell_records/")

if len(sys.argv) == 1:
    print("Error: need to specify model name")
    print("Usage: python demo.py your.model")
    sys.exit(-1)

model = sys.argv[1]

signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
print('Listening... Press Ctrl+C to exit')

detector.start(detected_callback=record,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()