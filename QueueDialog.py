#Import basic modules
import os

#Import basic modules
import os
import re

#Import the main window object (mw) from aqt
from aqt import mw, dialogs

#Import the "show info" tool from utils.py
from aqt.utils import showInfo

#Import all of the Qt GUI library
from aqt.qt import *

#Import local .py modules
from . import Utils
echo = Utils.echo
from . import CustomQt

#Class to instantiate a QueueDialog object
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
        self.queueTable.setColumnCount(self.Comparer.groupNum * 3)
        actions = []
        headers = []
        for i in range(self.Comparer.groupNum):
            headers.extend([f'Group {i+1}: Note fields', 'Action', 'Tag/Replacement'])
            #endIndex = len(self.Comparer.actions) if self.Comparer.groups[i].duplicateAction == 'Tag with...' else len(self.Comparer.actions) - 1
            actions.append(self.Comparer.actions)
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
        for groupIndex in range(self.Comparer.groupNum):
            self.queueTable.horizontalHeader().setSectionResizeMode(0 + groupIndex*3, QHeaderView.Stretch)
            self.queueTable.horizontalHeader().setSectionResizeMode(1 + groupIndex*3, QHeaderView.Fixed)
            self.queueTable.horizontalHeader().setSectionResizeMode(2 + groupIndex*3, QHeaderView.Fixed)
            self.queueTable.horizontalHeader().resizeSection(1 + groupIndex*3, 100)
            self.queueTable.horizontalHeader().resizeSection(2 + groupIndex*3, 100)

        self.triggers = True
                

    # #Method to open note edit window
    # def editNote(self, nID):
    #     browser = dialogs.open("Browser", mw)
    #     browser.form.searchEdit.lineEdit().setText("nid:{}".format(nID))
    #     browser.onSearchActivated()

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
        #fields = QPushButton('<br>'.join([f"<b>{f['name']}:</b> {f['value']}" for f in note['compareFields']]))
        fields.setToolTip('<br>'.join([f"<b>{fName}:</b> {fValue}" for fName, fValue in note['fields'].items()]))
        self.addTableWidget(rowIndex, groupIndex*3, fields)
        #fields.clicked.connect(lambda: self.editNote(note['id']))

        #Create a combobox for the action to be added to the table, add the row index to it,
        #disable the wheel event
        actionBox = QComboBox(self)
        actionBox.rowIndex = rowIndex
        actionBox.groupIndex = groupIndex
        actionBox.addItems(actions[groupIndex])
        actionBox.wheelEvent = lambda event: None
        self.addTableWidget(rowIndex, 1 + groupIndex*3, actionBox)

        #Create a textbox for the replace / tag action and add it to the table
        textBox = QLineEdit(self)
        textBox.rowIndex = rowIndex
        textBox.groupIndex = groupIndex
        self.addTableWidget(rowIndex, 2 + groupIndex*3, textBox)

        #Link the correct lambda functions to the widgets
        actionBox.currentIndexChanged.connect(lambda: self.selectAction(actionBox, textBox))
        textBox.textChanged.connect(lambda: self.enterText(textBox, actionBox))

        #Also select the correct action, which is either a set one or the default one
        action = self.queue[rowIndex][groupIndex].get('action', self.Comparer.groups[groupIndex].duplicateAction)
        actionBox.setCurrentText(action)

        #Update the text box based on the selected action
        self.updateTextBox(rowIndex, groupIndex, textBox, action)

    #Method trigger when an action is selected and it should be updated in it
    def selectAction(self, actionBox, textBox):
        
        if self.triggers == False:
            return
        
        self.triggers = False

        #Retrieve the row index, group index and selected action
        rowIndex = actionBox.rowIndex
        groupIndex = actionBox.groupIndex
        action = actionBox.currentText()
        
        #Update the action in the queue
        self.newAction(rowIndex, groupIndex, action)

        #Update the text field
        self.updateTextBox(rowIndex, groupIndex, textBox, action)

        self.triggers = True
        

    #Method to update the action in the queue
    def newAction(self, rowIndex, groupIndex, action, overWrite = True):
        note = self.queue[rowIndex][groupIndex]

        if overWrite or 'action' not in note:
            note['action'] = action

        return note['action']

    #Method trigger when text is entered
    def enterText(self, textBox, actionBox):
        
        if self.triggers == False:
            return
        
        self.triggers = False

        #Retrieve the row index, group index and selected action
        rowIndex = actionBox.rowIndex
        groupIndex = actionBox.groupIndex
        action = actionBox.currentText()
        
        #Update the text in the queue
        if action == 'Tag with...':
            self.updateText(rowIndex, groupIndex, textBox.text(), 'tag')
        elif action == 'Replace with...':
            self.updateText(rowIndex, groupIndex, textBox.text(), 'replacement')

        self.triggers = True

    #Method to update the entered text
    def updateText(self, rowIndex, groupIndex, text, textType):
        note = self.queue[rowIndex][groupIndex]
        note[textType] = text

    #Method to update the text field based on the selected action
    def updateTextBox(self, rowIndex, groupIndex, textBox, action):
        note = self.queue[rowIndex][groupIndex]
        text = ''
        if action == 'Tag with...':
            text = note['tag']
        elif action == 'Replace with...':
            text = note['replacement']
        textBox.setText(text)

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
