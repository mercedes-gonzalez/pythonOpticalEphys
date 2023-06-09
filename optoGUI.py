"""
    Python based GUI for all optical e-phys and auto-cleaning.

    Mercedes Gonzalez. May 2020.
    m.gonzalez@gatech.edu
    Precision Biosystems Lab | Georgia Institute of Technology
    Version Control: https://github.gatech.edu/mgonzalez91/pythonOpticalEphys 

"""
# Import all necessary libraries
import tkinter as tk 
from tkinter import ttk
from tkinter import filedialog
from os import listdir, getcwd
from os.path import isfile, join
import csv
import numpy as np
import scipy as sp
import scipy.signal as sig
import pyabf
import matplotlib.pyplot as plt
import axographio as axo
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from tkinter.messagebox import showinfo, showwarning
from PIL import ImageTk, Image
import random #randomize locations for now
import re # regex 
import time # for sleeps
import cv2
from serial.tools import list_ports
from sutter import Sutter_driver

# GUI Formatting params
# Colors
sample_num = 0
abovebath_num = 1
washbath_num = 2
cleanbath_num = 3
abovewash_num = 4
aboveclean_num = 5
NOCOLOR = False
if NOCOLOR:
    # autocleaning colors
    wash_colors = ['snow','snow3','snow2','snow3','light grey']
    clean_colors = wash_colors
    locations_colors = wash_colors
    settings_colors = wash_colors
    controls_colors = wash_colors
    # optoephys colors
    camera_colors = wash_colors
    plot_colors = wash_colors
    connect_colors = wash_colors
    ephys_settings_colors = wash_colors
    # help tab colors
    help_colors = wash_colors
else:
    # autocleaning colors
    wash_colors = ['lavender','SlateBlue1','SlateBlue2','SlateBlue3','SlateBlue4']
    clean_colors = ['lavender','MediumPurple1','MediumPurple2','MediumPurple3','MediumPurple4']
    locations_colors = ['alice blue','RoyalBlue1','RoyalBlue2','RoyalBlue3','RoyalBlue4']
    settings_colors = ['thistle','MediumOrchid1','MediumOrchid2','MediumOrchid3','MediumOrchid4']
    controls_colors = ['snow','snow2','snow3','snow4','light grey']
    # optoephys colors
    # camera_colors = ['peach puff','firebrick1','firebrick2','firebrick3','firebrick4'] # don't use red here. 
    camera_colors = ['snow','snow2','snow3','snow4','light grey'] # grey is good
    plot_colors = ['antique white','AntiqueWhite1','AntiqueWhite2','AntiqueWhite3','AntiqueWhite4']
    connect_colors = ['lemon chiffon','goldenrod1','goldenrod2','goldenrod3','goldenrod4']
    ephys_settings_colors = ['light salmon','IndianRed1','IndianRed1','IndianRed1','IndianRed1']
    # help tab colors
    help_colors = ['gray80','gray70','gray50','gray40','gray50']
# color indexing
entryc = 0
btnc = 1
boxc = 2
framec = 3
tabc = 4


# Text formatting
title_str = 'Arial 11 bold'
label_str = 'Arial 9'
btn_str = 'Arial 9 bold'

# other general formatting for boxes in gui
styles = ['flat','raised','sunken','groove','ridge']
boxwidth = 14
sty = 3
size = 3
xpad = 5
ypad = 2
linewidth = 2 # drawing cell contours line width

# strings 
INIT_STATUS_STR = 'Click CLEAN to begin.'
NULL_DIR_STR = "* SET DIRECTORY *"
instruction_text = """
CONTROLS + STATUS:
[CLEAN] Initiates cleaning protocol selected in SETTINGS frame.
[BREAK IN] Performs break in pressure control only. (No manipulator movement)
[STOP] Stops all processes in progress.

WASH
"""
img_name = "temp_img.png"
ROOT_PATH = getcwd()
wid = 550
hei = 550

CF = 0.0625 # conversion factor microsteps-->microns

# Define GUI class
class ephysTool(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self,master)
        master.title("All Optical + Cleaning")
        self.master = master
        # self.getCOMports()

        s = ttk.Style()
        s.configure('TNotebook.Tab', font=('URW Gothic L','12','bold'),foreground="black")

        # Notebook
        self.tabs = ttk.Notebook(self.master)

        # DEFINE CLEANING FRAMES
        self.CLEAN_TAB = tk.Frame(self.tabs,bg=controls_colors[3],relief=styles[sty],borderwidth=size)
        self.tabs.add(self.CLEAN_TAB,text='   | AUTO-CLEANING |   ')
        
        self.CONTROLS_FRAME = tk.Frame(self.CLEAN_TAB,bg=controls_colors[framec],relief=styles[sty],borderwidth=size)
        self.WASH_FRAME = tk.Frame(self.CLEAN_TAB,bg=wash_colors[framec],relief=styles[sty],borderwidth=size)
        self.CLEAN_FRAME = tk.Frame(self.CLEAN_TAB,bg=clean_colors[framec],relief=styles[sty],borderwidth=size)
        self.LOCATIONS_FRAME = tk.Frame(self.CLEAN_TAB,bg=locations_colors[framec],relief=styles[sty],borderwidth=size)
        self.SETTINGS_FRAME = tk.Frame(self.CLEAN_TAB,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)

        # CONTROLS FRAME WIDGETS
        self.controls_title = tk.Label(self.CONTROLS_FRAME, text="CONTROLS + STATUS",font=(title_str),bg=controls_colors[framec])
        self.controls_box = tk.Frame(self.CONTROLS_FRAME,bg=controls_colors[framec],relief=styles[0],borderwidth=1)
        self.clean_btn = tk.Button(self.controls_box,text='CLEAN',font=(btn_str),bg=controls_colors[btnc],command=self.cleanPipette)
        self.done_indicator = tk.Label(self.controls_box, text="DONE",relief=styles[3],font=(label_str),bg='dark green')

        self.status_box = tk.Frame(self.CONTROLS_FRAME,bg=controls_colors[framec],relief=styles[0],borderwidth=1)
        self.status = tk.StringVar()
        self.status.set(INIT_STATUS_STR)
        self.status_display = tk.Label(self.status_box, textvariable=self.status,bg=controls_colors[framec],relief=styles[3])
        self.status_label = tk.Label(self.status_box, text="Status:",font=(label_str),bg=controls_colors[framec])

        self.duration_value = tk.DoubleVar()
        self.duration_value.set(20) # default duration
        self.duration_label = tk.Label(self.controls_box, text="Break In Duration [ms]:",font=(label_str),bg=controls_colors[framec])
        vcmd = self.master.register(self.validate) # we have to wrap the command
        self.duration_entry = tk.Entry(self.controls_box, text=self.duration_value,validate="key", validatecommand=(vcmd, '%P'),bg=controls_colors[entryc])

        self.breakin_btn = tk.Button(self.controls_box,text='BREAK IN',font=(btn_str),bg=controls_colors[btnc])
        self.stop_btn = tk.Button(self.CONTROLS_FRAME,text='STOP',font=(btn_str),bg=controls_colors[btnc],fg='red',command=self.stopCleaning)

        # WASH FRAME WIDGETS
        self.wash_title = tk.Label(self.WASH_FRAME, text="WASH",font=(title_str),bg=wash_colors[framec])
        
        self.wash_time_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[boxc],relief=styles[1],borderwidth=1)
        self.wash_time_label = tk.Label(self.wash_time_box,bg=wash_colors[boxc],text="Time [s]")
        self.wash_time_display = tk.Text(self.wash_time_box,bg=wash_colors[entryc],width=boxwidth)
        self.wash_time_display.insert(tk.INSERT,'3\n10')
        
        self.wash_pres_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[boxc],relief=styles[1],borderwidth=1)
        self.wash_pres_label = tk.Label(self.wash_pres_box,bg=wash_colors[boxc],text="Pressure [mBar]")
        self.wash_pres_display = tk.Text(self.wash_pres_box,bg=wash_colors[entryc],width=boxwidth)
        self.wash_pres_display.insert(tk.INSERT,'-345\n700')

        self.prewash = tk.IntVar()
        self.prewash.set(0)
        self.wash_controls_box = tk.Frame(self.WASH_FRAME,bg=wash_colors[boxc],relief=styles[sty],borderwidth=1)
        self.prewash_btn = tk.Checkbutton(self.wash_controls_box,text='PREWASH',font=(btn_str),bg=wash_colors[boxc],selectcolor=wash_colors[3],indicatoron=1,variable=self.prewash,onvalue=1,offvalue=0)
        self.save_wash_btn = tk.Button(self.wash_controls_box,text='SAVE PROTOCOL',font=(btn_str),bg=wash_colors[btnc],command=lambda: self.saveProtocol('wash'))
        self.load_wash_btn = tk.Button(self.wash_controls_box,text='LOAD PROTOCOL',font=(btn_str),bg=wash_colors[btnc],command=lambda: self.loadProtocol('wash'))

        
        # CLEAN FRAME WIDGETS
        self.clean_title = tk.Label(self.CLEAN_FRAME, text="CLEAN",font=(title_str),bg=clean_colors[framec])
        self.clean_controls_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[boxc],relief=styles[1],borderwidth=1)

        self.clean_time_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[boxc],relief=styles[1],borderwidth=1)
        self.clean_time_label = tk.Label(self.clean_time_box,bg=clean_colors[boxc],text="Time [s]")
        self.clean_time_display = tk.Text(self.clean_time_box,bg=clean_colors[entryc],width=boxwidth)
        self.clean_time_display.insert(tk.INSERT,'5\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n5')
        
        self.clean_pres_box = tk.Frame(self.CLEAN_FRAME,bg=clean_colors[boxc],relief=styles[1],borderwidth=1)
        self.clean_pres_label = tk.Label(self.clean_pres_box,bg=clean_colors[boxc],text="Pressure [mBar]")
        self.clean_pres_display = tk.Text(self.clean_pres_box,bg=clean_colors[entryc],width=boxwidth)
        self.clean_pres_display.insert(tk.INSERT,'-345\n-345\n700\n-345\n700\n-345\n700\n-345\n700\n-345\n700\n700\n')

        self.save_clean_btn = tk.Button(self.clean_controls_box,text='SAVE PROTOCOL',font=(btn_str),bg=clean_colors[btnc],command=lambda: self.saveProtocol('clean'))
        self.load_clean_btn = tk.Button(self.clean_controls_box,text='LOAD PROTOCOL',font=(btn_str),bg=clean_colors[btnc],command=lambda: self.loadProtocol('clean'))

        # LOCATIONS FRAME WIDGETS
        self.locations_title = tk.Label(self.LOCATIONS_FRAME, text="LOCATIONS",font=(title_str),bg=locations_colors[framec])
        self.save_locations_btn = tk.Button(self.LOCATIONS_FRAME,text='SAVE LOCATIONS',font=(btn_str),relief=styles[1],bg=locations_colors[btnc],command=self.saveLocations)
        self.load_locations_btn = tk.Button(self.LOCATIONS_FRAME,text='LOAD LOCATIONS',font=(btn_str),relief=styles[1],bg=locations_colors[btnc],command=self.loadLocations)

        # Sample location
        self.sample_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=0)
        self.sample_location_label = tk.Label(self.sample_location_box, text="Sample Location:",font=(label_str),bg=locations_colors[framec])
        
        # Sample location x
        self.sample_x_value = tk.IntVar()
        self.sample_x_value.set(0)
        self.sample_x_display = tk.Label(self.sample_location_box,bg=locations_colors[boxc],textvariable=self.sample_x_value)

        # Sample location y
        self.sample_y_value = tk.IntVar()
        self.sample_y_value.set(0)
        self.sample_y_display = tk.Label(self.sample_location_box,bg=locations_colors[boxc],textvariable=self.sample_y_value)

        # Sample location z
        self.sample_z_value = tk.IntVar()
        self.sample_z_value.set(0)
        self.sample_z_display = tk.Label(self.sample_location_box,bg=locations_colors[boxc],textvariable=self.sample_z_value)

        # Sample location GO
        self.sample_go_btn = tk.Button(self.sample_location_box,text='GO',font=(btn_str),bg=locations_colors[btnc],command=lambda: self.goToLocation(sample_num))

        # -------------
        # Above baths location
        self.abovebath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=1)
        self.abovebath_location_btn = tk.Button(self.abovebath_location_box, text="Above Bath Location:",font=(btn_str),bg=locations_colors[boxc],command=lambda: self.setLocation(abovebath_num))
        
        # Above baths location x
        self.abovebath_x_value = tk.IntVar()
        self.abovebath_x_value.set(0)
        self.abovebath_x_display = tk.Label(self.abovebath_location_box,bg=locations_colors[boxc],textvariable=self.abovebath_x_value)

        # Above baths location y
        self.abovebath_y_value = tk.IntVar()
        self.abovebath_y_value.set(0)
        self.abovebath_y_display = tk.Label(self.abovebath_location_box,bg=locations_colors[boxc],textvariable=self.abovebath_y_value)

        # Above baths location z
        self.abovebath_z_value = tk.IntVar()
        self.abovebath_z_value.set(0)
        self.abovebath_z_display = tk.Label(self.abovebath_location_box,bg=locations_colors[boxc],textvariable=self.abovebath_z_value)

        # Above baths location GO
        self.abovebath_go_btn = tk.Button(self.abovebath_location_box,text='GO',font=(btn_str),bg=locations_colors[btnc],command=lambda: self.goToLocation(abovebath_num))

        # -------------
        # Wash bath location
        self.washbath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=1)
        self.washbath_location_btn = tk.Button(self.washbath_location_box, text="Wash Bath Location:",font=(btn_str),bg=locations_colors[boxc],command=lambda: self.setLocation(washbath_num))
        
        # Wash bath location x
        self.washbath_x_value = tk.IntVar()
        self.washbath_x_value.set(0)
        self.washbath_x_display = tk.Label(self.washbath_location_box,bg=locations_colors[boxc],textvariable=self.washbath_x_value)

        # Wash bath location y
        self.washbath_y_value = tk.IntVar()
        self.washbath_y_value.set(0)
        self.washbath_y_display = tk.Label(self.washbath_location_box,bg=locations_colors[boxc],textvariable=self.washbath_y_value)

        # Wash bath location z
        self.washbath_z_value = tk.IntVar()
        self.washbath_z_value.set(0)
        self.washbath_z_display = tk.Label(self.washbath_location_box,bg=locations_colors[boxc],textvariable=self.washbath_z_value)

        # Wash bath location GO
        self.washbath_go_btn = tk.Button(self.washbath_location_box,text='GO',font=(btn_str),bg=locations_colors[btnc],command=lambda: self.goToLocation(washbath_num))
        # -------------
        # Clean bath location
        self.cleanbath_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=1)
        self.cleanbath_location_btn = tk.Button(self.cleanbath_location_box, text="Clean Bath Location:",font=(btn_str),bg=locations_colors[boxc],command=lambda: self.setLocation(cleanbath_num))
        
        # Clean bath location x
        self.cleanbath_x_value = tk.IntVar()
        self.cleanbath_x_value.set(0)
        self.cleanbath_x_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[boxc],textvariable=self.cleanbath_x_value)

        # Clean bath location y
        self.cleanbath_y_value = tk.IntVar()
        self.cleanbath_y_value.set(0)
        self.cleanbath_y_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[boxc],textvariable=self.cleanbath_y_value)

        # Clean bath location z
        self.cleanbath_z_value = tk.IntVar()
        self.cleanbath_z_value.set(0)
        self.cleanbath_z_display = tk.Label(self.cleanbath_location_box,bg=locations_colors[boxc],textvariable=self.cleanbath_z_value)

        # Clean bath location GO
        self.cleanbath_go_btn = tk.Button(self.cleanbath_location_box,text='GO',font=(btn_str),bg=locations_colors[btnc],command=lambda: self.goToLocation(cleanbath_num))

        # -------------
        # Above wash bath location
        self.abovewash_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=1)
        self.abovewash_location_label = tk.Label(self.abovewash_location_box, text="Above Wash Location:",font=(label_str),bg=locations_colors[framec])
        
        # Above wash bath location x
        self.abovewash_x_value = tk.IntVar()
        self.abovewash_x_value.set(0)
        self.abovewash_x_display = tk.Label(self.abovewash_location_box,bg=locations_colors[boxc],textvariable=self.abovewash_x_value)

        # Above wash bath location y
        self.abovewash_y_value = tk.IntVar()
        self.abovewash_y_value.set(0)
        self.abovewash_y_display = tk.Label(self.abovewash_location_box,bg=locations_colors[boxc],textvariable=self.abovewash_y_value)

        # Above wash bath location z
        self.abovewash_z_value = tk.IntVar()
        self.abovewash_z_value.set(0)
        self.abovewash_z_display = tk.Label(self.abovewash_location_box,bg=locations_colors[boxc],textvariable=self.abovewash_z_value)

        # Above wash bath location GO
        self.abovewash_go_btn = tk.Button(self.abovewash_location_box,text='GO',font=(btn_str),bg=locations_colors[btnc],command=lambda: self.goToLocation(abovewash_num))

        # -------------
        # Above clean bath location
        self.aboveclean_location_box = tk.Frame(self.LOCATIONS_FRAME,bg=locations_colors[framec],relief=styles[0],borderwidth=1)
        self.aboveclean_location_label = tk.Label(self.aboveclean_location_box, text="Above Clean Location:",font=(label_str),bg=locations_colors[framec])
        
        # Above clean bath location x
        self.aboveclean_x_value = tk.IntVar()
        self.aboveclean_x_value.set(0)
        self.aboveclean_x_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[boxc],textvariable=self.aboveclean_x_value)

        # Above Clean bath location y
        self.aboveclean_y_value = tk.IntVar()
        self.aboveclean_y_value.set(0)
        self.aboveclean_y_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[boxc],textvariable=self.aboveclean_y_value)

        # Above Clean bath location z
        self.aboveclean_z_value = tk.IntVar()
        self.aboveclean_z_value.set(0)
        self.aboveclean_z_display = tk.Label(self.aboveclean_location_box,bg=locations_colors[boxc],textvariable=self.aboveclean_z_value)

        # Above Clean bath location GO
        self.aboveclean_go_btn = tk.Button(self.aboveclean_location_box,text='GO',font=(btn_str),bg=locations_colors[btnc],command=lambda: self.goToLocation(aboveclean_num))

        # -------------
        # SETTINGS FRAME WIDGETS
        self.settings_title = tk.Label(self.SETTINGS_FRAME, text="SETTINGS",font=(title_str),bg=settings_colors[framec])
        
        self.protocol_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.protocol = tk.IntVar()
        self.protocol.set(1)
        self.protocol_label = tk.Label(self.protocol_box, text="Protocol:",font=(label_str),bg=settings_colors[framec])
        self.clean_protocol_btn = tk.Radiobutton(self.protocol_box,text="Clean",variable=self.protocol,value=0,bg=settings_colors[framec])
        self.sham_protocol_btn = tk.Radiobutton(self.protocol_box,text="Sham",variable=self.protocol,value=1,bg=settings_colors[framec])
        
        # Actuator type
        self.actuator_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.actuator_value = tk.IntVar()
        self.actuator_value.set(0)
        self.actuator_label = tk.Label(self.actuator_box, text="Actuator Type:",font=(label_str),bg=settings_colors[framec])
        self.sutter_btn = tk.Radiobutton(self.actuator_box,text="Sutter",variable=self.actuator_value,value=0,bg=settings_colors[framec])
        self.scientifica_btn = tk.Radiobutton(self.actuator_box,text="Scientifica",variable=self.actuator_value,value=1,bg=settings_colors[framec])
        
        # Manipulator COM
        # self.COM_PORT = ''
        self.COM_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.COMS_list = list(list_ports.comports())
        self.manip_COM_combo = ttk.Combobox(self.COM_box,values=self.COMS_list)
        self.COM_label = tk.Label(self.COM_box, text="Manipulator COM: ",font=(label_str),bg=settings_colors[framec])
        if len(self.COMS_list) == 1:
            self.manip_COM_combo.current(0)
            self.sutter = Sutter_driver(port='COM3',baudrate=128000,bytesize=8,stopbits=1)

        # Multiclamp handle
        self.multiclamp_box = tk.Frame(self.SETTINGS_FRAME,bg=settings_colors[framec],relief=styles[sty],borderwidth=size)
        self.multiclamp_handle = tk.IntVar()
        self.multiclamp_handle.set(0)
        self.multiclamp_entry = tk.Entry(self.multiclamp_box, text=self.multiclamp_handle,validate="key", validatecommand=(vcmd, '%P'),bg=settings_colors[entryc])
        self.multiclamp_label = tk.Label(self.multiclamp_box, text="Multiclamp Handle: ",font=(label_str),bg=settings_colors[framec])
        
        # self.help_btn = tk.Button(self.SETTINGS_FRAME,text='Help',bg=settings_colors[btnc],command=self.popup_help)
# --------------------------------------------------------------------
# --------------------------------------------------------------------
#       Optical Electrophysiology Tab
        
        # DEFINE OPTOEPHYS FRAME
        self.OPTOEPHYS_TAB = tk.Frame(self.tabs,bg='snow3',relief=styles[sty],borderwidth=size)
        self.tabs.add(self.OPTOEPHYS_TAB,text='   | OPTIX + EPHYS |   ')

        # OPTOEPHYS FRAMES
        self.CAMERA_FRAME = tk.Frame(self.OPTOEPHYS_TAB,bg=camera_colors[framec],relief=styles[sty],borderwidth=size)
        self.PLOT_FRAME = tk.Frame(self.OPTOEPHYS_TAB,bg=plot_colors[framec],relief=styles[sty],borderwidth=size)
        self.CONNECT_FRAME = tk.Frame(self.OPTOEPHYS_TAB,bg=connect_colors[framec],relief=styles[sty],borderwidth=size)

        # OPTOEPHYS WIDGETS
        # Camera frame widgets
        self.camera_label = tk.Label(self.CAMERA_FRAME, text="CAMERA VIEWPORT",font=(title_str),bg=camera_colors[framec])
        self.camera_canvas = tk.Canvas(self.CAMERA_FRAME, width=wid,height=hei,bg=camera_colors[framec])

        self.my_images = list(["1.png","2.png","3.png","3.png"])
        self.my_image_number = 0

        self.raw_tif = np.array(Image.open(join(ROOT_PATH,'images',self.my_images[self.my_image_number])).convert('L').resize((wid,hei)))
        self.display_tif = ImageTk.PhotoImage(image=Image.fromarray(self.raw_tif))
        self.viewport = self.camera_canvas.create_image(wid/2,hei/2,image=self.display_tif)
        
        # Sample rate
        self.samplerate_box = tk.Frame(self.CAMERA_FRAME,bg=camera_colors[framec],relief=styles[0],borderwidth=1)
        self.samplerate_value = tk.DoubleVar()
        self.samplerate_value.set(100) # default sample rate
        self.samplerate_value.trace_add("write", self.samplerateChange)
        self.samplerate_label = tk.Label(self.samplerate_box, text="Sample Rate [Hz]:",bg=camera_colors[framec])
        vcmd = self.master.register(self.validate) # we have to wrap the command
        self.samplerate_entry = tk.Entry(self.samplerate_box, text=self.samplerate_value,validate="key", validatecommand=(vcmd, '%P'),bg=camera_colors[entryc])

        # plot frame widgets
        self.plots_label = tk.Label(self.PLOT_FRAME, text="PLOTS",font=(title_str),bg=plot_colors[framec])
        
        # plot 
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.PLOT_FRAME)  # A tk.DrawingArea.
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.PLOT_FRAME)
        self.toolbar.update()

        # connect frame widgets
        self.connect_label = tk.Label(self.CONNECT_FRAME, text="CONNECTIONS",font=(title_str),bg=connect_colors[framec])
        
        # Mode selection
        self.mode_str = tk.StringVar()
        self.mode_str.set('Auto [all]') # set default value
        self.mode_box = tk.Frame(self.CONNECT_FRAME,bg=connect_colors[framec],relief=styles[sty],borderwidth=size)
        self.mode_list = ['Auto [all]','Auto [select]','Manual']
        self.mode_combo = ttk.Combobox(self.mode_box,textvariable=self.mode_str,values=self.mode_list)
        self.mode_label = tk.Label(self.mode_box, text="Mode: ",font=(label_str),bg=connect_colors[framec])

        # Camera control (temporarily just reading tifs)
        self.find_fluor_cells = tk.Button(self.CONNECT_FRAME,text='Find Cells',font=(btn_str),bg=connect_colors[btnc],command=self.idFluorescentCells)
        self.next = tk.Button(self.CONNECT_FRAME,text='>',font=(btn_str),bg=connect_colors[btnc],command=self.refreshCamera)
        
        self.threshold_box = tk.Frame(self.CONNECT_FRAME,bg=connect_colors[framec],relief=styles[sty],borderwidth = size)
        self.threshold_label = tk.Label(self.threshold_box, text="Threshold Percentile",font=(label_str),bg=connect_colors[framec])
        self.threshold_var = tk.DoubleVar()
        self.threshold_var.set(97.0)
        self.threshold_perc = tk.Spinbox(self.threshold_box,from_=0,to=100,increment=.5,textvariable=self.threshold_var,bg=connect_colors[btnc],command=self.idFluorescentCells)
        
        self.scolor_box = tk.Frame(self.CONNECT_FRAME,bg=connect_colors[framec],relief=styles[sty],borderwidth = size)
        self.scolor_label = tk.Label(self.scolor_box, text="Color Blending",font=(label_str),bg=connect_colors[framec])
        self.scolor_var = tk.DoubleVar()
        self.scolor_var.set(.034)
        self.sigma_color = tk.Spinbox(self.scolor_box,from_=0,to=10,increment=.005,textvariable=self.scolor_var,bg=connect_colors[btnc],command=self.idFluorescentCells)
        
        self.sspace_box = tk.Frame(self.CONNECT_FRAME,bg=connect_colors[framec],relief=styles[sty],borderwidth = size)
        self.sspace_label = tk.Label(self.sspace_box, text="Spatial Blending",font=(label_str),bg=connect_colors[framec])
        self.sspace_var = tk.DoubleVar()
        self.sspace_var.set(.019)
        self.sigma_space = tk.Spinbox(self.sspace_box,from_=0,to=10,increment=.005,textvariable=self.sspace_var,bg=connect_colors[btnc],command=self.idFluorescentCells)
        
        # DEFINE HELP FRAME
        self.HELP_TAB = tk.Frame(self.tabs,bg='snow3',relief=styles[sty],borderwidth=size)
        self.tabs.add(self.HELP_TAB,text='   | HELP |   ')

        self.instructions_label = tk.Label(self.HELP_TAB, text="Instructions",font=(title_str),bg=help_colors[framec])
        self.help_label = tk.Label(self.HELP_TAB,text=instruction_text,font=(label_str),bg=help_colors[boxc])
# __________________________________________________________________________________________________________
# __________________________________________________________________________________________________________
# ______ PACKING _______


        # CONTROLS FRAME PACKING
        self.CONTROLS_FRAME.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.controls_title.pack(side=tk.TOP,fill=tk.X,expand=1)

        self.controls_box.pack(side=tk.TOP,fill=tk.X,expand=0)
        
        self.stop_btn.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0,padx=xpad,pady=ypad)

        self.clean_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.done_indicator.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.breakin_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=0,padx=xpad,pady=ypad)
        self.duration_label.pack(side=tk.LEFT,fill=tk.Y,expand=0,padx=xpad,pady=ypad)
        self.duration_entry.pack(side=tk.LEFT,fill=tk.Y,expand=0,padx=xpad,pady=ypad)

        self.status_box.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.status_label.pack(side=tk.LEFT,fill=tk.Y,expand=0,padx=xpad,pady=ypad)
        self.status_display.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)



        # CLEAN FRAME PACKING
        self.CLEAN_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.clean_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.clean_controls_box.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.save_clean_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.load_clean_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)

        self.clean_time_box.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.clean_time_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.clean_time_display.pack(side=tk.TOP,fill=tk.Y,expand=0)
        
        self.clean_pres_box.pack(side=tk.RIGHT,fill=tk.Y,expand=1)
        self.clean_pres_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.clean_pres_display.pack(side=tk.TOP,fill=tk.Y,expand=0)

        # WASH FRAME PACKING
        self.WASH_FRAME.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.wash_title.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.wash_controls_box.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=0)
        self.prewash_btn.pack(side=tk.TOP,fill=tk.BOTH,expand=0)
        self.save_wash_btn.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)
        self.load_wash_btn.pack(side=tk.LEFT,fill=tk.BOTH,expand=1,padx=xpad,pady=ypad)

        self.wash_time_box.pack(side=tk.LEFT,fill=tk.Y,expand=1)
        self.wash_time_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.wash_time_display.pack(side=tk.TOP,fill=tk.Y,expand=0)
        
        self.wash_pres_box.pack(side=tk.RIGHT,fill=tk.Y,expand=1)
        self.wash_pres_label.pack(side=tk.TOP,fill=tk.X,expand=0)
        self.wash_pres_display.pack(side=tk.TOP,fill=tk.Y,expand=0)

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

        self.protocol_box.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.protocol_label.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.clean_protocol_btn.pack(side=tk.LEFT,fill=tk.Y,expand=0)
        self.sham_protocol_btn.pack(side=tk.LEFT,fill=tk.Y,expand=0)

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
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
        # OPTOEPHYS PACKING
        self.CAMERA_FRAME.pack(side=tk.LEFT,fill=tk.BOTH,anchor=tk.NW,expand=0,padx=xpad,pady=ypad)
        self.PLOT_FRAME.pack(side=tk.TOP,fill=tk.BOTH,anchor=tk.NE,expand=0,padx=xpad,pady=ypad)
        self.CONNECT_FRAME.pack(side=tk.LEFT,fill=tk.BOTH,anchor=tk.SW,expand=1,padx=xpad,pady=ypad)
        
        # camera frame packing
        self.camera_canvas.pack(side=tk.TOP,expand=0)
        self.camera_label.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.samplerate_box.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.samplerate_label.pack(side=tk.LEFT,expand=0)
        self.samplerate_entry.pack(side=tk.LEFT,fill=tk.X,expand=0)
        
        # plot frame packing
        self.plots_label.pack(side=tk.TOP,fill=tk.X,expand=1,padx=xpad,pady=ypad)
        
        # Pack plot because it's not in a frame
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=1)

        # connections frame packing
        self.connect_label.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)

        self.mode_box.pack(side=tk.TOP,anchor=tk.W,expand=0,padx=xpad,pady=ypad)
        self.mode_label.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)
        self.mode_combo.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)

        self.threshold_box.pack(side=tk.TOP,anchor=tk.W,expand=0,padx=xpad,pady=ypad)
        self.threshold_label.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)
        self.threshold_perc.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)
        
        self.scolor_box.pack(side=tk.TOP,anchor=tk.W,expand=0,padx=xpad,pady=ypad)
        self.scolor_label.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)
        self.sigma_color.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)

        self.sspace_box.pack(side=tk.TOP,anchor=tk.W,expand=0,padx=xpad,pady=ypad)
        self.sspace_label.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)
        self.sigma_space.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)

        self.find_fluor_cells.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)
        self.next.pack(side=tk.LEFT,anchor=tk.E,expand=0,padx=xpad,pady=ypad)

        # self.help_btn.pack(anchor=tk.SE,expand=0,padx=xpad,pady=ypad)
        
        # HELP PACKING
        self.instructions_label.pack(side=tk.TOP,fill=tk.X,expand=0,padx=xpad,pady=ypad)
        self.help_label.pack(side=tk.TOP,fill=tk.BOTH,expand=0,padx=xpad,pady=ypad)
        
        # Pack the tabs
        self.tabs.pack(fill=tk.BOTH,expand=1)

        # After everything is packed, initialize some things: 

        # Configure Plot Initially
        self.ax = self.fig.add_subplot(111)
        self.ax.clear()
        self.ax.set_ylabel('Voltage [mV]')
        self.ax.set_xlabel('Time [s]')
        box = self.ax.get_position()
        self.ax.set_position([box.x0, box.y0, box.width*.75, box.height])

        # Configure COM port communication with sutter
        

# __________________________________________________________________________________________________________________________
# __________________________________________________________________________________________________________________________
#       Define GUI Functions

    def validate(self, new_text):
        # PURPOSE: ensure that the input to a control is a number (otherwise will not accept)
        if not new_text: # the field is being cleared
            self.entered_number = 0
            return True
        try:
            self.entered_number = int(new_text)
            return True
        except ValueError:
            return False

    def samplerateChange(self,*args):
        # PURPOSE: Once the camera is working, this will change the sample rate of the viewport
        print('sample rate changed.')

    def refreshCamera(self):
        # PURPOSE: Changes the image in the pseudo-viewport. Once the camera is working, this can go away
        self.my_image_number += 1

        if self.my_image_number == len(self.my_images):
            self.my_image_number = 0

        self.raw_tif = np.array(Image.open(join(ROOT_PATH,'images',self.my_images[self.my_image_number])).convert('L').resize((wid,hei)))
        self.img = ImageTk.PhotoImage(image=Image.fromarray(self.raw_tif))
        self.camera_canvas.itemconfig(self.viewport,image=self.img)

        # self.idFluorescentCells()

    def idFluorescentCells(self,*args): 
        # PURPOSE: If button is pressed, identify fluorescent cells in the image. Once camera is set up, make sure to change image to camera's image. 
        color_num = 200
        self.raw_tif = np.array(Image.open(join(ROOT_PATH,'images',self.my_images[self.my_image_number])).convert('L').resize((wid,hei)))
        
        row,col = self.raw_tif.shape
        raw_image = self.raw_tif
        
        # Read image (from camera)
        norm_image = raw_image/np.max(raw_image)
        contour_image = raw_image

        # filter to preserve edges, threshold above 97 percentile 'fluorescence', use 2.4% of size for filter size
        bilateral_filtered_image = cv2.bilateralFilter(norm_image.astype('float32'), int(float(self.scolor_var.get())*row), int(float(self.sspace_var.get())*row), int(.019*row))
        ret, masked_image = cv2.threshold(bilateral_filtered_image,np.quantile(norm_image,float(self.threshold_perc.get())/100),1,cv2.THRESH_BINARY)
        
        # find contours from masked image  
        contours, hierarchy = cv2.findContours(masked_image.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

        # detect if cell or not 
        centroids = list()
        for cnt in contours:
            # measure minimum enclosing circle for each contour detected
            (x,y),radius = cv2.minEnclosingCircle(cnt)

            # if contour size is between .05% and 1% of field of view, count as cell
            # also check if min enclosing circle is significantly bigger than contourArea to measure roundness
            if cv2.contourArea(cnt) < .01*row*col and cv2.contourArea(cnt) > .0005*row*col and cv2.contourArea(cnt) > (radius*radius*3.1415*.5):
                cv2.drawContours(contour_image, cnt, -1, (color_num,color_num,color_num), linewidth)

                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                
                centroids.append([cx, cy])
                cv2.drawMarker(contour_image,(cx,cy),(color_num, color_num, color_num), cv2.MARKER_CROSS,10,1)

        self.img = ImageTk.PhotoImage(image=Image.fromarray(contour_image))

        # self.camera_canvas.delete(self.viewport)
        self.camera_canvas.itemconfig(self.viewport,image=self.img)

    def goToLocation(self,loc):
        #PURPOSE: move the manipulator to a location
        if loc == sample_num:
            self.status.set('Moving to sample')
            # moveStr = 
        elif loc == abovebath_num:
            self.status.set('Moving to sample')
        elif loc == cleanbath_num:
            self.status.set('Moving to clean bath')
        elif loc == washbath_num:
            self.status.set('Moving to wash bath')
        elif loc == aboveclean_num:
            self.status.set('Moving to above clean bath')
        elif loc == abovewash_num:
            self.status.set('Moving to above wash bath')
            
        self.sutter.Move2Pos(moveStr)
    def setLocation(self,loc):
        # PURPOSE: get location from controller and convert to array of bytes
        cmdStr = self.sutter.CurrentPos() # full command string sent to controller
        cmdByteStr = bytearray(cmdStr) # split into bytes for easy indexing
        driveNum = cmdByteStr[0]
        xByte = cmdByteStr[1:4]
        yByte = cmdByteStr[5:8]
        zByte = cmdByteStr[9:12]

        # convert to int: must be unsigned, little endian format... units are microsteps
        x_umstep = int.from_bytes(xByte,byteorder='little',signed=False) 
        y_umstep = int.from_bytes(yByte,byteorder='little',signed=False) 
        z_umstep = int.from_bytes(zByte,byteorder='little',signed=False) 

        x_micron = int(x_umstep*CF)
        y_micron = int(y_umstep*CF)
        z_micron = int(z_umstep*CF)

        if loc == abovebath_num:
            self.abovebath_x_value.set(x_micron)
            self.abovebath_y_value.set(y_micron)
            self.abovebath_z_value.set(z_micron)
        elif loc == washbath_num:
            self.washbath_x_value.set(x_micron)
            self.washbath_y_value.set(y_micron)
            self.washbath_z_value.set(z_micron)
        elif loc == cleanbath_num:
            self.cleanbath_x_value.set(x_micron)
            self.cleanbath_y_value.set(y_micron)
            self.cleanbath_z_value.set(z_micron)
        
    def saveLocations(self):
        #PURPOSE: save the locations in the window as a csv for loading later on
        above = np.array((self.abovebath_x_value.get(),self.abovebath_y_value.get(),self.abovebath_z_value.get()),dtype='int32')
        clean = np.array((self.cleanbath_x_value.get(),self.cleanbath_y_value.get(),self.cleanbath_z_value.get()),dtype='int32')
        wash = np.array((self.washbath_x_value.get(),self.washbath_y_value.get(),self.washbath_z_value.get()),dtype='int32')
        all = np.transpose(np.vstack((above,clean,wash)))

        f = filedialog.asksaveasfilename(filetypes=[('Comma separated variable', 'csv')],defaultextension='.csv')
        if f: # asksaveasfile return `None` if dialog closed with "cancel".
            np.savetxt(f, all, delimiter=',', fmt='%s', header='above,clean,wash')
            self.save_text = """ Data saved successfully at """ + f
            self.popup_save(True)
        else:
            self.popup_save(False)
            return
    
    def loadLocations(self):
        # PURPOSE: load locations from a csv
        f = filedialog.askopenfilename(title='Select locations file',filetypes=[('Comma separated variable', 'csv')],defaultextension='.csv')
        contents = np.genfromtxt(f,delimiter=',')
        self.abovebath_x_value.set(int(contents[0][0]))
        self.abovebath_y_value.set(int(contents[1][0]))
        self.abovebath_z_value.set(int(contents[2][0]))
        
        self.cleanbath_x_value.set(int(contents[0][1]))
        self.cleanbath_y_value.set(int(contents[1][1]))
        self.cleanbath_z_value.set(int(contents[2][1]))
        
        self.washbath_x_value.set(int(contents[0][2]))
        self.washbath_y_value.set(int(contents[1][2]))
        self.washbath_z_value.set(int(contents[2][2]))
    
    def updateProtocolDisplay(self,protocol_type):
        #PURPOSE: updates the protocol display with new values
        if protocol_type == 'clean':
            # Clear display
            self.clean_time_display.delete(1.0,tk.END)
            self.clean_pres_display.delete(1.0,tk.END)

            # Update with new values
            self.setProtocol(self.clean_time_value, self.clean_pres_value,'clean')
            for t in self.clean_time_value:
                self.clean_time_display.insert(tk.INSERT,str(t)+"\n")
            for p in self.clean_pres_value:
                self.clean_pres_display.insert(tk.INSERT,str(p)+"\n")
        else: # wash
            # Clear display
            self.wash_time_display.delete(1.0,tk.END)
            self.wash_pres_display.delete(1.0,tk.END)

            # Update with new values
            self.setProtocol(self.wash_time_value, self.wash_pres_value,'wash')
            for t in self.wash_time_value:
                self.wash_time_display.insert(tk.INSERT,str(t)+"\n")
            for p in self.wash_pres_value:
                self.wash_pres_display.insert(tk.INSERT,str(p)+"\n")

    def setProtocol(self,time,pres,protocol_type):
        # PURPOSE: saves the inputs from the user to a variable
        if protocol_type == 'clean':
            self.clean_time_value = time
            self.clean_pres_value = pres
            
        else: # wash
            self.wash_time_value = time
            self.wash_pres_value = pres
        
    def loadProtocol(self,protocol_type):
        # PURPOSE: loads cleaning/washing protocol from csv 
        # Read file and parse
        name = filedialog.askopenfilename(title='Select protocol file',filetypes=[('Comma separated variable', 'csv')],defaultextension='.csv')
        f = open(name,"r")
        data = f.read()
        tempdata = re.split("\n",data)
        
        # Split by , ... Remove empty strings... map to integers! 
        temptime = list(map(int,list(filter(None,re.split(",",tempdata[1])))))
        temppres = list(map(int,list(filter(None,re.split(",",tempdata[3])))))
        
        # Error catching: vectors must be same length
        if len(temptime) != len(temppres):
            showwarning("Warning","Time and pressure inputs from the selected file are not the same length. Please check the file and try again.")
            return

        # Update variable value from csv
        self.setProtocol(temptime,temppres,protocol_type)
        # Update display
        self.updateProtocolDisplay(protocol_type)
    
    def updateProtocolValue(self,protocol_type): 
        # PURPOSE: whenever user changes protocol, update its variable
        if protocol_type == 'clean':
            self.clean_time_value = re.sub("\n",",",self.clean_time_display.get(1.0,tk.END)) + "\n"
            self.clean_pres_value = re.sub("\n",",",self.clean_pres_display.get(1.0,tk.END)) + "\n"
        else: # wash protocol
            self.wash_time_value = re.sub("\n",",",self.wash_time_display.get(1.0,tk.END)) + "\n"
            self.wash_pres_value = re.sub("\n",",",self.wash_pres_display.get(1.0,tk.END)) + "\n"
        
    def saveProtocol(self,protocol_type):
        #PURPOSE: save the wash/clean protocol as a csv
        if protocol_type == 'clean':
            self.updateProtocolValue('clean')
            temptime = self.clean_time_value
            temppres = self.clean_pres_value
        else: # wash 
            self.updateProtocolValue('wash')
            temptime = self.wash_time_value
            temppres = self.wash_pres_value

        # Error catching: vectors must be same length
        if len(temptime) != len(temppres):
            showwarning("Warning","Time and pressure inputs are not the same length. Please adjust inputs and try again.")
        else: # vectors are same length, so write file
            name = filedialog.asksaveasfilename(filetypes=[('Comma separated variable', 'csv')],defaultextension='.csv')
            f = open(name,"w")
            f.write('Time [s]\n')
            f.write(temptime)
            f.write('Pressure [mBar]\n')
            f.write(temppres)
            f.close()

    def cleanPipette(self):
        # PURPOSE: do the cleaning protocol 
        showinfo("Ready?",'Make sure that the pipette is at a safe location above the sample. Then press OK.')

        self.status.set('Initializing cleaning protocol...')
        # # time.sleep(2)

        # self.status.set('Moving laterally to baths...')
        # # time.sleep(2)

        # self.status.set('Axial movement to bath ...')
        # # time.sleep(2)
        
        # self.status.set('Dip in bath...')
        # # time.sleep(2)
        self.done_indicator.configure(background='green2')

    def stopCleaning(self):
        # PURPOSE: Stop everything (like estop)
        self.done_indicator.configure(background='red')
        self.done_indicator.configure(text='USER STOPPED')

    def popup_help(self):
        # Was going to make the help info a popup but I like it better as a tab because we have more real estate there.
        # This could be used for something else though. 
        showinfo("Help", instruction_text)

    def popup_save(self,saved):
        # PURPOSE: let user know that the data was or was not saved successfully. 
        if saved == False:
            showwarning("Warning","Data was not saved.")
        else:
            showinfo("Save Successful", self.save_text)
    
root = tk.Tk()
root.geometry("1000x700+500+50") #width x height + x and y screen dims
# root.configure(bg=bg_color)
my_gui = ephysTool(root)
root.mainloop()

'''
    TODO: WITHOUT SUTTER
    - calculate retracting movements
    - determine multiclamp handle
    - save default settings
    - load default settings

    TODO: WITH SUTTER

    TODO: OPTICAL EPHYS
    - read image files with button 
    - auto all mode: detect cells and populate list
    - auto select mode: detect cells, select ones to test. 
    - manual mode: draw cells (click centroid, slide control to change diam.)
    - label cells in all modes

    FINISHED: 
    - get position
    - move to position
    - does driver from github work? yes! wooo
    - load available COM ports and import to control list
    - set locations
    - looks pretty good. 
    - load locations (from csv)
    - save locations (to csv)
    - buttons have bold text, text entries are white, labels are not bold. 
    - read times/pressures from text() boxes from a list
    - save protocols (to csv)
    - load protocols (from csv)
    

'''
