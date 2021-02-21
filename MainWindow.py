#To do
#-enable duplicate note checking
#-enable tree construction general Exception

#Import basic modules
import os, datetime, re

#Import the main window object (mw) from aqt
from aqt import mw

#Import the "show info" tool from utils.py
from aqt.utils import showInfo

#Import all of the Qt GUI library
from aqt.qt import *

#Import local .py modules
from . import GroupWindow, Comparer, Utils, QueueDialog
echo = Utils.echo

#Class which will run a dialog and create a Comparer object when instantiated
#to compare groups of notes for duplicates
class Dialog(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Setup the dialog window and vertical layout
        self.setWindowTitle("Note Comparer")
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        #Create an label for the intro explanation
        self.intro = QLabel(
            'With this add-on you can group notes by a number of ways such as a deck, note type and even multiple tags.\
            \nNotes in different groups can then be marked as duplicates depending on the fields that are selected and an action can be performed on them.\
            \nBy default, notes in different groups are marked as duplicates when their fields with the same number matches.\
            \nYou can disable this and specificy your own conditions for duplicate notes if you enable \'advanced mode\' below.\
			\nHover over \'advanced options\' or \'RegEx capture\' for more explanation.')
        self.intro.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.intro)

        #Create Comparer object and then using the Comparer, create subwindows.
        #Add these to the horizontal group layout which is added to the main layout
        self.Comparer = Comparer.Comparer()
        self.groupWindows = []
        self.groupWindowsLayout = QHBoxLayout(self)

        for i in range(self.Comparer.groupNum):
            self.addGroupWindow()

        self.layout.addLayout(self.groupWindowsLayout)

        #Create toggles for advanced options
        self.advancedCheckBox = QCheckBox('Enable advanced mode', self)
        self.layout.addWidget(self.advancedCheckBox)
        self.advancedCheckBox.stateChanged.connect(self.toggleAdvanced)
        self.advancedCheckBox.setToolTip('''
        <p>Using the text box below, you can manually specificy conditions which determine whether notes from different groups are seen as duplicates.
        To that end, you have to specify which (parts of) fields much match in order for the notes to be seen as duplicates (field values = fields, in this context):</p>
        <ul style='list-style-position: inside'>
            <li>
                Any field can be specified as '<code>GxFy</code>' where '<code>x</code>' and '<code>y</code>' indicate the group number and field number respectively.
                <br><b>Example</b>: '<code>G1F1</code>' means field 1 of group 1.
                <br>Instead of a field you can also specify any text by surrounding it with single quotes (f.e. <code>'example'</code>). 
            </li>
            <li>
                <div>Any pair of fields can be compared as '<code>GxFy [operator] GaFb</code>' (now referred to as a 'condition').
                Possible operators are:</div>
                    <ul>
                        <li>'<code>=</code>': This means that both fields must exactly match for the condition to be seen as '<code>True</code>'. Text in quotes must be on the right side.</li>
                        <li>'<code>in</code>': This means that the field left from the [operator] must be present somewhere in the field to the right for the condition to be '<code>True</code>'. 
                        If the left field is a single word it must also be present as a single word in the right field. Text in quotes must be on the left.</li>
                        <li>'<code>></code>': This means the same as <code>in</code>, but the left field doesn't have to be present as a single word in the right field, but can also be part of a word.</li>
                    </ul>
                <div><b>Example 1</b>: '<code>G1F1 in G2F1</code>' means that field 1 of group 1 needs to be present in field 1 of group 2.</div>
                <div><b>Example 2</b>: '<code>G1F1 = 'ball'</code>' means that field 1 of group 1 match exactly match 'ball'.</div>
                <div><b>Example 3</b>: '<code>'ball' > G1F1</code>' means that the letters 'ball' need to be present in field 1 of group 1, so it can match either 'football' or 'basketball'.</div>
            </li>
            <li>Any number of conditions can be strung together by using:
                <ul>
                    <li>'<code>and</code>': This means that the conditions left and right from '<code>and</code>' must be '<code>True</code>' for this 'group condition' to also be '<code>True</code>'.</li>
                    <li>'<code>or</code>': This means that one of both conditions must be 'True'.</li>
                </ul>
                <div><b>Example</b>: '<code>G1F1 = G2F1 and 'ball' in G1F2</code>' means that the first field of both groups must match
                AND that the word 'ball' must be present in field 2 of group 1. However, it is important to note that conditions are evaluated from left to right,
                so if let's say you have three conditions with the following values in succession '<code>True and False or True</code>',
                the first two conditions '<code>True and False</code>' are together <code>'False'</code> so the whole thing now reads '<code>False or True</code>'. Following that, it is then interpreted as '<code>True</code>'.</div>
            </li>
            <li>Any number of conditions can be given precedence by using parentheses.
                <br><b>Example</b>: '<code>(G1F1 = G2F1 and G1F2 = G2F2) or (G1F3 = G2F3 and G1F4 = G2F4)</code>' means that either fields 1 and 2 must match OR fields 3 and 4
                in order for all of these conditions together to be seen as '<code>True</code>' and the notes to be seen as duplicates.
            </li>
        </ul>''')

        self.regexCheckBox = QCheckBox('Enable RegEx capture for advanced mode', self)
        self.layout.addWidget(self.regexCheckBox)
        self.regexCheckBox.setEnabled(False)
        self.regexCheckBox.stateChanged.connect(self.toggleRegex)
        self.regexCheckBox.setToolTip('''
        <p>If 'RegEx capture' has been enabled, you will be able to specify part(s) for each field instead of the whole field 
        by entering a regular expression in the 'RegEx' boxes and capturing certain parts in parenthesis.
        Any captured group of a field can then be referenced in the box below as '<code>GxFyRz</code>' where '<code>z</code>' is the captured group number.
        If you don't know how regular expressions work, please read about them somewhere in order to use this program's capabilities to the fullest.
        <br><b>Example 1</b>: Let's say I have entered the regular expression '<code>\d{2}-\d{2}-\d{4}</code>' in order to capture the day, month and year field 1 of group 1 called 'date'.
        I can then reference the day, month and year using '<code>G1F1R1</code>', '<code>G1F1R2</code>' and '<code>G1F1R3</code>' respectively.
        <br><br>You can also use an regular expression in the place of a quoted text (even when this option is disabled). You just have to use a forward slash instead of quotes (f.e. <code>/regex/</code>).
        When used in conjuction with the '<code>=</code>' or '<code>in</code>' operators the other field has to match the regular expression either entirely or partly respectively.
        <br><b>Example 2</b>: '<code>/\d/ in G1F1 or G1F2 = /\w/</code>' means that there must be at least a single digit in field 1 or field 2 must be exactly one letter.</p>''')
        
        #Create plaint text edit for manual duplicate conditions
        self.conditionLabel = QLabel("Enter your manual conditions for duplicate notes below.", self)
        self.layout.addWidget(self.conditionLabel)
        self.conditionLabel.setVisible(False)
        
        self.conditionEdit = QPlainTextEdit(self)
        self.layout.addWidget(self.conditionEdit)
        self.conditionEdit.setVisible(False)
        self.conditionEdit.textChanged.connect(self.enterCondition)

        #Add compare button
        self.compareButton = QPushButton('Compare groups', self)
        self.layout.addWidget(self.compareButton)
        self.compareButton.clicked.connect(self.compare)
        self.compareButton.setToolTip('This can take from 10 min up till 1h+ for decks bigger than 1000 notes.')

        #Add invisible button to show the dialog window
        self.queueButton = QPushButton('Show duplicates (this can take a while)', self)
        self.layout.addWidget(self.queueButton)
        self.queueButton.clicked.connect(self.showQueue)
        self.queueButton.setVisible(False)

        #Add progress activity label, bar and time left label
        self.progressActivityLabel = QLabel('', self)
        self.layout.addWidget(self.progressActivityLabel)
        self.progressActivityLabel.setVisible(False)

        self.progressBar = QProgressBar(self)
        self.layout.addWidget(self.progressBar)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(False)

        self.timeLeftLabel = QLabel('', self)
        self.layout.addWidget(self.timeLeftLabel)
        self.timeLeftLabel.setVisible(False)
        
        #Create a thread and add the Comparer object to it
        self.thread = QThread(self)
        self.Comparer.moveToThread(self.thread)

        #Connect the echo and (local) error functions to the echo and error event respectively
        self.Comparer.echo.connect(echo)
        self.Comparer.error.connect(self.error)
        self.errorShown = False

        #Link the thread start method to the Comperator run method
        self.thread.started.connect(self.Comparer.run)

        #During the comparison, update the progress bar
        self.Comparer.progress.connect(self.reportCompareProgress)
        self.Comparer.finished.connect(lambda: self.reportCompareProgress(100, None, 'Done'))

        #When the comparer is finished, end the thread and show the queue
        self.Comparer.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.showQueue)

        #Re-enable all GUI elements and hide/reset the progress report bar + time left label when finished
        self.thread.finished.connect(lambda: self.reset())

        #When all actions have been performed but the queue is not empty yet, reopen the queue dialog
        self.Comparer.actionsDone.connect(lambda: self.showQueue() if len(self.Comparer.queue) > 0 else None) 

        #When the main dialog is closed, terminate any running threads
        self.rejected.connect(self.close)

    #Method to create the layout for a single note group
    def addGroupWindow(self):
        newGroup = GroupWindow.GroupWindowLayout(self.Comparer, self)
        self.groupWindowsLayout.addLayout(newGroup)
        self.groupWindows.append(newGroup)

    #Method trigger to toggle advanced mode
    def toggleAdvanced(self):
        check = self.advancedCheckBox.isChecked()

        self.Comparer.advancedMode = check
        self.conditionLabel.setVisible(check)
        self.conditionEdit.setVisible(check)
        self.regexCheckBox.setEnabled(check)

        if not check:
            self.regexCheckBox.setChecked(check)

    #Method trigger to toggle regex capture
    def toggleRegex(self):

        check = self.regexCheckBox.isChecked()
        self.Comparer.regexCapture = check
        for gw in self.groupWindows: 
            if check:
                gw.fieldTable.showColumn(1)
            else:
                gw.fieldTable.hideColumn(1)

    #Method trigger to save entered conditions
    def enterCondition(self):
        conditions = self.conditionEdit.toPlainText()
        self.Comparer.conditionString = conditions

    #Method trigger to compare all of the cards between the group
    def compare(self):
        
        #Finish the condition tree when the advanced options are enabled
        if self.Comparer.advancedMode:
            try:
                self.Comparer.conditionTree.setString(self.Comparer.conditionString)
                self.Comparer.conditionTree.createChildren()
            except re.error as e:
                self.error(e)
                return
            # except Exception:
            #     self.error('Something went wrong')
            #     return

        # notes = [
        #     {'id': 1, 'compareFields': [{'value': 'lorem', 'groups': ('or',)}, {'value': 'spring op', 'groups': ()}]},
        #     {'id': 2, 'compareFields': [{'value': 'lorem ipsum', 'groups': ()}, {'value': 'spring', 'groups': ()}]}
        # ]
        # echo(f'Answer:{self.Comparer.conditionTree.solve(notes)}')

        #Retrieve all of the note ids
        self.Comparer.getNoteIDs()
        
        #Show the progress bar and time left label
        self.progressActivityLabel.setVisible(True)
        self.progressBar.setVisible(True)
        self.timeLeftLabel.setVisible(True)
        
        #Disable all GUI elements
        self.setEnabledAll(False)

        #Start the thread
        self.thread.start()

    #Method to report the compare progress, which consists of the percentage and time left
    def reportCompareProgress(self, percentage, timeLeft, activity):
        self.progressBar.setValue(percentage)
        self.progressActivityLabel.setText(activity)
        if timeLeft != None:
            self.timeLeftLabel.setText(f'Time left: {str(datetime.timedelta(seconds=timeLeft))}\nDuplicates found: {len(self.Comparer.queue)}')

    #Method to enable / disable all of the GUI elements
    def setEnabledAll(self, boolean):

        #Disable all widgets in the current layout
        self.intro.setEnabled(boolean)
        self.advancedCheckBox.setEnabled(boolean)
        self.regexCheckBox.setEnabled(boolean)
        self.conditionLabel.setEnabled(boolean)
        self.conditionEdit.setEnabled(boolean)
        self.compareButton.setEnabled(boolean)
        self.queueButton.setEnabled(boolean)

        #Disable all widgets per group window
        for gw in self.groupWindows:
            gw.setEnabledAll(boolean)

    #Method to show error message to the user
    def error(self, msg):
        self.errorShown = True
        echo(msg)

    #Method to reset the GUI
    def reset(self):
        self.setEnabledAll(True)

        self.progressActivityLabel.setVisible(False)
        self.progressActivityLabel.setText('')
        self.progressBar.setVisible(False)
        self.progressBar.reset()
        self.timeLeftLabel.setVisible(False)
        self.timeLeftLabel.setText('')

    #Method to show the queue after comparison
    def showQueue(self):

        #Hide the show duplicates button any time this function is called
        #(as it can also be due to an error and since the queue has then be emptied, this button should not be visible)
        self.queueButton.setVisible(False)

        #When an error causes the comparison to end, don't show the queue
        if self.errorShown:
            self.errorShown = False
            return

        #Retrieve the queue
        queue = self.Comparer.queue

        #Let the user with a pop-up no if there are no results
        if len(queue) == 0:
            echo('No results')

        #If there are, create a dialog window listing all of the duplicates and drop down menu's te select actions
        else:

            #Show the show duplicates button when there are results
            self.queueButton.setVisible(True)

            #Create and execute the new dialog with this dialog as parent
            dialog = QueueDialog.QueueDialog(self.Comparer, self)
            dialog.exec()

    #Method to safely clean up after closing the main dialog and any running threads
    def close(self):
        self.Comparer.stop = True
        del self.Comparer
    

        


