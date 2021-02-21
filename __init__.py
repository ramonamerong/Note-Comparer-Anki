#Import basic modules
import os

#Import the main window object (mw) from aqt
from aqt import mw

#Import the "show info" tool from utils.py
from aqt.utils import showInfo

#Import all of the Qt GUI library
from aqt.qt import *

#Import local .py modules
from . import Utils, MainWindow
echo = Utils.echo

#This is the function for starting the program
def main():

    #Create the dialog
    parent = mw.app.activeWindow()
    dialog = MainWindow.Dialog(parent)

    #Run the dialog
    dialog.show()


#Create a new menu item
action = QAction("Note Comparer", mw)
#Set it to call the main function when it's clicked
action.triggered.connect(main)
#And add it to the tools menu
mw.form.menuTools.addAction(action)



