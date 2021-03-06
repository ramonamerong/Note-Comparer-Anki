
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
from . import Node

echo = Utils.echo
Node = Node.Node

#Class to instantiate a Group object to represent one group of cards to be used in a Comparer object
#An fieldinfo object is required (create with the static method Comparer::createFieldInfo)
class Group:

    def __init__(self, groupIndex, Comparer):
        self.groupIndex = groupIndex
        self.Comparer = Comparer
        self.fieldInfo = Comparer.fieldInfo
        self.type = ''
        self.name = ''
        self.actions = ['Nothing', 'Delete', 'Suspend', 'Unsuspend', 'Tag with...']
        self.duplicateAction = ''
        self.duplicateActionTag = ''
        self.duplicateActionReplacement = ''
        self.replaceFieldReference = None
        self.fields = []

    #Method to return the currently selected note group field info
    def getSelectedNoteGroup(self):
        try:
            return self.fieldInfo[self.type][self.name]
        except Exception:
            return None

    #Method to return the current fields based on the selected type and name
    def getPossibleFields(self):
        try:
            return self.fieldInfo[self.type][self.name]['fields']
        except Exception:
            return []

    #Method to return a single field based on the index given and the selected type and name
    def getPossibleField(self, fieldIndex):
        try:
            return self.getPossibleFields()[fieldIndex]
        except Exception:
            return None

    #Method to return the field that has been added at this index
    def getFieldRow(self, rowIndex):
        try:
            return self.fields[rowIndex]
        except Exception:
            return None   

    #Method to add or update an field
    def addUpdateFieldRow(self, rowIndex, fieldIndex):
        
        newFieldRow = {'field': self.getPossibleField(fieldIndex), 'regex': ''}
        oldFieldRow = self.getFieldRow(rowIndex)
        
        if oldFieldRow == None:
            self.fields.append(newFieldRow)
        elif newFieldRow['field'] != oldFieldRow['field']:
            self.fields[rowIndex] = newFieldRow

    #Method to remove an added field
    def removeFieldRow(self, rowIndex):
        self.fields.pop(rowIndex)

    #Method to clear all added fields
    def clearFieldRows(self):
        self.fields = []

    #Method to add the fields of a group of tags to the 'Tags' dictionary of the field info
    #if it is still empty
    def createGroupTagsFields(self, tags):

        #Sort the tags on alphabetical order and create a tag string to use as a key
        tags.sort()
        tagString = ' '.join(tags)
        
        #Retrieve all of the ids of the notes
        noteIDs = mw.col.find_notes(' and '.join([f'tag:{t}' for t in tags ]))

        self.createFields(noteIDs, 'Tags', tagString)

        return tagString

    #Method to add fields of the notes selected in the browser to the 'Browser' dictionary
    def createGroupBrowserFields(self, noteIDs):
        numSelections = len(self.fieldInfo['Browser'])
        selectionString = f'Selection {numSelections + 1}'
        self.createFields(noteIDs, 'Browser', selectionString)

        return selectionString

    #Method to add fields into the fieldInfo depending on the given group type and name
    def createFields(self, noteIDs, groupType, groupName):
        echo(len(noteIDs))
        #If the current group name doesn't exist yet in the group type dictionary create it
        if groupName not in self.fieldInfo[groupType]:
            self.fieldInfo[groupType][groupName] = {'fields': [], 'noteIDs': []}
        #Else if the fields array is not empty don't continue
        elif len(self.fieldInfo[groupType][groupName]['fields']) > 0:
            return

        #Loop over all of the notes to determine their note types and thus their fields.
        group = self.fieldInfo[groupType][groupName]
        noteTypeFields = {}
        for noteID in noteIDs:
            note = mw.col.getNote(noteID)
            noteTypeName = self.Comparer.noteTypeIndex[note.mid]
            if noteTypeName not in noteTypeFields:
                noteTypeFields[noteTypeName] = self.fieldInfo['Note type'][noteTypeName]['fields']

        #Then, add these fields to the fields array of the group of tags entry
        #and also add the note IDs to the tag group
        for fields in noteTypeFields.values():
            group['fields'].extend(fields)
        group['noteIDs'].extend(noteIDs)


    #Method to save a replacement action
    def setduplicateActionReplacement(self, replacement):

        #Save the duplicateAction replacement
        self.duplicateActionReplacement = replacement

        #When it is a field reference, break it up, save it and return
        try:
            operandType = Node.operandType(replacement)
            if operandType[0] == 'field':
                self.replaceFieldReference = operandType[1]
                return

        #Otherwise set it to None
        except re.error:
            pass
        self.replaceFieldReference = None
