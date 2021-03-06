#Import basic modules
import os, itertools, math, time, re

#Import the main window object (mw) from aqt
from aqt import mw

#Import the "show info" tool from utils.py
from aqt.utils import showInfo

#Import all of the Qt GUI library
from aqt.qt import *

#Import local .py modules
from . import Utils
from . import Group
from . import Node
echo = Utils.echo
ProgressTimer = Utils.ProgressTimer
Group = Group.Group
Node = Node.Node

#Class to instantiate a Comparer object with all of the methods to compare cards between groups of cards
#and to decide what to do with duplicates
class Comparer(QObject):

    #Setup signals
    finished = pyqtSignal()
    progress = pyqtSignal(int, int, str)
    echo = pyqtSignal(str)
    error = pyqtSignal(str)
    actionsDone = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groupNum = 2
        self.createFieldInfo()
        self.groups = []
        self.advancedMode = False
        self.regexCapture = False
        self.conditionTree = Node('')
        self.conditionString = ''
        self.queue = []
        self.stop = False


    #Method for creating a dictionary with card group types (deck, note_type, card_type and tag),
    #which contain card group names and those contain any fields their cards may have 
    #(except for the tag group type which are only added when requested to save run time)
    def createFieldInfo(self):
        
        #Retrieve the note types (models) and their card types (templates) from the database
        self.fieldInfo = {'Deck': {}, 'Note type': {}, 'Tags': {}, 'Browser': {}}
        self.noteTypeIndex = {}
        for model in mw.col.models.all():

            #Create model index (id -> name)
            self.noteTypeIndex[model['id']] = model['name']

            #Add the note types
            fields = []
            noteTypeInfo = {
                'name': model['name'],
                'id': model['id'],
                'fields': fields,
                'noteIDs': []
            }
            for f in model['flds']:
                fields.append({
                    'name': f['name'],
                    'noteType': noteTypeInfo
                })
            
            self.fieldInfo['Note type'][model['name']] = noteTypeInfo

            # #For every note add all of the card types
            # for cardType in model['tmpls']:
            #     self.fieldInfo['Card type'][cardType['name']] = {
            #         'fields': fields,
            #         'noteType': noteTypeInfo
            #     }

        #Determine all of the decks first
        #Also create a deck index (id -> name)
        self.deckIndex = {}
        for deck in mw.col.decks.all():
            self.fieldInfo['Deck'][deck['name']] = {
                'id': deck['id'],
                'fields': [],
                'noteTypes': {},
                'noteIDs': [],
                'children': mw.col.decks.children(deck['id'])
            }
            self.deckIndex[deck['id']] = deck['name']

        #Then loop over all of the cards to determine which note types occur in the decks
        for row in mw.col.db.execute('select cards.did, notes.mid from cards left join notes on cards.nid = notes.id'):
            did = row[0]
            mid = row[1]
            deckName = self.deckIndex[did]
            noteTypeName = self.noteTypeIndex[mid]
            deck = self.fieldInfo['Deck'][deckName]
            noteType = {}

            #Only add the note type and fields if it does not already exist
            if noteTypeName not in deck['noteTypes']:
                noteType = self.fieldInfo['Note type'][noteTypeName]
                deck['noteTypes'][noteTypeName] = noteType
                deck['fields'].extend(noteType['fields'])
        
        #Since parent decks can have cards associated with them, recursively look for children of any
        #deck and add any not present note types to that deck
        for deckName in self.fieldInfo['Deck'].keys():
            self.fillParentDecks(deckName)

        #Loop over all of the tags to add them to the fieldInfo but don't add any fields yet
        for tag in mw.col.tags.all():
            self.fieldInfo['Tags'][tag] = {'fields': [], 'noteIDs': []}


    #Recursive method to fill any parent decks with their children's
    def fillParentDecks(self, deckName):
        
        #Retrieve the current deck and it's already existing note types
        d = self.fieldInfo['Deck'][deckName]
        noteTypes = d['noteTypes'].copy()

        #Base case: An deck without children
        if len(d['children']) == 0:
            return d['noteTypes']

        #Loop over all children to collect all of the note types present
        for cName, cID in d['children']:
            noteTypes = {**noteTypes, **self.fillParentDecks(cName)}

        #Loop over all the retrieved note types
        #and add the fields of any note type not already contained
        for name, noteType in noteTypes.items():
            if name not in d['noteTypes']:
                d['fields'].extend(noteType['fields'])

        #Assign the retrieved note types to the deck's noteTypes propery
        d['noteTypes'] = noteTypes

        #Return the note types
        return noteTypes

    #Method to add group to the comparer
    def addGroup(self):
        self.groups.append(Group(len(self.groups), self))
        return len(self.groups) - 1

    #Method to load note ids into the currently selected fields.
    #Must be carried out before the method 'run'
    def getNoteIDs(self):
        
        #Retrieve all of the note IDs per group and assign them
        #to the currently selected name if not already present
        for i in range(len(self.groups)):
            group = self.groups[i]
            noteGroupIDs = group.getSelectedNoteGroup()['noteIDs']

            #If there are already note IDs present, continue
            if len(noteGroupIDs) > 0:
                continue

            #Depending on the chosen type the IDs are retrieved differently
            if self.groups[i].type == 'Deck':
                noteIDs = mw.col.find_notes(f'deck:"{group.name}"')
                noteGroupIDs.extend(noteIDs)
            if self.groups[i].type == 'Note type':
                noteIDs = mw.col.find_notes(f'note:"{group.name}"')
                noteGroupIDs.extend(noteIDs)

            #This is disabled for tags, since this is already saved when tags are added
            # elif self.groups[i].type == 'Tags':
            #     tags = self.groups[i].name.split(' ')
            #     tags = ['tag:' + t for t in tags]
            #     tagsQuery = ' and '.join(tags)
            #     noteGroupIDs.append(mw.col.find_notes(tagsQuery))

    #Method to turn a note object into a dictionary with all the necessary information
    def getNoteDict(self, note, groupIndex):

        #Retrieve the note
        note = {'id': note.id, 'noteTypeID': note.mid, 'fields': dict(note.items()), 
        'tags': note.tags, 'compareFields': [], 'replacement': '', 'tag': ''}

        #Retrieve all the compare fields to be set
        compareFields = self.groups[groupIndex].fields
        for f in compareFields:

            #If either the note doesn't have the set field or
            #the set field's note type doesn't match the note's note type id
            #the field value should be false
            fieldName = f['field']['name']
            fieldValue = note['fields'].get(fieldName, False)
            fieldNoteTypeID = f['field']['noteType']['id']
            if fieldNoteTypeID != note['noteTypeID']:
                fieldValue = False
                fieldNoteTypeID = False

            compareField = {
                'name': fieldName,
                'value': fieldValue.strip() if isinstance(fieldValue, str) else fieldValue,
                'noteTypeID': fieldNoteTypeID,
                'groups': None,
            }

            #When regex capture is enabled, try to save the matched groups
            if self.regexCapture:
                try:
                    match = re.search(f['regex'], fieldValue)
                except re.error:
                    raise re.error(f'The regular expression \'{f["regex"]}\' of the field \'{fieldName}\' is invalid.')
                if match != None:
                    groups = match.groups()
                    compareField['groups'] = groups if len(groups) > 0 else None
            note['compareFields'].append(compareField)

        #Return the note
        return note

    #Method to compare all groups and add any duplicate note combinations to the queue
    #Must be run in a thread when using a GUI to prevent it from freezing
    def run(self):
        try:

            #Determine the least number of fields that are compared.
            #When this is 0, one of the groups have no fields set, and an Exception is raised
            self.shortestLength = min(*[len(g.fields) for g in self.groups])
            if self.shortestLength == 0:
                raise IndexError('One or more groups have no fields set.')
                
            #Clean the current queue
            self.queue = []

            #Retrieve the note IDs per group into a single array
            noteGroups = [g.getSelectedNoteGroup()['noteIDs'].copy() for g in self.groups]
            
            #When not at least two of the groups have notes), raise an Exception
            for notes in noteGroups:
                if len(notes) == 0:
                    raise IndexError('Some groups do not contain any notes.')

            #Create a progress timer and link the local progress event to it
            progressTimer = ProgressTimer(0, '', 3)
            progressTimer.progress.connect(self.progress.emit)

            #Create a dictionary for every note and add the fields that need to be compared, along with
            #any regex if set
            for groupIndex in range(self.groupNum):
                
                notes = noteGroups[groupIndex]

                #Restart the timer for every group
                numNotes = len(notes)
                progressTimer.restart(numNotes, f'Loading notes of group {groupIndex+1}')

                #Create every note dictionary with the correct fields for this group
                for i in range(numNotes):
                    nid = notes[i]
                    notes[i] = self.getNoteDict(mw.col.getNote(nid), groupIndex)
                    progressTimer.emitIntervalProgress(i+1)

                #Check if the thread should be terminated
                if self.stop:
                    return

            #Make an array with all possible combinations by index
            combinations = itertools.product(*[range(len(ng)) for ng in noteGroups])
            
            #Calculate the number of combinations and set the start variables for the loop
            numComb = 1
            for ng in noteGroups:
                numComb *= len(ng)
            #self.echo.emit(str(numComb))
            completed = 0
            progressTimer.restart(numComb, 'Comparing notes...')

            #Compare all the notes of every group to every note in every other group by iterating over the combinations array
            #and add any duplicates to the queue
            for noteIndices in combinations:

                #Retrieve the correct notes by their indexes
                notes = []
                for i in range(self.groupNum):
                    notes.append(noteGroups[i][noteIndices[i]])

                #Check for duplicates for these notes, if present, add a replacement if the field is set and add them to the queue
                if self.checkDuplicate(notes):
                    self.addReplacement(notes)
                    self.queue.append(notes)

                #Emit the progress signal every 1 seconds
                #To pass on the percentage and time left
                completed += 1
                progressTimer.emitIntervalProgress(completed)

                #Check if the thread should be terminated
                if self.stop:
                    return


        #When an IndexError is thrown, inform the user
        except IndexError as e:
            self.error.emit(f'Something went wrong: {e}')

        #When done, emit the finished signal
        self.finished.emit()

    #Method to check for duplicate notes in a given array. 
    #Returns 'True' if it are duplicates
    def checkDuplicate(self, notes):

        #Check if all of the IDs are unique, if not return false
        noteIDs = [n['id'] for n in notes]
        if len(noteIDs) != len(set(noteIDs)):
            return False

        #If advanced mode is enabled, return 'True' if all set conditions are met
        if self.advancedMode:
            return self.conditionTree.solve(notes)
            
        #If advanced mode is disabled, return 'True' if all of the set fields with the same number exactly matches
        else:
            
            #Only compare the mininum number of fields by looking at the fields for all of the groups one by one
            duplicatePresent = True
            for rowIndex in range(self.shortestLength):
                if not self.compareFieldRow(rowIndex, notes):
                    duplicatePresent = False
                    break
            
            return duplicatePresent

    #Recursive method to solve the conditions for a group of notes using the condition tree
    def solveConditions(self, notes):
        return self.conditionTree.solve(notes)

    #Method to compare a single field row by looking at the specific field values in the notes, returns 'True' if they all match.
    def compareFieldRow(self, rowIndex, notes):
        duplicatePresent = True

        #Compare the field values
        compareFieldValue = ''
        for groupIndex in range(self.groupNum):
            note = notes[groupIndex]
            fieldValue = note['compareFields'][rowIndex]['value']

            #Save the first field value as the value to compare to
            if groupIndex == 0:
                compareFieldValue = fieldValue
                continue

            #Compare this value to all others
            if fieldValue != compareFieldValue or compareFieldValue == False:
                duplicatePresent = False
                break

        return duplicatePresent

    #Method to add the tag / replacement of the group to the notes
    def addReplacement(self, notes):
        for groupIndex in range(len(notes)):

            #Save the tag
            group = self.groups[groupIndex]
            note = notes[groupIndex]
            note['tag'] = group.duplicateActionTag

            #When the field reference is 'None' and a replacement is set
            #it is just a string so save it into the note
            if group.replaceFieldReference == None and group.duplicateActionReplacement != '':
                note['replacement'] = group.duplicateActionReplacement
            
            #Otherwise try to retrieve the field value from the other notes and save it if it is valid
            else:
                replacement = Node.getFieldValue(notes, group.replaceFieldReference)
                if replacement != False:
                    note['replacement'] = replacement

    #Method to perform the set actions on the cards in the queue
    def performActions(self, maxRows):

        #Loop over all the notes in every row and perform the appropiate actions on it
        breaked = False
        for rowIndex, row in enumerate(self.queue):
            for groupIndex, note in enumerate(row):
                action = note.get('action', self.groups[groupIndex].duplicateAction)

                #Try to retrieve the note, when it is not found, skip it
                try:
                    noteObject = mw.col.getNote(note['id'])
                except:
                    continue

                #Perform the appropiate action
                if action == 'Delete':
                    mw.col.remNotes([noteObject.id])
                elif action == 'Suspend':
                    for card in noteObject.cards():
                        card.queue = -1
                        card.flush()
                elif action == 'Unsuspend':
                    for card in noteObject.cards():
                        card.queue = 0
                        card.flush()
                elif action == 'Tag with...':
                    #tag = self.groups[groupIndex].duplicateActionTag
                    tag = note['tag']
                    if tag != '':
                        noteObject.addTag(tag)
                        noteObject.flush()
                elif action.startswith('Replace'):

                    #Retrieve the field number of the field in question
                    match = re.search(r'F(\d+)', action)
                    if match != None:
                        fieldNum = int(match.group(1))

                        #Only save the replacement when the replacement is not an empty string
                        #and the compare field value is not 'False'
                        #since it is otherwise not a field that is present in the note
                        field = note['compareFields'][fieldNum - 1]
                        if field['value'] != False and note['replacement'] != '':
                            noteObject[field['name']] = note['replacement']
                            noteObject.flush()

            #When the number of rows exceeds the max
            #replace the current queue for the remaining items
            #and break out of the loop
            #and emit the actionsDone event
            if rowIndex + 1 >= maxRows:
                breaked = True
                self.queue = self.queue[rowIndex + 1 : len(self.queue)]
                echo('Done')
                self.actionsDone.emit()
                break

        #Let the user know it is done
        if breaked == False:
            echo('Done')
