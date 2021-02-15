#Import basic modules
import os, time, re

#Import the main window object (mw) from aqt
from aqt import mw

#Import the "show info" tool from utils.py
from aqt.utils import showInfo

#Import all of the Qt GUI library
from aqt.qt import *


#Function to echo any bugs in a show window
def echo(text):
    if isinstance(text, Exception):
        text = '\n'.join(text.args)
    else:
        text = str(text)
    showInfo(text)


#Class to emit progress based on the given times, current items processes and total items
class ProgressTimer(QObject):

    progress = pyqtSignal(int, int, str)

    def __init__(self, totalItems, activity = '', interval = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.restart(totalItems, activity, interval)

    def restart(self, totalItems, activity = '', interval = 1):
        self.totalItems = totalItems
        self.activity = activity
        self.interval = interval

        self.startTime = time.time()
        self.lastTime = self.startTime

    def getProgress(self, currentItems):
        currentTime = time.time()
        passedTime = currentTime - self.startTime
        speed = currentItems / passedTime if passedTime != 0 else 0
        timeLeft = round((self.totalItems - currentItems) / speed) if speed != None else None
        self.lastTime = currentTime
        return round(currentItems / self.totalItems * 100), timeLeft, self.activity

    def getIntervalProgress(self, currentItems):
        currentTime = time.time()
        if currentTime - self.lastTime > self.interval:
            return self.getProgress(currentItems)

    def emitProgress(self, currentItems):
        self.progress.emit(*self.getProgress(currentItems))

    def emitIntervalProgress(self, currentItems):
        currentTime = time.time()
        if currentTime - self.lastTime > self.interval:
            self.emitProgress(currentItems)

#Method to search for a word in a string
def wordIn(word, string):
    # for w in string.split(' '):
    #     if word.lower() == w.lower():
    #         return True
    return re.search(r'\b' + word + r'\b', string, flags = re.IGNORECASE) != None

#Method to remove brackets from a conditional string
def removeBrackets(string):

    #Remove any white space characters from the start and end
    string = string.strip()

    #Check the number of opening and closing brackets and throw an exception
    #when not all brackets have been closed
    openBr = 0
    minOpenBr = -1
    lastMinOpenBr = -1
    lastCh = ''
    start = True
    for i in range(len(string)):
        ch = string[i]

        #When two following characters aren't the same,
        #update whether the start has been passed (defined as after all of the opening brackets at the start)
        diffCh = lastCh != ch and i != len(string) - 1
        if diffCh and start and i > 0:
            start = False

        #Save the minimum number of brackets seen after the start
        if not start and (minOpenBr == -1 or openBr < minOpenBr):
            minOpenBr = openBr

        #When two following characters aren't the same,
        #save the minimum number of opening brackets.
        #At the end this will thus contain the minimum number of not closed brackets seen in the middle of the string.
        if diffCh:
            lastMinOpenBr = minOpenBr

        #Increment the open bracket counter according to the bracket
        if ch == '(':
            openBr += 1
        elif ch == ')':
            if openBr > 0:
                openBr -= 1
            else:
                raise re.error('You have too many closing brackets.')

        #Save the last character
        lastCh = ch

    #When openBr is now not 0, raise an error
    if openBr != 0:
        raise re.error('Not all brackets have been closed.')

    #Remove as many brackets from the start and end
    #as the minimum number of open brackets seen in the middle of the string
    #and return the string
    return string[lastMinOpenBr : len(string) - lastMinOpenBr] if lastMinOpenBr != -1 else string
    


