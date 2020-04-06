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
        self.bg_color = 'snow3'
        
        # Notebook
        self.tabs = ttk.Notebook(self.master)

        # DEFINE FRAMES
        self.CLEAN_TAB = tk.Frame(self.tabs, height=50,width=600,bg=self.bg_color,relief=styles[sty],borderwidth=size)
        self.tabs.add(self.CLEAN_TAB,text='Sel ya dir')
        
        self.OPTOEPHYS_TAB = tk.Frame(self.tabs, height=50,width=600,bg=self.bg_color,relief=styles[sty],borderwidth=size)
        self.tabs.add(self.OPTOEPHYS_TAB,text='Optix')

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