#Import basic modules
import os
import re

#Import the main window object (mw) from aqt
from aqt import mw

#Import the "show info" tool from utils.py
from aqt.utils import showInfo

#Import all of the Qt GUI library
from aqt.qt import *

#Import local .py modules
from . import Utils
echo = Utils.echo
from . import CustomQt

#Class to instantiate a GroupWindow object
class QueueDialog(QDialog):

    def __init__(self, Comparer, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.Comparer = Comparer
        self.queue = Comparer.queue
        self.triggers = False
        self.maxRows = 1000

        #Create a layout
        self.setWindowTitle("Action Queue")
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        #Add the intro explanation
        self.intro = QLabel('''Below are all of the duplicates found in the groups. You can select an action to perform on each note from the dropdown menu.
            If you want to change the action for all duplicates in a group at once, close this window, select the appropiate action from the dropdown menu        
            and reopen this window by pressing 'show duplicates'. If you hover over a duplicate note you will be able to see all of it's fields.
            Some notes are marked as duplicates multiple times and all of the set actions will therefore be performed upon it''', self)
        self.intro.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.intro)
        
        #Add a table widget to display the queue
        #and determine the available actions per group
        self.queueTable = QTableWidget(self)
        self.queueTable.setColumnCount(self.Comparer.groupNum *2)
        actions = []
        headers = []
        for i in range(self.Comparer.groupNum):
            headers.extend([f'Group {i+1}: Note fields', 'Action'])
            endIndex = len(self.Comparer.actions) if self.Comparer.groups[i].duplicateAction == 'Tag with...' else len(self.Comparer.actions) - 1
            actions.append(self.Comparer.actions[0:endIndex])
        self.queueTable.setHorizontalHeaderLabels(headers)
        self.layout.addWidget(self.queueTable)

        #Add all of the duplicates found as rows
        for rowIndex in range(len(self.queue)):

            #Increase the number of rows in the table by 1
            self.queueTable.setRowCount(rowIndex+1)

            #Add the appropiate widgets for ever group to the row
            for groupIndex in range(self.Comparer.groupNum):
                self.addRow(rowIndex, groupIndex, actions)

            #When the rowIndex exceeds the maximum number of rows,
            #stop adding new rows and attach a message to the explanation
            if rowIndex + 1 >= self.maxRows:
                self.intro.setText(self.intro.text() + 
                f'\n\nSince there are more than {self.maxRows} duplicates, the queue has been broken up.\
                    \nAfter processing the current items the other items can be processed.')
                break

        #Add a button to start the actions
        self.startButton = QPushButton('Perform actions', self)
        self.layout.addWidget(self.startButton)
        self.startButton.clicked.connect(self.askConfirmation)

        #Resize the columns
        self.queueTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queueTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.queueTable.horizontalHeader().resizeSection(1, 80)
        self.queueTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.queueTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.queueTable.horizontalHeader().resizeSection(3, 80)

        self.triggers = True
                

    #Method to add an widget to an table cell
    def addTableWidget(self, rowIndex, columnIndex, widget):
        item = QTableWidgetItem()
        item.widget = widget
        self.queueTable.setItem(rowIndex, columnIndex, item)
        self.queueTable.setCellWidget(rowIndex, columnIndex, widget)

    #Method to add an row:
    def addRow(self, rowIndex, groupIndex, actions):

        #Retrieve the duplicate notes for the row to be added
        note = self.queue[rowIndex][groupIndex]

        #Add a description of the fields and their values to the first column per group
        fields = QLabel('<br>'.join([f"<b>{f['name']}:</b> {f['value']}" for f in note['compareFields']]))
        fields.setToolTip('<br>'.join([f"<b>{fName}:</b> {fValue}" for fName, fValue in note['fields'].items()]))
        self.addTableWidget(rowIndex, groupIndex*2, fields)

        #Create a combobox for the action to be added to the table, add the row index to it,
        #disable the wheel event and link an lambda function to it
        actionBox = QComboBox(self)
        actionBox.rowIndex = rowIndex
        actionBox.groupIndex = groupIndex
        actionBox.addItems(actions[groupIndex])
        actionBox.wheelEvent = lambda event: None
        actionBox.currentIndexChanged.connect(lambda: self.selectAction(actionBox, rowIndex, groupIndex))
        self.addTableWidget(rowIndex, groupIndex*2+1, actionBox)

        #Also select the correct action, which is either a set one or the default one
        action = self.queue[rowIndex][groupIndex].get('action', self.Comparer.groups[groupIndex].duplicateAction)
        actionBox.setCurrentText(action)

    #Method trigger when an action is selected and it should be updated in t
    def selectAction(self, actionBox, rowIndex, groupIndex):
        
        if self.triggers == False:
            return
        
        self.triggers = False

        #Retrieve the row index, group index and selected action
        rowIndex = actionBox.rowIndex
        groupIndex = actionBox.groupIndex
        action = actionBox.currentText()
        
        #Update the action in the queue
        self.newAction(rowIndex, groupIndex, action)

        self.triggers = True

    #Method to update the action in the queue
    def newAction(self, rowIndex, groupIndex, action, overWrite = True):
        note = self.queue[rowIndex][groupIndex]

        if overWrite or 'action' not in note:
            note['action'] = action

        return note['action']

    #Method to ask for conformation for performing the actions by creating a message box
    def askConfirmation(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("All actions have been set and are ready to be performed.")
        msg.setInformativeText("Are you sure you want to perform the set actions on the notes?")
        msg.setWindowTitle("Confirmation")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        res = msg.exec()

        #When the user agrees, close the current window
        #and perform the actions
        if res == QMessageBox.Ok:
            self.accept()
            self.Comparer.performActions(self.maxRows)
