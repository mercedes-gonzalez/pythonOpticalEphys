'''
All of the functions and extra code needed for all optical ephys 
Mercedes Gonzalez. March 2020. 
'''
import serial.tools.list_ports as serialport
import tkinter as tk 
from tkinter import ttk

def getCOMports(self):
    self.COMS_list = list(serialport.comports())
    self.COMS_list = list(['lol','nothing works'])
    return