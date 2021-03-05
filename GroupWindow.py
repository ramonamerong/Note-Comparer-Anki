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
from . import Utils, FieldTable
echo = Utils.echo
from . import CustomQt

#Class to instantiate a GroupWindow object
class GroupWindowLayout(QVBoxLayout):

    def __init__(self, Comparer, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        #Config variables
        self.tableClearable = True
        self.triggers = True

        #Create a new group object and add it to the comparer
        self.groupIndex = Comparer.addGroup()
        self.group = Comparer.groups[self.groupIndex]

        #Create and add widgets to this layout group window
        self.title = QLabel(f"<b>Group {self.groupIndex + 1}</b>", parent)
        self.title.setAlignment(Qt.AlignCenter)
        self.addWidget(self.title)

        #Add widget to select group type and link trigger method
        self.groupTypeLabel = QLabel('Choose whether you want to group notes by deck, note type or tag(s).  ', parent)
        self.addWidget(self.groupTypeLabel)
        self.groupTypeBox = QComboBox(parent)
        self.groupTypeBox.addItems(['Deck', 'Note type', 'Tags'])
        self.groupTypeBox.currentTextChanged.connect(self.selectGroupType)
        self.addWidget(self.groupTypeBox)

        #Add widgets to select group name / tags
        self.groupNameLabel = QLabel('Choose the exact deck, note type or tag(s) to group notes by.', parent)
        self.addWidget(self.groupNameLabel)

        self.groupNameBox = QComboBox(parent)
        self.addWidget(self.groupNameBox)
        self.groupNameBox.currentTextChanged.connect(self.selectGroupName)

        self.groupTagsBox = CustomQt.CheckableComboBox(parent)
        self.groupTagsBox.addItems(self.group.fieldInfo['Tags'].keys())
        self.groupTagsBox.currentTextChanged.connect(self.selectGroupTags)
        self.addWidget(self.groupTagsBox)

        #Add widget to select duplicate action and link trigger method
        self.duplicateActionLabel = QLabel('Choose the default action for duplicate notes in a group.', parent)
        self.addWidget(self.duplicateActionLabel)
        self.duplicateActionBox = QComboBox(parent)
        self.duplicateActionBox.addItems(Comparer.actions)
        self.addWidget(self.duplicateActionBox)
        self.duplicateActionBox.currentTextChanged.connect(self.selectDuplicateAction)

        #Add widget with autocompleter to enter a tag for the duplicate action
        self.tagBox = QLineEdit(parent)
        completer = QCompleter(self.group.fieldInfo['Tags'].keys(), parent)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.tagBox.setCompleter(completer)
        self.tagBox.setPlaceholderText('Enter an existing tag or a new one.')
        self.addWidget(self.tagBox)
        self.tagBox.textChanged.connect(self.enterTag)

        #Add widget to enter a replacement for the duplicate action
        self.replaceBox = QLineEdit(parent)
        self.replaceBox.setPlaceholderText('Enter a replacement for the first field (hover for more info).')
        self.replaceBox.setToolTip('''The replacement for the first selected field\
        can either be normal text or a reference to a field value.\
        This is of the form '<code>GxFy(Rz)</code>', where '<code>x</code>' is the group,\
        '<code>y</code>' the field and '<code>z</code>' the optional captured group (without parentheses).\
        <br>(Please hover over 'Advanced mode' and 'Regex capture' for more information).''')
        self.addWidget(self.replaceBox)
        self.replaceBox.textChanged.connect(self.enterReplacement)

        #Add a table widget to display the fields
        self.fieldTableLabel = QLabel('Choose the fields to compare with.', parent)
        self.addWidget(self.fieldTableLabel)
        self.fieldTable = FieldTable.FieldTable(self.group, parent)
        self.addWidget(self.fieldTable)

        #Setup the default selection of the group type, name, fields and duplicate action
        self.selectGroupType('Deck')
        self.selectDuplicateAction(self.duplicateActionBox.currentText())
    
    
    #Method trigger to update the group type and the groupName combobox
    def selectGroupType(self, selectedText):
        
        if selectedText != self.group.type and self.triggers:
            
            self.triggers = False

            #When the selected text is not 'Tags', 
            #add the correct group names to the next box and hide the groupTagsBox and show the groupNameBox
            self.group.type = selectedText
            if selectedText != 'Tags':
                names = self.group.fieldInfo[selectedText].keys()
                self.groupNameBox.clear()
                self.groupNameBox.addItems(names)
                self.groupNameBox.setVisible(True)
                self.groupTagsBox.setVisible(False)
                
                self.triggers = True
                self.selectGroupName(self.groupNameBox.currentText())

            #When it is 'Tags', hide the groupNameBox but show the groupTagsBox
            else:
                self.groupTagsBox.setVisible(True)
                self.groupNameBox.setVisible(False)

                self.triggers = True
                self.selectGroupTags(self.groupTagsBox.currentText())

    #Method trigger to update the group name
    def selectGroupName(self, selectedText):
        if selectedText != self.group.name and self.triggers:

            self.triggers = False

            self.group.name = selectedText
            
            #Clear fields if self.tableClearable has been set to true
            if self.fieldTable.tableClearable:
                self.fieldTable.clearFieldRows()
                self.fieldTable.addFieldRow()
                self.fieldTable.tableClearable = False
            
            self.fieldTable.updateFieldRow(0)

            self.triggers = True

    #Method trigger to update the group tags
    def selectGroupTags(self, selectedText):
        
        #Create a tagString of the tags when the selected text isn't empty
        tagString = ''
        if selectedText != '':
            tags = re.split(', ', selectedText)
            tagString = self.group.createGroupTagsFields(tags)

        #Select the tagString as a group name
        self.selectGroupName(tagString)
        
    #Method trigger to update the duplicate action
    #If the option 'Tag with...' or 'Replace with...' is selected, unhide the field where the tag / replacement can be entered
    def selectDuplicateAction(self, selectedText):
        if selectedText != self.group.duplicateAction and self.triggers:
            
            self.triggers = False

            self.group.duplicateAction = selectedText

            #When it is 'Tag with...' show a field to enter a tag
            if selectedText == 'Tag with...':
                self.tagBox.setVisible(True)
                self.replaceBox.setVisible(False)

            #When it is 'Replace with...' show a field to enter a replacement
            elif selectedText == 'Replace with...':
                self.replaceBox.setVisible(True)
                self.tagBox.setVisible(False)

            #When it is not, hide the above fields to enter a tag/replacement
            else:
                self.tagBox.setVisible(False)
                self.replaceBox.setVisible(False)

            self.triggers = True

    #Method trigger to update entered tag for the duplicate action
    def enterTag(self, tag):

        if tag != self.group.duplicateActionTag and self.triggers:
            self.triggers = False
            self.group.duplicateActionTag = tag
            self.triggers = True

    #Method trigger to update entered replacement for the duplicate action
    def enterReplacement(self, replacement):

        if replacement != self.group.duplicateActionReplacement and self.triggers:
            self.triggers = False
            self.group.setduplicateActionReplacement(replacement)
            self.triggers = True

    #Method to enable / disable all of the GUI elements
    def setEnabledAll(self, boolean):
        self.triggers = boolean
        self.title.setEnabled(boolean)

        self.groupTypeLabel.setEnabled(boolean)
        self.groupTypeBox.setEnabled(boolean)

        self.groupNameLabel.setEnabled(boolean)
        self.groupNameBox.setEnabled(boolean)
        self.groupTagsBox.setEnabled(boolean)

        self.duplicateActionLabel.setEnabled(boolean)
        self.duplicateActionBox.setEnabled(boolean)
        self.tagBox.setEnabled(boolean)

        self.fieldTableLabel.setEnabled(boolean)
        self.fieldTable.setEnabledAll(boolean)