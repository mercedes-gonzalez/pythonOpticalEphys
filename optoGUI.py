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
title_str = 'Arial 11 bold'
location_str = 'Arial 9 bold'
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
        self.wash_controls_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[1],relief=styles[1],borderwidth=1)
        self.prewash_btn = tk.Checkbutton(self.wash_controls_box,text='PREWASH',bg=wash_colors[2],selectcolor='red3',indicatoron=0,variable=self.prewash,onvalue=1,offvalue=0)
        self.save_wash_btn = tk.Button(self.wash_controls_box,text='SAVE PROTOCOL',bg=wash_colors[2])
        self.load_wash_btn = tk.Button(self.wash_controls_box,text='LOAD PROTOCOL',bg=wash_colors[2])

        
        # CLEAN FRAME WIDGETS
        self.clean_title = tk.Label(self.CLEAN_FRAME, text="CLEAN",font=(title_str),bg=clean_colors[0])
        self.clean_controls_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[1],relief=styles[1],borderwidth=1)
        self.save_clean_btn = tk.Button(self.clean_controls_box,text='SAVE PROTOCOL',bg=clean_colors[2])
        self.load_clean_btn = tk.Button(self.clean_controls_box,text='LOAD PROTOCOL',bg=clean_colors[2])

        # LOCATIONS FRAME WIDGETS
        self.locations_title = tk.Label(self.LOCATIONS_FRAME, text="LOCATIONS",font=(title_str),bg=locations_colors[0])
        self.save_locations_btn = tk.Button(self.LOCATIONS_FRAME,text='SAVE LOCATIONS',bg=locations_colors[2])

        # Sample location
        self.sample_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[1],relief=styles[1],borderwidth=1)
        self.sample_location_label = tk.Label(self.sample_location_box, text="Sample Location:",font=(location_str),bg=locations_colors[0])
        
        # Sample location x
        self.sample_x_value = tk.IntVar()
        self.sample_x_value.set(0)
        self.sample_x_display = tk.Label(self.sample_location_box,bg=locations_colors[1],textvariable=self.sample_x_value)

        # Sample location y
        self.sample_y_value = tk.IntVar()
        self.sample_y_value.set(0)
        self.sample_y_display = tk.Label(self.sample_location_box,bg=locations_colors[1],textvariable=self.sample_y_value)

        # Sample location z
        self.sample_z_value = tk.IntVar()
        self.sample_z_value.set(0)
        self.sample_z_display = tk.Label(self.sample_location_box,bg=locations_colors[1],textvariable=self.sample_z_value)

        # Sample location GO
        self.sample_go_btn = tk.Button(self.sample_location_box,text='GO',bg=locations_colors[2])

        # ------------------------------------
        # Above baths location
        self.abovebath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[1],relief=styles[1],borderwidth=1)
        self.abovebath_location_label = tk.Label(self.abovebath_location_box, text="Above Bath Location:",font=(location_str),bg=locations_colors[0])
        
        # Above baths location x
        self.abovebath_x_value = tk.IntVar()
        self.abovebath_x_value.set(0)
        self.abovebath_x_display = tk.Label(self.abovebath_location_box,bg=locations_colors[1],textvariable=self.abovebath_x_value)

        # Above baths location y
        self.abovebath_y_value = tk.IntVar()
        self.abovebath_y_value.set(0)
        self.abovebath_y_display = tk.Label(self.abovebath_location_box,bg=locations_colors[1],textvariable=self.abovebath_y_value)

        # Above baths location z
        self.abovebath_z_value = tk.IntVar()
        self.abovebath_z_value.set(0)
        self.abovebath_z_display = tk.Label(self.abovebath_location_box,bg=locations_colors[1],textvariable=self.abovebath_z_value)

        # Above baths location GO
        self.abovebath_go_btn = tk.Button(self.abovebath_location_box,text='GO',bg=locations_colors[2])

        # ------------------------------------
        # Clean bath location
        self.cleanbath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[1],relief=styles[1],borderwidth=1)
        self.cleanbath_location_label = tk.Label(self.cleanbath_location_box, text="Clean Bath Location:",font=(location_str),bg=locations_colors[0])
        
        # Clean bath location x
        self.cleanbath_x_value = tk.IntVar()
        self.cleanbath_x_value.set(0)
        self.cleanbath_x_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[1],textvariable=self.cleanbath_x_value)

        # Clean bath location y
        self.cleanbath_y_value = tk.IntVar()
        self.cleanbath_y_value.set(0)
        self.cleanbath_y_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[1],textvariable=self.cleanbath_y_value)

        # Clean bath location z
        self.cleanbath_z_value = tk.IntVar()
        self.cleanbath_z_value.set(0)
        self.cleanbath_z_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[1],textvariable=self.cleanbath_z_value)

        # Clean bath location GO
        self.cleanbath_go_btn = tk.Button(self.cleanbath_location_box,text='GO',bg=locations_colors[2])

        # ------------------------------------
        # Wash bath location
        self.washbath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[1],relief=styles[1],borderwidth=1)
        self.washbath_location_label = tk.Label(self.washbath_location_box, text="Wash Bath Location:",font=(location_str),bg=locations_colors[0])
        
        # Clean bath location x
        self.washbath_x_value = tk.IntVar()
        self.washbath_x_value.set(0)
        self.washbath_x_display = tk.Label(self.washbath_location_box,bg=locations_colors[1],textvariable=self.washbath_x_value)

        # Clean bath location y
        self.washbath_y_value = tk.IntVar()
        self.washbath_y_value.set(0)
        self.washbath_y_display = tk.Label(self.washbath_location_box,bg=locations_colors[1],textvariable=self.washbath_y_value)

        # Clean bath location z
        self.washbath_z_value = tk.IntVar()
        self.washbath_z_value.set(0)
        self.washbath_z_display = tk.Label(self.washbath_location_box,bg=locations_colors[1],textvariable=self.washbath_z_value)

        # Clean bath location GO
        self.washbath_go_btn = tk.Button(self.washbath_location_box,text='GO',bg=locations_colors[2])
        # ------------------------------------
        # Above clean bath location
        self.aboveclean_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[1],relief=styles[1],borderwidth=1)
        self.aboveclean_location_label = tk.Label(self.aboveclean_location_box, text="Above Clean Location:",font=(location_str),bg=locations_colors[0])
        
        # Above clean bath location x
        self.aboveclean_x_value = tk.IntVar()
        self.aboveclean_x_value.set(0)
        self.aboveclean_x_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[1],textvariable=self.aboveclean_x_value)

        # Above Clean bath location y
        self.aboveclean_y_value = tk.IntVar()
        self.aboveclean_y_value.set(0)
        self.aboveclean_y_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[1],textvariable=self.aboveclean_y_value)

        # Above Clean bath location z
        self.aboveclean_z_value = tk.IntVar()
        self.aboveclean_z_value.set(0)
        self.aboveclean_z_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[1],textvariable=self.aboveclean_z_value)

        # Above Clean bath location GO
        self.aboveclean_go_btn = tk.Button(self.aboveclean_location_box,text='GO',bg=locations_colors[2])

        # ------------------------------------
        # Above wash bath location
        self.abovewash_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[1],relief=styles[1],borderwidth=1)
        self.abovewash_location_label = tk.Label(self.abovewash_location_box, text="Above Wash Location:",font=(location_str),bg=locations_colors[0])
        
        # Above wash bath location x
        self.abovewash_x_value = tk.IntVar()
        self.abovewash_x_value.set(0)
        self.abovewash_x_display = tk.Label(self.abovewash_location_box,bg=locations_colors[1],textvariable=self.abovewash_x_value)

        # Above wash bath location y
        self.abovewash_y_value = tk.IntVar()
        self.abovewash_y_value.set(0)
        self.abovewash_y_display = tk.Label(self.abovewash_location_box,bg=locations_colors[1],textvariable=self.abovewash_y_value)

        # Above wash bath location z
        self.abovewash_z_value = tk.IntVar()
        self.abovewash_z_value.set(0)
        self.abovewash_z_display = tk.Label(self.abovewash_location_box,bg=locations_colors[1],textvariable=self.abovewash_z_value)

        # Above wash bath location GO
        self.abovewash_go_btn = tk.Button(self.abovewash_location_box,text='GO',bg=locations_colors[2])

        # ------------------------------------
        # SETTINGS FRAME WIDGETS
        self.settings_title = tk.Label(self.SETTINGS_FRAME, text="SETTINGS",font=(title_str),bg=settings_colors[0])

        # DEFINE OPTOEPHYS FRAMES
        self.OPTOEPHYS_TAB = tk.Frame(self.tabs,bg='snow3',relief=styles[sty],borderwidth=size)
        self.tabs.add(self.OPTOEPHYS_TAB,text='OPTIX + EPHYS')

        # WASH FRAME PACKING
        self.WASH_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.wash_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.wash_controls_box.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.prewash_btn.pack(side=tk.TOP,fill=tk.BOTH,expand=0)
        self.save_wash_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.load_wash_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

        # CLEAN FRAME PACKING
        self.CLEAN_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.clean_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.clean_controls_box.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.save_clean_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        self.load_clean_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)

        # LOCATIONS FRAME PACKING
        self.LOCATIONS_FRAME.pack(side=tk.TOP,fill=tk.X,expand=1)
        self.locations_title.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.save_locations_btn.pack(side=tk.BOTTOM,fill=tk.Y,expand=0)
        # Sample location packing
        self.sample_location_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.sample_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.sample_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.sample_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.sample_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.sample_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Above bath packing
        self.abovebath_location_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.abovebath_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.abovebath_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovebath_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovebath_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovebath_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Cleaning bath location packing
        self.cleanbath_location_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.cleanbath_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.cleanbath_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.cleanbath_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.cleanbath_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.cleanbath_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Wash bath location packing
        self.washbath_location_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.washbath_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.washbath_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.washbath_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.washbath_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.washbath_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Above clean bath location packing
        self.aboveclean_location_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.aboveclean_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.aboveclean_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.aboveclean_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.aboveclean_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.aboveclean_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Above wash bath location packing
        self.abovewash_location_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.abovewash_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.abovewash_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovewash_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovewash_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovewash_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)

        # SETTINGS FRAME PACKING
        self.SETTINGS_FRAME.pack(side=tk.TOP,fill=tk.X,expand=1)
        self.settings_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        # Pack the tabs
        self.tabs.pack(fill=tk.BOTH,expand=1)
# Define GUI Functions
    def popup_help(self):
        showinfo("Help", instruction_text)

root = tk.Tk()
root.geometry("800x600+50+100") #width x height + x and y screen dims
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