"""
    Python based GUI for all optical e-phys and auto-cleaning.

    Mercedes Gonzalez. March 2020. 
    m.gonzalez@gatech.edu
    Precision Biosystems Lab | Georgia Institute of Technology
    Version Control: https://github.gatech.edu/mgonzalez91/patchingAnalysis

"""

# Import all necessary libraries
import tkinter as tk 
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
from patchAnalysis import * 
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
class patchAnalysisTool(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self,master)
        master.title("Patching Analysis Tool")
        self.master = master
        self.bg_color = 'snow3'

        # DEFINE FRAMES
        self.DIR_FRAME = tk.Frame(self.master, height=50,width=600,bg=self.bg_color,relief=styles[sty],borderwidth = size)
        self.LIST_FRAME = tk.Frame(self.master, height=300,width=200,bg=self.bg_color,relief=styles[sty],borderwidth = size)
        self.MODE_FRAME = tk.Frame(self.master, height=100,width=200,bg=self.bg_color,relief=styles[sty],borderwidth = size)
        self.CONTROLS_FRAME = tk.Frame(self.master, height=100,width=100,bg=self.bg_color,relief=styles[sty],borderwidth = size)
        self.INSTR_FRAME = tk.Frame(self.master, height=100,width=100,bg=self.bg_color,relief=styles[sty],borderwidth = size)
        
        # PLOTTING (no frame)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)  # A tk.DrawingArea.
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.toolbar.update()

        # Variables for plotting later on
        self.input_cmd = np.empty((1,1))
        self.AP_count = np.empty((1,1))
        self.input_dur = np.empty((1,1))    

        # DIRECTORY frame
        self.directory = NULL_DIR_STR
        self.directory_label_text = tk.StringVar()
        self.directory_label_text.set(self.directory)
        self.directory_display = tk.Label(self.DIR_FRAME, textvariable=self.directory_label_text)
        self.directory_label = tk.Label(self.DIR_FRAME, text="Directory:")

        # Capacitance
        self.cap_value = tk.DoubleVar()
        self.cap_value.set(20) # default capactiance
        self.cap_value.trace_add("write", self.capChange)
        self.cap_label = tk.Label(self.CONTROLS_FRAME, text="Capacitance [pF]:")
        vcmd = self.master.register(self.validate) # we have to wrap the command
        self.cap_entry = tk.Entry(self.CONTROLS_FRAME, text=self.cap_value,validate="key", validatecommand=(vcmd, '%P'))

        # LIST frame
        self.abffile_box = tk.Listbox(self.LIST_FRAME,selectmode=tk.EXTENDED) #yscrollcommand=scrollbar.set)
        self.scrollbar = tk.Scrollbar(self.LIST_FRAME)
        self.scrollbar['command'] = self.abffile_box.yview
        self.abffile_box['yscrollcommand'] = self.scrollbar.set
        self.file_selection = [self.abffile_box.get(i) for i in self.abffile_box.curselection()]

        # MODE frame
        self.mode = tk.IntVar() # 0 is auto, 1 is manual
        self.mode.set(0)
        self.modes = {"Auto" : "0", "Manual" : "1"}
        self.mode.trace_add("write", self.modeChange)

        # Buttons
        self.auto_button = tk.Radiobutton(self.MODE_FRAME,text="Auto",variable=self.mode,value=0)
        self.manual_button = tk.Radiobutton(self.MODE_FRAME,text="Manual",variable=self.mode,value=1)

        # CONTROLS frame
        self.select_button = tk.Button(self.CONTROLS_FRAME, text="Select", command=lambda: self.update("select"))
        self.reset_button = tk.Button(self.CONTROLS_FRAME, text="Reset", command=lambda: self.update("reset"))
        self.save_button = tk.Button(self.CONTROLS_FRAME, text=" Save ", command=lambda: self.update("save"))

        # INSTRUCTIONS frame
        self.help_button = tk.Button(self.INSTR_FRAME, text="Help", command=self.popup_help)
        
        # COLORING
        self.abffile_box.configure(background='snow2')
        self.directory_display.configure(background=self.bg_color)
        self.directory_label.configure(background=self.bg_color)
        self.cap_label.configure(background=self.bg_color)
        self.auto_button.configure(background=self.bg_color)
        self.manual_button.configure(background=self.bg_color)
        self.save_button.configure(background=self.bg_color)
        self.reset_button.configure(background=self.bg_color)
        self.help_button.configure(background=self.bg_color)
        self.select_button.configure(background=self.bg_color)

        # Pack plot because it's not in a frame
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar.pack(side=tk.TOP,fill=tk.BOTH,expand=1)

        # LAYOUT PACKING
        self.DIR_FRAME.pack(side=tk.TOP,fill=tk.BOTH)
        self.LIST_FRAME.pack(side=tk.LEFT,fill=tk.BOTH)
        self.CONTROLS_FRAME.pack(side=tk.RIGHT,fill=tk.Y)
        self.MODE_FRAME.pack(side=tk.RIGHT,fill=tk.Y)
        self.INSTR_FRAME.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        
        self.directory_label.pack(side=tk.LEFT,expand=0)
        self.directory_display.pack(side=tk.LEFT,expand=0)
        self.abffile_box.pack(side=tk.LEFT,fill=tk.Y)
        self.scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
        self.cap_label.pack(side=tk.TOP,expand=0)
        self.cap_entry.pack(side=tk.TOP,fill=tk.X,expand=0)

        self.auto_button.pack(side=tk.TOP,fill=tk.Y,expand=1,anchor=tk.W)
        self.manual_button.pack(side=tk.TOP,fill=tk.Y,expand=1,anchor=tk.W)

        self.select_button.pack(side=tk.TOP,fill=tk.BOTH,expand=0)
        self.reset_button.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.save_button.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        
        self.help_button.pack(anchor=tk.SE)

        # Configure Plot Initially
        self.ax = self.fig.add_subplot(111)
        self.ax.clear()
        self.ax.set_ylabel('Firing Frequency [Hz]')
        self.ax.set_xlabel('Current Density [pA/pF]')
        box = self.ax.get_position()
        self.ax.set_position([box.x0, box.y0, box.width*.75, box.height])

        # Check for change in selection and new files in directory
        self.poll()
        self.probeForNewFiles()

# Define GUI Functions
    def popup_help(self):
        showinfo("Help", instruction_text)

    def popup_save(self,saved):
        if saved == False:
            showwarning("Warning","Data was not saved.")
        else:
            showinfo("Save Successful", self.save_text)
      
    def poll(self):
        now = self.abffile_box.curselection()
        if now != self.file_selection:
            self.file_selection = now
            self.modeChange()
            self.canvas.draw()  
        self.after(100, self.poll)

    def probeForNewFiles(self):
        if self.directory != NULL_DIR_STR:
            now = [f for f in listdir(self.directory) if isfile(join(self.directory, f)) & f.endswith(".abf")]
            if now != self.abf_files:
                self.abf_files = now
                # Remove all files and add new file list back in
                self.abffile_box.delete(0,tk.END)
                for abf in self.abf_files:
                    self.abffile_box.insert(tk.END,abf)
                self.updatePlot()
                self.canvas.draw()
        self.after(2000, self.probeForNewFiles)

    def updatePlot(self):
        self.ax = self.fig.add_subplot(111)
        self.ax.clear()
        self.ax.set_ylabel('Firing Frequency [Hz]')
        self.ax.set_xlabel('Current Density [pA/pF]')
        
        abf = pyabf.ABF(join(self.directory,self.abf_files[0]))
        # Plot data depending on mode 
        if self.mode.get() == 0: # auto mode 
            for item in self.abf_files:
                self.input_cmd, self.AP_count, self.input_dur = analyzeFile(item,self)
                self.step_time = self.input_dur[0]/abf.dataRate
                self.ax.plot(self.input_cmd/float(self.cap_entry.get()),self.AP_count/self.step_time,"o",label=item) 
        else: # manual mode
            user_selected = self.abffile_box.curselection()
            selected = [self.abf_files[int(item)] for item in user_selected]
            for sel in selected:
                self.input_cmd, self.AP_count, self.input_dur = analyzeFile(sel,self)
                self.step_time = self.input_dur[0]/abf.dataRate
                self.ax.plot(self.input_cmd/float(self.cap_entry.get()),self.AP_count/self.step_time,"o",label=sel)
        self.ax.legend(fancybox=True,shadow=True,bbox_to_anchor=(1, 1),prop={'size':8})
        self.canvas.draw()
        return

    def modeChange(self, *args):
        # Set up plot axes
        self.ax = self.fig.add_subplot(111)
        self.ax.clear()
        self.ax.set_ylabel('Firing Frequency [Hz]')
        self.ax.set_xlabel('Current Density [pA/pF]')

        # If there is a directory selected, update plot, otherwise do nothing. 
        if self.directory != NULL_DIR_STR:
            self.updatePlot()
        self.canvas.draw()

    def capChange(self,*args):
        self.updatePlot()
        self.canvas.draw()

    def validate(self, new_text):
        if not new_text: # the field is being cleared
            self.entered_number = 0
            return True
        try:
            self.entered_number = int(new_text)
            return True
        except ValueError:
            return False

    def update(self, method):
        if method == "select":
            self.directory = filedialog.askdirectory()
            self.directory_label_text.set(self.directory)
            self.abf_files = [f for f in listdir(self.directory) if isfile(join(self.directory, f)) & f.endswith(".abf")]
            for abf in self.abf_files:
                self.abffile_box.insert(tk.END,abf)
            self.updatePlot()
        elif method == "save": # save all data plotted in one csv with a column for filename 
            count = 0
            abf = pyabf.ABF(join(self.directory,self.abf_files[0]))
            self.step_time = self.input_dur[0]/abf.dataRate
            if self.mode.get() == 0: # if in auto mode
                for item in self.abf_files:
                    self.input_cmd, self.AP_count, self.input_dur = analyzeFile(item,self)
                    names = np.vstack(np.array([item]*len(self.input_cmd),dtype='str'))
                    namesInput = np.hstack((names,self.input_cmd/float(self.cap_entry.get())))
                    temp_data = np.hstack((namesInput,self.AP_count/self.step_time)) # concatenate horizontally 
                    count = count + 1
                    if count == 1:
                        all_data = temp_data
                    else:
                        all_data = np.vstack((all_data,temp_data)) # concatenate vertically
            else: # manual mode 
                user_selected = self.abffile_box.curselection()
                selected = [self.abf_files[int(item)] for item in user_selected]
                for sel in selected:
                    self.input_cmd, self.AP_count, self.input_dur = analyzeFile(sel,self)
                    names = np.vstack(np.array([sel]*len(self.input_cmd),dtype='str'))
                    namesInput = np.hstack((names,self.input_cmd/float(self.cap_entry.get())))
                    temp_data = np.hstack((namesInput,self.AP_count/self.step_time)) # concatenate horizontally 
                    count = count + 1 
                    if count == 1:
                        all_data = temp_data
                    else:
                        all_data = np.vstack((all_data,temp_data))
            
            f = filedialog.asksaveasfilename(filetypes=[('Comma separated variable', '.csv')],defaultextension='.csv')
            if f: # asksaveasfile return `None` if dialog closed with "cancel".
                np.savetxt(f, all_data, delimiter=',', fmt='%s', header='Filename, Current Density (pA/pF), Fire Freq (Hz)')
                self.save_text = """ Data saved successfully at """ + f
                self.popup_save(True)
            else:
                self.popup_save(False)
                return
        elif method == "reset":
            # Clear selected directory
            self.directory = NULL_DIR_STR
            self.directory_label_text.set(self.directory)

            # Clear file list
            self.abf_files=[None]
            self.abffile_box.delete(0,tk.END)

            # Clear plot
            self.ax = self.fig.add_subplot(111)
            self.ax.clear()
            self.ax.set_ylabel('Firing Frequency [Hz]')
            self.ax.set_xlabel('Current Density [pA/pF]')
        self.canvas.draw()


root = tk.Tk()
root.geometry("600x600+50+100") #width x height + x and y screen dims
# root.configure(bg=bg_color)
my_gui = patchAnalysisTool(root)
root.mainloop()

'''
    TODO 
    - membtest plot and analysis

    DONE
    - select button to select directory
    - display current directory
    - reset button    
    - read all files from the selected directory
    - display file names in listbox 
    - add plot box
    - interactive plot??? 
    - proper container placement
        - put everything in frames
    - manual vs auto mode 
        - manual means user chooses files 
        - auto means grab all files from directory
    - read data from only selected files
    - plot data from selected files
        - prettify the plot
    - save figure (in toolbar)
    - save data in csv
    - enable auto-updating every 5 seconds
    - add legend with filenames
    - enable capacitance entry 

'''