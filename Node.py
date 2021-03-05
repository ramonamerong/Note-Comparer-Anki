
#Import basic modules
import os, re

#Import local .py modules
from . import Utils
echo = Utils.echo

#Class to build a conditional tree to compare notes
class Node:

    def __init__(self, string, depth = 0, removeBrackets = True):
        self.children = []
        if removeBrackets:
            self.setString(string)
        else:
            self.string = string
        self.depth = depth

        self.leftOperand = None
        self.leftValue = None
        self.rightOperand = None
        self.rightValue = None
        self.solveMethod = None
    
    #Function to set a string
    def setString(self, string):
        try:
            self.string = Utils.removeBrackets(string.replace('\n', ' ').replace('\t', ' '))
        except re.error as e:
            raise e

    #Recursive tree method to create children by chopping the condition string set to 'value' into parts
    #to base new children on
    def createChildren(self):
        #echo(self.string + ':' + str(self.depth))

        #Remove any current children
        self.children = []

        #Copy the string value
        string = self.string

        #Remove any '$' signs
        string = string.replace('$', '')

        #Replace all bracket groups with $i
        brackets = []
        i = 0
        newBrackets = re.findall(r'\([^()]*\)', string)
        while len(newBrackets) > 0:
            for br in newBrackets:
                string = string.replace(br, f'${i}')
                i += 1
            brackets.extend(newBrackets)
            newBrackets = re.findall(r'\([^()]*\)', string)

        #Then, split the top level array based on 'and'/'or' operators
        #and clean up any empty values
        #these are the values for the children
        childValues = [cv for cv in re.split(r'( and )|( or )', string) if cv not in [None, '']]

        #If there are child values, rebuild every child value using the saved brackets,
        #create new children and also let them make their own
        if len(childValues) > 1:
            for cv in childValues:

                #Rebuild the child value using the saved brackets
                while '$' in cv:
                    for match in re.finditer(r'\$(\d+)', cv):
                        cv = cv.replace(match.group(0), brackets[int(match.group(1))])

                #Remove any excess brackets from the child value,
                #create a new child, add it and activate it
                child = Node(cv, self.depth + 1)
                self.children.append(child)
                child.createChildren()
        
        #If this is the end child node it is either an operator, 
        #or an elemental condition
        #In the case of the latter, dissect the end value into left and right operands
        #and save the correct solve method
        else:

            #When the end child node is an operator return
            if string in ['and', 'or']:
                return

            #Split the current value into left operand, operator and right operand
            stringSplit = [i for i in re.split(r'(=)|(in)|(>)', string) if i not in [None, '']]

            #When the length isn't 3 raise an error
            if len(stringSplit) != 3:
                raise re.error(f'"{string}" is not a valid condition.')

            #Retrieve the types of the operands
            leftType, self.leftValue = self.__class__.operandType(stringSplit[0])
            rightType, self.rightValue = self.__class__.operandType(stringSplit[2])

            #Depending on the operator different solve methods are saved 
            #while stripping any special characters (' for string values or / for regular expressions)
            if stringSplit[1] == '=':

                #The left operand cannot be an regular expression
                if leftType == 'regex':
                    raise re.error(f"The left part of \"{string}\" cannot be a regular expression.")

                #Depending on if the right operand is a regular expression
                #a different solve method is saved
                if rightType == 'regex':
                    self.solveMethod = self.equalRegexCompare
                else:
                    self.solveMethod = self.equalCompare


            elif stringSplit[1] == 'in':

                #The right operand cannot be an regular expression
                if rightType == 'regex':
                    raise re.error(f"The right part of \"{string}\" cannot be a regular expression.")

                #Depending on if the left operand is a regular expression
                #a different solve method is saved
                if leftType == 'regex':
                    self.solveMethod = self.inRegexCompare
                else:
                    self.solveMethod = self.inCompare

            elif stringSplit[1] == '>':
                
                #The neither operands can be an regular expression
                if leftType == 'regex' or rightType == 'regex':
                    raise re.error(f"The neither the left or right part of \"{string}\" can be a regular expression.")

                #Save the solve method
                self.solveMethod = self.insideCompare

            else:
                raise re.error(f'"{string}" is not a valid condition.')


    #Method to check the end child element's operand and return it
    #If no type can be found, raise an error
    @staticmethod
    def operandType(operand):

        operand = operand.strip()
        fieldMatch = re.fullmatch(r'G(\d+)F(\d+)R?(\d+)?', operand)

        if fieldMatch != None:
            return ('field', fieldMatch.groups())
        elif re.fullmatch(r"^'.*'$", operand) != None:
            return ('string', operand.strip("'"))
        elif re.fullmatch(r"^/.*/$", operand) != None:
            try:
                operand = operand.strip('/')
                re.compile(operand)
                return ('regex', operand)
            except re.error:
                raise re.error(f'"{operand}" is not a valid regular expression.')
        else:
            raise re.error(f'"{operand}" is not a valid value, regular expression or field reference.')


    #Recursive tree method to solve child conditions based on the notes given
    def solve(self, notes):

        #Return the correct value when the node has no children 
        numChildren = len(self.children)
        if numChildren == 0:

            #When the value is an operator, return it
            if self.string in ['and', 'or']:
                return self.string

            #When the value isn't an operator, solve and return the elemental condition
            else:
                return self.solveMethod(notes)

        #When the node has children, solve their values from left to right
        #and return the total result
        else:
            totalCondition = self.children[0].solve(notes)
            currentOperator = ''
            for i in range(1, numChildren):
                newCondition = self.children[i].solve(notes)

                #When a child is an operator save it temporarily
                if newCondition in ['and', 'or']:
                    currentOperator = newCondition
                
                #When it is a condition combine it with the total condition
                #depending on the current operator, and delete the current operator afterwards.
                #if there is no currentOperator, raise an error
                else: 
                    if currentOperator == 'and':
                        totalCondition = totalCondition and newCondition
                    elif currentOperator == 'or':
                        totalCondition = totalCondition or newCondition
                    else:
                        raise re.error('The use of \'and\'/\'or\' operators is incorrect.')
                    currentOperator = ''

            #Return the total condition
            return totalCondition

    #Method to retrieve a field value from a set of notes
    @staticmethod
    def getFieldValue(notes, fieldReference):

        #When the field reference is not a field reference, return it
        if not isinstance(fieldReference, tuple):
            return fieldReference

        #Get the correct field
        try:
            noteIndex = int(fieldReference[0]) - 1
            fieldIndex = int(fieldReference[1]) - 1
            if noteIndex == -1 or fieldIndex == -1:
                raise Exception
            field = notes[noteIndex]['compareFields'][fieldIndex]
        except Exception:
            return False

        #When a regex group index have been given, return that
        #otherwise return the field value
        if fieldReference[2] != None:
            try:
                regexIndex = int(fieldReference[2]) - 1
                if regexIndex == -1:
                    raise Exception
                return field['groups'][regexIndex].strip()
            except Exception:
                return False
        else:
            return field['value']

    #Methods to solve an elemental condition
    def equalCompare(self, notes):
        
        #When either or both of the values are field references, retrieve them from the notes
        left = self.__class__.getFieldValue(notes, self.leftValue)
        right = self.__class__.getFieldValue(notes, self.rightValue)

        #Return the comparison
        if isinstance(left, bool) or isinstance(right, bool):
            return False
        else:
            return left == right

    def inCompare(self, notes):

        #When either or both of the values are field references, retrieve them from the notes
        left = self.__class__.getFieldValue(notes, self.leftValue)
        right = self.__class__.getFieldValue(notes, self.rightValue)

        #Return the comparison
        if isinstance(left, bool) or isinstance(right, bool):
            return False
        else:
            return left in right if ' ' in left else Utils.wordIn(left, right)

    def insideCompare(self, notes):

        #When either or both of the values are field references, retrieve them from the notes
        left = self.__class__.getFieldValue(notes, self.leftValue)
        right = self.__class__.getFieldValue(notes, self.rightValue)

        #Return the comparison
        if isinstance(left, bool) or isinstance(right, bool):
            return False
        else:
            return left in right

    def equalRegexCompare(self, notes):

        #When the left value is a field reference return it from the notes
        left = self.__class__.getFieldValue(notes, self.leftValue)

        #Return the comparison
        if isinstance(left, bool):
            return False
        else:
            return re.fullmatch(self.rightValue, left) != None

    def inRegexCompare(self, notes):

        #When the right value is a field reference return it from the notes
        right = self.__class__.getFieldValue(notes, self.rightValue)

        #Return the comparison
        if isinstance(right, bool):
            return False
        else:
            return re.search(self.leftValue, right) != None
