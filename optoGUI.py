"""
    Python based GUI for all optical e-phys and auto-cleaning.

    Mercedes Gonzalez. March 2020.
    m.gonzalez@gatech.edu
    Precision Biosystems Lab | Georgia Institute of Technology
    Version Control: https://github.gatech.edu/mgonzalez91/pythonOpticalEphys 

"""

# Import all necessary libraries
import tkinter as tk 
from tkinter import ttk
from tkinter import filedialog
from os import listdir
from os.path import isfile, join
import csv
import numpy as np
import scipy as sp
import scipy.signal as sig
import pyabf
import matplotlib as plt
import axographio as axo
from cleanFuncts import * 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from tkinter.messagebox import showinfo, showwarning

# GUI Formatting params
# Colors
bg_color = 'snow3'
wash_colors = ['firebrick1','firebrick2','firebrick3','firebrick4']
clean_colors = ['DarkOrange1','DarkOrange2','DarkOrange3','DarkOrange4']
locations_colors = ['goldenrod1','goldenrod2','goldenrod3','goldenrod4']
settings_colors = ['green','green1','green3','green4']
title_str = 'Arial 9 bold'
styles = ['flat','raised','sunken','groove','ridge']
sty = 3
size = 3
NULL_DIR_STR = "* SET DIRECTORY *"
instruction_text = """
1. [Select] to choose directory with .abf files
2. [Save] saves data shown on plot in a .csv located in a specified folder
3. [Reset] clears all data and plots.

NOTE:
- Auto mode plots all files in the directory
- Manual mode only plots selected files
- Use tool bar to interact with plot
"""
# Define GUI class
class ephysTool(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self,master)
        master.title("MG Electrophysiology Tool")
        self.master = master

        # Notebook
        self.tabs = ttk.Notebook(self.master)

        # DEFINE CLEANING FRAMES
        self.CLEAN_TAB = tk.Frame(self.tabs,bg='snow3',relief=styles[sty],borderwidth=size)
        self.tabs.add(self.CLEAN_TAB,text='AUTO-CLEANING')
        
        self.WASH_FRAME = tk.Frame(self.CLEAN_TAB,bg=wash_colors[0],relief=styles[sty],borderwidth=size)
        self.CLEAN_FRAME = tk.Frame(self.CLEAN_TAB,bg=clean_colors[0],relief=styles[sty],borderwidth=size)
        self.LOCATIONS_FRAME = tk.Frame(self.CLEAN_TAB,bg=locations_colors[0],relief=styles[sty],borderwidth=size)
        self.SETTINGS_FRAME = tk.Frame(self.CLEAN_TAB,bg=settings_colors[0],relief=styles[sty],borderwidth=size)

        # WASH FRAME BUTTONS
        self.wash_title = tk.Label(self.WASH_FRAME, text="WASH",font=(title_str),bg=wash_colors[0])

        self.prewash = tk.IntVar()
        self.prewash.set(0)
        self.wash_controls_frame = tk.Frame(self.WASH_FRAME,bg=wash_colors[1],relief=styles[1],borderwidth=1)
        self.prewash_btn = tk.Checkbutton(self.wash_controls_frame,text='PREWASH',bg=wash_colors[2],selectcolor='red3',indicatoron=0,variable=self.prewash,onvalue=1,offvalue=0)
        self.save_wash_btn = tk.Button(self.wash_controls_frame,text='SAVE PROTOCOL',bg=wash_colors[2])
        self.load_wash_btn = tk.Button(self.wash_controls_frame,text='LOAD PROTOCOL',bg=wash_colors[2])

        
        # CLEAN FRAME BUTTONS
        self.clean_title = tk.Label(self.CLEAN_FRAME, text="CLEAN",font=(title_str),bg=clean_colors[0])

        self.clean_controls_frame = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[1],relief=styles[1],borderwidth=1)
        self.save_clean_btn = tk.Button(self.clean_controls_frame,text='SAVE PROTOCOL',bg=clean_colors[2])
        self.load_clean_btn = tk.Button(self.clean_controls_frame,text='LOAD PROTOCOL',bg=clean_colors[2])


        # LOCATIONS FRAME BUTTONS
        self.locations_title = tk.Label(self.LOCATIONS_FRAME, text="LOCATIONS",font=(title_str),bg=locations_colors[0])
        
        # SETTINGS FRAME BUTTONS
        self.settings_title = tk.Label(self.SETTINGS_FRAME, text="SETTINGS",font=(title_str),bg=settings_colors[0])

        # DEFINE OPTOEPHYS FRAMES
        self.OPTOEPHYS_TAB = tk.Frame(self.tabs,bg='snow3',relief=styles[sty],borderwidth=size)
        self.tabs.add(self.OPTOEPHYS_TAB,text='OPTIX + EPHYS')

        # FRAME PACKING 
        self.WASH_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.CLEAN_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.LOCATIONS_FRAME.pack(side=tk.TOP,fill=tk.X,expand=1)
        self.SETTINGS_FRAME.pack(side=tk.TOP,fill=tk.X,expand=1)

        # WASH FRAME PACKING
        self.wash_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.wash_controls_frame.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.prewash_btn.pack(side=tk.TOP,fill=tk.BOTH,expand=0)
        self.save_wash_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.load_wash_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)


        # CLEAN FRAME PACKING
        self.clean_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.clean_controls_frame.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.save_clean_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        self.load_clean_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)

        # LOCATIONS FRAME PACKING
        self.locations_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        # SETTINGS FRAME PACKING
        self.settings_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        # Pack the tabs
        self.tabs.pack(fill=tk.BOTH,expand=1)
# Define GUI Functions
    def popup_help(self):
        showinfo("Help", instruction_text)

root = tk.Tk()
root.geometry("600x600+50+100") #width x height + x and y screen dims
# root.configure(bg=bg_color)
my_gui = ephysTool(root)
root.mainloop()

'''
    TODO: CLEANING
    - sutter driver working
    - save position
    - move to position
    - set protocol params
    - set pressure
    - CLEAN button
    - SAVE protocol
    - 
    - 

    TODO: OPTICAL EPHYS
    - 

    FINISHED: 
    

'''