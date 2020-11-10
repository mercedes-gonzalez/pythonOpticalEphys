# pythonOpticalEphys (with auto-cleaning) 
Python based GUI for auto-cleaning and all optical electrophysiology.

General Format: 3 tabs
(1) Autocleaning: allows user to do an autocleaning protocol. 
(2) All Optical Electrophysiology: This will become the yolo tab. Right now it's set up to read images instead of the camera because I haven't gotten around to setting it up with the QImaging camera on the rig. 
(3) Help: Just wanted to have an instructions manual basically. 

Code Organization: (optoGUI.py)

1. Import libraries
2. Define general formatting (font sizes, colors, etc)

ephysTool CLASS: 
3. Define Notebook (holds the tabs)
4. Define cleaning tab frames
5. Define cleaning tab widgets (widgets exist inside frames)
6. Define optical ephys tab frames
7. Define optical ephys tab widgets
8. Define help tab 
9. Pack cleaning tab things
10. Pack optical ephys tab things
11. Pack help tab
12. Initialize plot


13. Define GUI functions - I added a little description to each one
14. Main function to build the tkinter window/ main loop

