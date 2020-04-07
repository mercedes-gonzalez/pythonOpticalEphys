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
wash_colors = ['salmon','firebrick1','firebrick2','firebrick3','firebrick4']
clean_colors = ['sandybrown','DarkOrange1','DarkOrange2','DarkOrange3','DarkOrange4']
locations_colors = ['LightGoldenRod1','goldenrod1','goldenrod2','goldenrod3','goldenrod4']
settings_colors = ['pale green','green','green1','green3','green4']
controls_colors = ['lavender','MediumPurple1','MediumPurple2','MediumPurple3','MediumPurple4']
entryc = 0
btnc = 1
boxc = 2
framec = 3
tabc = 4
boxwidth = 14
title_str = 'Arial 11 bold'
label_str = 'Arial 9 bold'
styles = ['flat','raised','sunken','groove','ridge']
sty = 3
size = 3
xpad = 5
ypad = 2
NULL_DIR_STR = "* SET DIRECTORY *"
instruction_text = """
1. Insert helpful instructions here. 
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
        
        self.CONTROLS_FRAME = tk.Frame(self.CLEAN_TAB,bg=controls_colors[framec],relief=styles[sty],borderwidth=size)
        self.WASH_FRAME = tk.Frame(self.CLEAN_TAB,bg=wash_colors[framec],relief=styles[sty],borderwidth=size)
        self.CLEAN_FRAME = tk.Frame(self.CLEAN_TAB,bg=clean_colors[framec],relief=styles[sty],borderwidth=size)
        self.LOCATIONS_FRAME = tk.Frame(self.CLEAN_TAB,bg=locations_colors[framec],relief=styles[sty],borderwidth=size)
        self.SETTINGS_FRAME = tk.Frame(self.CLEAN_TAB,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)

        # CONTROLS FRAME WIDGETS
        self.controls_title = tk.Label(self.CONTROLS_FRAME, text="CONTROLS",font=(title_str),bg=controls_colors[framec])
        self.clean_btn = tk.Button(self.CONTROLS_FRAME,text='CLEAN',bg=controls_colors[btnc])
        
        self.sep1 = ttk.Separator(self.CONTROLS_FRAME, orient="horizontal")
        
        self.protocol_box = tk.Frame(self.CONTROLS_FRAME,bg=controls_colors[framec],relief=styles[sty],borderwidth=size)
        self.protocol = tk.IntVar()
        self.protocol.set(1)
        self.protocol_label = tk.Label(self.CONTROLS_FRAME, text="Protocol:",font=(label_str),bg=controls_colors[framec])
        self.clean_protocol_btn = tk.Radiobutton(self.CONTROLS_FRAME,text="Clean",variable=self.protocol,value=0,bg=controls_colors[framec])
        self.sham_protocol_btn = tk.Radiobutton(self.CONTROLS_FRAME,text="Sham",variable=self.protocol,value=1,bg=controls_colors[framec])
        
        self.sep2 = ttk.Separator(self.CONTROLS_FRAME, orient="horizontal")
        
        self.duration_value = tk.DoubleVar()
        self.duration_value.set(20) # default capactiance
        self.duration_label = tk.Label(self.CONTROLS_FRAME, text="Break In Duration [s]:",font=(label_str),bg=controls_colors[framec])
        vcmd = self.master.register(self.validate) # we have to wrap the command
        self.duration_entry = tk.Entry(self.CONTROLS_FRAME, text=self.duration_value,validate="key", validatecommand=(vcmd, '%P'),bg=controls_colors[entryc])

        self.sep3 = ttk.Separator(self.CONTROLS_FRAME, orient="horizontal")

        self.breakin_btn = tk.Button(self.CONTROLS_FRAME,text='BREAK IN',bg=controls_colors[btnc])

        # WASH FRAME WIDGETS
        self.wash_title = tk.Label(self.WASH_FRAME, text="WASH",font=(title_str),bg=wash_colors[framec])
        
        self.wash_time_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[boxc],relief=styles[1],borderwidth=1)
        self.wash_time_value = tk.StringVar()
        self.wash_time_value.set('3,\n10') # default capactiance
        self.wash_time_label = tk.Label(self.wash_time_box,bg=wash_colors[boxc],text="Time [s]")
        self.wash_time_entry = tk.Text(self.wash_time_box,bg=wash_colors[entryc],width=boxwidth)
        
        self.wash_pres_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[boxc],relief=styles[1],borderwidth=1)
        self.wash_pres_value = tk.StringVar()
        self.wash_pres_value.set('-345,\n1000') # default capactiance
        self.wash_pres_label = tk.Label(self.wash_pres_box,bg=wash_colors[boxc],text="Pressure [mBar]")
        self.wash_pres_entry = tk.Text(self.wash_pres_box,bg=wash_colors[entryc],width=boxwidth)

        self.prewash = tk.IntVar()
        self.prewash.set(0)
        self.wash_controls_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[boxc],relief=styles[sty],borderwidth=1)
        self.prewash_btn = tk.Checkbutton(self.wash_controls_box,text='PREWASH',bg=wash_colors[boxc],selectcolor=wash_colors[3],indicatoron=1,variable=self.prewash,onvalue=1,offvalue=0)
        self.save_wash_btn = tk.Button(self.wash_controls_box,text='SAVE PROTOCOL',bg=wash_colors[btnc])
        self.load_wash_btn = tk.Button(self.wash_controls_box,text='LOAD PROTOCOL',bg=wash_colors[btnc])

        
        # CLEAN FRAME WIDGETS
        self.clean_title = tk.Label(self.CLEAN_FRAME, text="CLEAN",font=(title_str),bg=clean_colors[framec])
        self.clean_controls_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[boxc],relief=styles[1],borderwidth=1)

        self.clean_time_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[boxc],relief=styles[1],borderwidth=1)
        self.clean_time_value = tk.StringVar()
        self.clean_time_value.set('3,\n10') # default capactiance
        self.clean_time_label = tk.Label(self.clean_time_box,bg=clean_colors[boxc],text="Time [s]")
        self.clean_time_entry = tk.Text(self.clean_time_box,bg=clean_colors[entryc],width=boxwidth)
        
        self.clean_pres_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[boxc],relief=styles[1],borderwidth=1)
        self.clean_pres_value = tk.StringVar()
        self.clean_pres_value.set('-345,\n1000') # default capactiance
        self.clean_pres_label = tk.Label(self.clean_pres_box,bg=clean_colors[boxc],text="Pressure [mBar]")
        self.clean_pres_entry = tk.Text(self.clean_pres_box,bg=clean_colors[entryc],width=boxwidth)

        self.save_clean_btn = tk.Button(self.clean_controls_box,text='SAVE PROTOCOL',bg=clean_colors[btnc])
        self.load_clean_btn = tk.Button(self.clean_controls_box,text='LOAD PROTOCOL',bg=clean_colors[btnc])

        # LOCATIONS FRAME WIDGETS
        self.locations_title = tk.Label(self.LOCATIONS_FRAME, text="LOCATIONS",font=(title_str),bg=locations_colors[framec])
        self.save_locations_btn = tk.Button(self.LOCATIONS_FRAME,text='SAVE LOCATIONS',relief=styles[1],bg=locations_colors[btnc])
        self.load_locations_btn = tk.Button(self.LOCATIONS_FRAME,text='LOAD LOCATIONS',relief=styles[1],bg=locations_colors[btnc])

        # Sample location
        self.sample_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=0)
        self.sample_location_label = tk.Label(self.sample_location_box, text="Sample Location:",font=(label_str),bg=locations_colors[boxc])
        
        # Sample location x
        self.sample_x_value = tk.IntVar()
        self.sample_x_value.set(0)
        self.sample_x_display = tk.Label(self.sample_location_box,bg=locations_colors[entryc],textvariable=self.sample_x_value)

        # Sample location y
        self.sample_y_value = tk.IntVar()
        self.sample_y_value.set(0)
        self.sample_y_display = tk.Label(self.sample_location_box,bg=locations_colors[entryc],textvariable=self.sample_y_value)

        # Sample location z
        self.sample_z_value = tk.IntVar()
        self.sample_z_value.set(0)
        self.sample_z_display = tk.Label(self.sample_location_box,bg=locations_colors[entryc],textvariable=self.sample_z_value)

        # Sample location GO
        self.sample_go_btn = tk.Button(self.sample_location_box,text='GO',bg=locations_colors[btnc])

        # ------------------------------------
        # Above baths location
        self.abovebath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[entryc],relief=styles[0],borderwidth=1)
        self.abovebath_location_btn = tk.Button(self.abovebath_location_box, text="Above Bath Location:",font=(label_str),bg=locations_colors[boxc])
        
        # Above baths location x
        self.abovebath_x_value = tk.IntVar()
        self.abovebath_x_value.set(0)
        self.abovebath_x_display = tk.Label(self.abovebath_location_box,bg=locations_colors[entryc],textvariable=self.abovebath_x_value)

        # Above baths location y
        self.abovebath_y_value = tk.IntVar()
        self.abovebath_y_value.set(0)
        self.abovebath_y_display = tk.Label(self.abovebath_location_box,bg=locations_colors[entryc],textvariable=self.abovebath_y_value)

        # Above baths location z
        self.abovebath_z_value = tk.IntVar()
        self.abovebath_z_value.set(0)
        self.abovebath_z_display = tk.Label(self.abovebath_location_box,bg=locations_colors[entryc],textvariable=self.abovebath_z_value)

        # Above baths location GO
        self.abovebath_go_btn = tk.Button(self.abovebath_location_box,text='GO',bg=locations_colors[btnc])

        # ------------------------------------
        # Clean bath location
        self.cleanbath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[entryc],relief=styles[0],borderwidth=1)
        self.cleanbath_location_btn = tk.Button(self.cleanbath_location_box, text="Clean Bath Location:",font=(label_str),bg=locations_colors[boxc])
        
        # Clean bath location x
        self.cleanbath_x_value = tk.IntVar()
        self.cleanbath_x_value.set(0)
        self.cleanbath_x_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[entryc],textvariable=self.cleanbath_x_value)

        # Clean bath location y
        self.cleanbath_y_value = tk.IntVar()
        self.cleanbath_y_value.set(0)
        self.cleanbath_y_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[entryc],textvariable=self.cleanbath_y_value)

        # Clean bath location z
        self.cleanbath_z_value = tk.IntVar()
        self.cleanbath_z_value.set(0)
        self.cleanbath_z_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[entryc],textvariable=self.cleanbath_z_value)

        # Clean bath location GO
        self.cleanbath_go_btn = tk.Button(self.cleanbath_location_box,text='GO',bg=locations_colors[btnc])

        # ------------------------------------
        # Wash bath location
        self.washbath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[entryc],relief=styles[1],borderwidth=1)
        self.washbath_location_btn = tk.Button(self.washbath_location_box, text="Wash Bath Location:",font=(label_str),bg=locations_colors[boxc])
        
        # Clean bath location x
        self.washbath_x_value = tk.IntVar()
        self.washbath_x_value.set(0)
        self.washbath_x_display = tk.Label(self.washbath_location_box,bg=locations_colors[entryc],textvariable=self.washbath_x_value)

        # Clean bath location y
        self.washbath_y_value = tk.IntVar()
        self.washbath_y_value.set(0)
        self.washbath_y_display = tk.Label(self.washbath_location_box,bg=locations_colors[entryc],textvariable=self.washbath_y_value)

        # Clean bath location z
        self.washbath_z_value = tk.IntVar()
        self.washbath_z_value.set(0)
        self.washbath_z_display = tk.Label(self.washbath_location_box,bg=locations_colors[entryc],textvariable=self.washbath_z_value)

        # Clean bath location GO
        self.washbath_go_btn = tk.Button(self.washbath_location_box,text='GO',bg=locations_colors[btnc])
        # ------------------------------------
        # Above clean bath location
        self.aboveclean_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[entryc],relief=styles[1],borderwidth=1)
        self.aboveclean_location_label = tk.Label(self.aboveclean_location_box, text="Above Clean Location:",font=(label_str),bg=locations_colors[boxc])
        
        # Above clean bath location x
        self.aboveclean_x_value = tk.IntVar()
        self.aboveclean_x_value.set(0)
        self.aboveclean_x_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[entryc],textvariable=self.aboveclean_x_value)

        # Above Clean bath location y
        self.aboveclean_y_value = tk.IntVar()
        self.aboveclean_y_value.set(0)
        self.aboveclean_y_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[entryc],textvariable=self.aboveclean_y_value)

        # Above Clean bath location z
        self.aboveclean_z_value = tk.IntVar()
        self.aboveclean_z_value.set(0)
        self.aboveclean_z_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[entryc],textvariable=self.aboveclean_z_value)

        # Above Clean bath location GO
        self.aboveclean_go_btn = tk.Button(self.aboveclean_location_box,text='GO',bg=locations_colors[btnc])

        # ------------------------------------
        # Above wash bath location
        self.abovewash_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[entryc],relief=styles[1],borderwidth=1)
        self.abovewash_location_label = tk.Label(self.abovewash_location_box, text="Above Wash Location:",font=(label_str),bg=locations_colors[boxc])
        
        # Above wash bath location x
        self.abovewash_x_value = tk.IntVar()
        self.abovewash_x_value.set(0)
        self.abovewash_x_display = tk.Label(self.abovewash_location_box,bg=locations_colors[entryc],textvariable=self.abovewash_x_value)

        # Above wash bath location y
        self.abovewash_y_value = tk.IntVar()
        self.abovewash_y_value.set(0)
        self.abovewash_y_display = tk.Label(self.abovewash_location_box,bg=locations_colors[entryc],textvariable=self.abovewash_y_value)

        # Above wash bath location z
        self.abovewash_z_value = tk.IntVar()
        self.abovewash_z_value.set(0)
        self.abovewash_z_display = tk.Label(self.abovewash_location_box,bg=locations_colors[entryc],textvariable=self.abovewash_z_value)

        # Above wash bath location GO
        self.abovewash_go_btn = tk.Button(self.abovewash_location_box,text='GO',bg=locations_colors[btnc])

        # ------------------------------------
        # SETTINGS FRAME WIDGETS
        self.settings_title = tk.Label(self.SETTINGS_FRAME, text="SETTINGS",font=(title_str),bg=settings_colors[framec])
        
        # Actuator type
        self.actuator_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.actuator_value = tk.IntVar()
        self.actuator_value.set(0)
        self.actuator_label = tk.Label(self.actuator_box, text="Actuator Type:",font=(label_str),bg=settings_colors[framec])
        self.sutter_btn = tk.Radiobutton(self.actuator_box,text="Sutter",variable=self.actuator_value,value=0,bg=settings_colors[framec])
        self.scientifica_btn = tk.Radiobutton(self.actuator_box,text="Scientifica",variable=self.actuator_value,value=1,bg=settings_colors[framec])
        
        # Manipulator COM
        self.COM_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.COMS_list = ['TEST1','TEST2','GET COMS WORKING']
        self.manip_COM_combo = ttk.Combobox(self.COM_box,values=self.COMS_list)
        self.COM_label = tk.Label(self.COM_box, text="Manipulator COM: ",font=(label_str),bg=settings_colors[framec])

        # Multiclamp handle
        self.multiclamp_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.multiclamp_handle = tk.IntVar()
        self.multiclamp_handle.set(0)
        self.multiclamp_entry = tk.Entry(self.multiclamp_box, text=self.multiclamp_handle,validate="key", validatecommand=(vcmd, '%P'),bg=settings_colors[entryc])
        self.multiclamp_label = tk.Label(self.multiclamp_box, text="Multiclamp Handle: ",font=(label_str),bg=settings_colors[framec])
        
        self.help_btn = tk.Button(self.SETTINGS_FRAME,text='Help',bg=settings_colors[btnc],command=self.popup_help)
        
        # DEFINE OPTOEPHYS FRAMES
        self.OPTOEPHYS_TAB = tk.Frame(self.tabs,bg='snow3',relief=styles[sty],borderwidth=size)
        self.tabs.add(self.OPTOEPHYS_TAB,text='OPTIX + EPHYS')

# _____________________________________________________
# _____________________________________________________
#               PACKING 

        # CONTROLS FRAME PACKING
        self.CONTROLS_FRAME.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.controls_title.pack(side=tk.TOP,fill=tk.X,expand=1)
        self.clean_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        
        self.sep1.pack(side=tk.LEFT, fill=tk.BOTH,padx=xpad,pady=ypad)
        
        self.protocol_box.pack(side=tk.LEFT,fill=tk.BOTH,expand=0,padx=xpad,pady=ypad)
        self.protocol_label.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.clean_protocol_btn.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.sham_protocol_btn.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        
        self.sep2.pack(side=tk.LEFT, fill=tk.BOTH,padx=xpad,pady=ypad)
        
        self.duration_label.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.duration_entry.pack(side=tk.LEFT,fill=tk.Y,expand=0)

        self.sep3.pack(side=tk.LEFT, fill=tk.BOTH,padx=xpad,pady=ypad)

        self.breakin_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0,padx=xpad,pady=ypad)
        
        # WASH FRAME PACKING
        self.WASH_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.wash_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.wash_controls_box.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.prewash_btn.pack(side=tk.TOP,fill=tk.BOTH,expand=0)
        self.save_wash_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.load_wash_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

        self.wash_time_box.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.wash_time_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.wash_time_entry.pack(side=tk.TOP,fill=tk.Y,expand=0)
        
        self.wash_pres_box.pack(side=tk.RIGHT,fill=tk.Y,expand=1)
        self.wash_pres_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.wash_pres_entry.pack(side=tk.TOP,fill=tk.Y,expand=0)


        # CLEAN FRAME PACKING
        self.CLEAN_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.clean_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.clean_controls_box.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.save_clean_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.load_clean_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

        self.clean_time_box.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.clean_time_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.clean_time_entry.pack(side=tk.TOP,fill=tk.Y,expand=0)
        
        self.clean_pres_box.pack(side=tk.RIGHT,fill=tk.Y,expand=1)
        self.clean_pres_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.clean_pres_entry.pack(side=tk.TOP,fill=tk.Y,expand=0)


        # LOCATIONS FRAME PACKING
        self.LOCATIONS_FRAME.pack(side=tk.TOP,fill=tk.BOTH,expand=0)
        self.locations_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        # Sample location packing
        self.sample_location_box.pack(side=tk.TOP,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.sample_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.sample_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.sample_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.sample_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.sample_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Above bath packing
        self.abovebath_location_box.pack(side=tk.TOP,fill=tk.X,expand=1,padx=xpad,pady=ypad)
        self.abovebath_location_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.abovebath_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovebath_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovebath_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovebath_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Cleaning bath location packing
        self.cleanbath_location_box.pack(side=tk.TOP,fill=tk.X,expand=1,padx=xpad,pady=ypad)
        self.cleanbath_location_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.cleanbath_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.cleanbath_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.cleanbath_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.cleanbath_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Wash bath location packing
        self.washbath_location_box.pack(side=tk.TOP,fill=tk.X,expand=1,padx=xpad,pady=ypad)
        self.washbath_location_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.washbath_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.washbath_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.washbath_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.washbath_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        

        # Above clean bath location packing
        self.aboveclean_location_box.pack(side=tk.BOTTOM,fill=tk.X,expand=1,padx=xpad,pady=ypad)
        self.aboveclean_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.aboveclean_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.aboveclean_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.aboveclean_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.aboveclean_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)
        
        # Above wash bath location packing
        self.abovewash_location_box.pack(side=tk.BOTTOM,fill=tk.X,expand=1,padx=xpad,pady=ypad)
        self.abovewash_location_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.abovewash_x_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovewash_y_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovewash_z_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.abovewash_go_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=0)

        # Load and save locations buttons
        self.save_locations_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.load_locations_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)

        # SETTINGS FRAME PACKING
        self.SETTINGS_FRAME.pack(side=tk.TOP,fill=tk.BOTH,expand=1)
        self.settings_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.actuator_box.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.actuator_label.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.sutter_btn.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.scientifica_btn.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        
        self.COM_box.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.COM_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.manip_COM_combo.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

        self.multiclamp_box.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.multiclamp_label.pack(side=tk.LEFT,fill=tk.BOTH,expand=0)
        self.multiclamp_entry.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

        self.help_btn.pack(anchor=tk.SE,expand=0)

        # Pack the tabs
        self.tabs.pack(fill=tk.BOTH,expand=1)
# Define GUI Functions
    def popup_help(self):
        showinfo("Help", instruction_text)

    def validate(self, new_text):
        if not new_text: # the field is being cleared
            self.entered_number = 0
            return True
        try:
            self.entered_number = int(new_text)
            return True
        except ValueError:
            return False

root = tk.Tk()
root.geometry("800x600+50+100") #width x height + x and y screen dims
# root.configure(bg=bg_color)
my_gui = ephysTool(root)
root.mainloop()

'''
    TODO: WITHOUT SUTTER
    - read times/pressures from text() boxes from a list
    - save protocols (to csv)
    - load protocols (from csv)
    - set locations
    - load locations (from csv)
    - save locations (to csv)
    - calculate retracting movements
    - load available COM ports and import to control list
    - determine multiclamp handle
    - save default settings
    - load default settings

    TODO: WITH SUTTER
    - does driver from github work? 
    - will it work without the actual manip? 
    - get position
    - move to position
    - local coordinate frame necessary?? 



    TODO: OPTICAL EPHYS
    - 

    FINISHED: 
    - looks pretty good. 
    

'''