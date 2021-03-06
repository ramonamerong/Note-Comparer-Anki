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
class FieldTable(QTableWidget):

    #Setup signals for when a row is added / removed
    rowAdded = pyqtSignal(int)
    rowRemoved = pyqtSignal(int)

    def __init__(self, group, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Config variables
        self.tableClearable = True
        self.triggers = True

        #Set arguments to local properties
        self.group = group

        #Set the default table
        self.setColumnCount(3)
        self.hideColumn(1)
        self.setHorizontalHeaderLabels(['Fields', 'RegEx', 'Delete'] )
        self.addFieldRow()

        #Resize the columns
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.horizontalHeader().resizeSection(2, 65)

    #Method trigger to update the field in the Comparer object and also adds a new row if the index = row count - 1
    def selectField(self, fieldRow):

        if not self.triggers:
            return

        self.triggers = False

        #Get the row index
        rowIndex = fieldRow.rowIndex

        #Get the selected field index (which is the field index - 1, since the first row is a placeholder)
        selectedIndex = fieldRow.currentIndex() - 1

        #If this is the first placeholder field, remove the field row
        #and return
        if selectedIndex == -1:
            self.remFieldRow(rowIndex)
            self.triggers = True
            return

        #Add or update the field in the Group object
        self.group.addUpdateFieldRow(rowIndex, selectedIndex)

        #Set the tableClearable attribute to true if the number of rows is > 0
        if len(self.group.fields) > 0:
            self.tableClearable = True

        #Check the number of rows, if it's the last one, add a new row to the table
        if rowIndex == self.rowCount() - 1:
            self.addFieldRow(update = True)

        self.triggers = True

    #Method trigger to delete a row when selecting the delete button of a row
    def selectDelete(self, fieldRow):

        #If there is only one row left or it's the last row, don't delete it
        rowCount = self.rowCount()
        if rowCount <= 1 or rowCount - 1 == fieldRow.rowIndex:
            return

        #Delete the row
        self.remFieldRow(fieldRow.rowIndex)

    #Method trigger to save en entered regex
    def enterRegex(self, regexRow):
        if self.triggers == False:
            return
        self.triggers = False

        #Retrieve the added field row
        addedField = self.group.getFieldRow(regexRow.rowIndex)
        
        #Only continue to save it if the text is different
        if addedField != None and regexRow.text() != addedField['regex']:
            addedField['regex'] = regexRow.text()

        self.triggers = True


    #Method to add a new row to the field table
    def addFieldRow(self, update = False):

        #Increase the number of rows in the table by 1
        currentRowCount = self.rowCount() or 0
        self.setRowCount(currentRowCount+1)

        #Emit signal, except if it is the first row
        if currentRowCount > 0:
            self.rowAdded.emit(currentRowCount)

        #Create a combobox to be added to the table, add the row index to it,
        #disable the wheel event and link an lambda function to it
        fieldRow = QComboBox(self)
        fieldRow.rowIndex = currentRowCount
        fieldRow.addItems(['None'])
        fieldRow.wheelEvent = lambda event: None
        fieldRow.currentIndexChanged.connect(lambda: self.selectField(fieldRow))

        #Create a new QTableWidgetItem(), add the combobox to an attribute of it
        #and add it to the field table.
        self.addTableWidget(currentRowCount, 0, fieldRow)

        #Place a regex line edit at the second column
        regexRow = QLineEdit(self)
        regexRow.rowIndex = currentRowCount
        regexRow.textChanged.connect(lambda: self.enterRegex(regexRow))
        self.addTableWidget(currentRowCount, 1, regexRow)

        #Add a delete button to the third column
        delButton = QPushButton('🗑', self)
        delButton.clicked.connect(lambda: self.selectDelete(fieldRow))
        self.addTableWidget(currentRowCount, 2, delButton)

        #Update all the regex line edit and delete button states
        self.updateRowStates()

        #Add the vertical header item
        item = QTableWidgetItem(f'F{currentRowCount+1}')
        self.setVerticalHeaderItem(currentRowCount, item)

        #Update the fields of the row if necessary
        if update:
            self.updateFieldRow(currentRowCount)

        #Return the index of the added row
        return currentRowCount

    #Method to update the fields of the indicated the row based on the selected name and type
    def updateFieldRow(self, rowIndex):
        
        self.triggers = False

        #Retrieve the field names to be set
        fieldNames = [f"{f['name']}\n({f['noteType']['name']})\n" for f in self.group.getPossibleFields()]

        #Update row fields
        self.item(rowIndex, 0).widget.clear()
        self.item(rowIndex, 0).widget.addItems(['None'] + fieldNames)

        self.triggers = True


    #Method to remove the indicated row from the field table
    def remFieldRow(self, rowIndex):

        #Emit signal
        self.rowRemoved.emit(rowIndex)

        #Remove the row
        self.group.removeFieldRow(rowIndex)
        self.removeRow(rowIndex)
        
        #Update all of the indices of the field rows in the table after the indiciated index
        for i in range(rowIndex, self.rowCount()):
            self.item(i, 0).widget.rowIndex -= 1

        #Update the vertical header items following it
        for i in range(rowIndex, self.rowCount()):
            self.verticalHeaderItem(i).setText(f'F{i+1}')

        #Update the RegEx line edits and delete buttons 
        self.updateRowStates()

    #Method to clear all the field rows
    def clearFieldRows(self):
        self.setRowCount(0)
        self.group.clearFieldRows()

    #Method to add an widget to an table cell
    def addTableWidget(self, rowIndex, columnIndex, widget):
        item = QTableWidgetItem()
        item.widget = widget
        self.setItem(rowIndex, columnIndex, item)
        self.setCellWidget(rowIndex, columnIndex, widget)

    #Method to update the RegEx line edit and delete button active states
    def updateRowStates(self):
        rowCount = self.rowCount()

        #When the row count is 1 disable the first line edit and button
        if rowCount == 1:
            self.item(0, 1).widget.setEnabled(False)
            self.item(0, 2).widget.setEnabled(False)
        
        #When the row count is greater than 1, disable the last button
        #and enable all other buttons
        elif rowCount > 1:
            self.item(rowCount-1, 1).widget.setEnabled(False)
            self.item(rowCount-1, 2).widget.setEnabled(False)
            for i in range(rowCount-1):
                self.item(i, 1).widget.setEnabled(True)
                self.item(i, 2).widget.setEnabled(True)

    def setEnabledAll(self, boolean):
        for i in range(self.rowCount()):
            self.item(i, 0).widget.setEnabled(boolean)
            self.item(i, 1).widget.setEnabled(boolean)
            self.item(i, 2).widget.setEnabled(boolean)

        if boolean == True:
            self.updateRowStates()


        
