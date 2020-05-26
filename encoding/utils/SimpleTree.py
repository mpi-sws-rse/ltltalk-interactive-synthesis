import pdb
import re
import logging
try:
    from encoding import encodingConstants
    from ... import constants
except:
    from encoding import encodingConstants
    import constants


from lark import Lark, Transformer
symmetric_operators = [encodingConstants.LAND, encodingConstants.LOR]
binary_operators = [encodingConstants.LAND, encodingConstants.LOR, encodingConstants.UNTIL,encodingConstants.IMPLIES, encodingConstants.BEFORE, encodingConstants.STRICTLY_BEFORE]
unary_operators = ["X", encodingConstants.F, encodingConstants.G, encodingConstants.LNOT, encodingConstants.ENDS]
class SimpleTree:
    def __init__(self, label = "dummy"):
        self.left = None
        self.right = None
        self.label = label
    
    def __hash__(self):
        return hash((self.label, self.left, self.right))
    
    def __eq__(self, other):
        if other == None:
            return False
        else:
            return self.label == other.label and self.left == other.left and self.right == other.right
    
    def __ne__(self, other):
        return not self == other
    
    def _isLeaf(self):
        return self.right == None and self.left == None
    
    def _addLeftChild(self, child):
        if child == None:
            return
        if type(child) is str:
            child = SimpleTree(child)
        self.left = child
        
    def _addRightChild(self, child):
        if type(child) is str:
            child = SimpleTree(child)
        self.right = child
    
    def addChildren(self, leftChild = None, rightChild = None): 
        self._addLeftChild(leftChild)
        self._addRightChild(rightChild)
        
        
    def addChild(self, child):
        self._addLeftChild(child)
        
    def getAllNodes(self):
        leftNodes = []
        rightNodes = []
        
        if self.left != None:
            leftNodes = self.left.getAllNodes()
        if self.right != None:
            rightNodes = self.right.getAllNodes()
        return [self] + leftNodes + rightNodes

    def getAllOperators(self):
        leftOperators = []
        rightOperators = []
        if self.left is None and self.right is None:
            return []
        if not self.left is None:
            leftOperators = self.left.getAllOperators()
        if not self.right is None:
            rightOperators = self.right.getAllOperators()
        return [self.label] + leftOperators + rightOperators


    def getAllLabels(self):
        if self.left != None:
            leftLabels = self.left.getAllLabels()
        else:
            leftLabels = []
            
        if self.right != None:
            rightLabels = self.right.getAllLabels()
        else:
            rightLabels = []
        return [self.label] + leftLabels + rightLabels

    def __repr__(self):
        if self.left == None and self.right == None:
            return self.label
        
        # the (not enforced assumption) is that if a node has only one child, that is the left one
        elif self.left != None and self.right == None:
            return self.label + '(' + self.left.__repr__() + ')'
        
        elif self.left != None and self.right != None:
            return self.label + '(' + self.left.__repr__() + ',' + self.right.__repr__() + ')'


class Formula(SimpleTree):
    
    def __init__(self, formulaArg = "dummyF"):
        
        if not isinstance(formulaArg, str):
            self.label = formulaArg[0]
            self.left = formulaArg[1]
            try:
                self.right = formulaArg[2]
            except:
                self.right = None
        else:
            super().__init__(formulaArg)

    def __lt__(self, other):

        if self.getDepth() < other.getDepth():
            return True
        elif self.getDepth() > other.getDepth():
            return False
        else:
            if self.getNumberOfSubformulas() < other.getNumberOfSubformulas():
                return True
            elif self.getNumberOfSubformulas() > other.getNumberOfSubformulas():
                return False
            if self._isLeaf() and other._isLeaf():
                return self.label < other.label

            if self.right is None:
                if other.right is None:
                    return self.left < other.left
                else:
                    return True

            if not self.right is None:
                if other.right is None:
                    return False

            return self.label < other.label

    """
       normalization is an incomplete method to eliminate equivalent formulas
       """

    @classmethod
    def normalize(cls, f):

        if f is None:
            return None
        if f._isLeaf():
            return Formula([f.label, f.left, f.right])
        fLeft = Formula.normalize(f.left)
        fRight = Formula.normalize(f.right)


        if fLeft.label == "true":
            if f.label in [encodingConstants.LOR, encodingConstants.F, encodingConstants.G, encodingConstants.X]:
                return Formula("true")
            if f.label in [encodingConstants.LAND, encodingConstants.IMPLIES]:
                return Formula.normalize(fRight)
            if f.label == encodingConstants.LNOT:
                return Formula("false")
            if f.label == encodingConstants.UNTIL:
                return Formula.normalize(Formula([encodingConstants.F, fRight, None]))

        if fLeft.label == "false":
            if f.label in [encodingConstants.IMPLIES, encodingConstants.LNOT]:
                return Formula["true"]
            if f.label in [encodingConstants.LAND, encodingConstants.F, encodingConstants.G, encodingConstants.X]:
                return Formula["false"]
            if f.label in [encodingConstants.LOR, encodingConstants.UNTIL]:
                return Formula.normalize(fRight)

        if not fRight is None:
            if fRight.label == "true":
                if f.label in [encodingConstants.LOR, encodingConstants.IMPLIES, encodingConstants.UNTIL]:
                    return Formula("true")
                if f.label in [encodingConstants.LAND]:
                    return Formula.normalize(fLeft)

            if fRight.label == "false":
                if f.label in []:
                    return Formula["true"]
                if f.label in [encodingConstants.LAND, encodingConstants.UNTIL]:
                    return Formula["false"]
                if f.label in [encodingConstants.LOR]:
                    return Formula.normalize(fLeft)
                if f.label in [encodingConstants.IMPLIES]:
                    return Formula.normalize(Formula([encodingConstants.LNOT, fRight, None]))

        # elimiting p&p and similar
        if fLeft == fRight:
            if f.label in [encodingConstants.LAND, encodingConstants.UNTIL, encodingConstants.LOR]:
                return Formula.normalize(fLeft)
            elif f.label in [encodingConstants.BEFORE]:
                return Formula([encodingConstants.BEFORE, fLeft, Formula("true")])
            elif f.label in [encodingConstants.IMPLIES]:
                return Formula("true")

        # eliminating Fp U p and !p U p
        if f.label == encodingConstants.UNTIL:
            if fLeft.label == encodingConstants.F or fLeft.label == encodingConstants.LNOT:
                fLeftLeft = Formula.normalize(fLeft.left)
                if fLeftLeft == fRight:
                    return Formula.normalize(Formula([encodingConstants.F, fLeftLeft]))
            if fRight.label == encodingConstants.F:
                fRightLeft = Formula.normalize(fRight.left)
                if fRightLeft == fLeft:
                    return fRight

        if f.label == encodingConstants.F and fLeft.label == encodingConstants.F:
            return fLeft

        # if there is p | q, don't add q | p
        if f.label in symmetric_operators and not fLeft < fRight:
            return Formula([f.label, fRight, fLeft])

        return Formula([f.label, fLeft, fRight])


    @classmethod
    def convertTextToFormula(cls, formulaText):

        f = Formula()
        try:
            formula_parser = Lark(r"""
                ?formula: _binary_expression
                        |_unary_expression
                        | constant
                        | variable
                !constant: "true"
                        | "false"
                _binary_expression: binary_operator "(" formula "," formula ")"
                _unary_expression: unary_operator "(" formula ")"                
                !variable: NAME
                !binary_operator: "and" | "or" | "->" | "until" | "B" | "before"
                !unary_operator: "eventually" | "G" | "neg" | "X" | "E"                
                %import common.SIGNED_NUMBER
                %import common.WS                
                %import common.ESCAPED_STRING
                %import common.CNAME -> NAME
                %ignore WS 
             """, start = 'formula')
        
            
            tree = formula_parser.parse(formulaText)
            #logging.debug(tree.pretty())
            
        except Exception as e:
            logging.error("can't parse formula %s" %formulaText)
            logging.error("error: %s" %e)
            
        
        f = TreeToFormula().transform(tree)
        return f

    # used for compatibility with DSLTL grammar
    def reFormat(self):
        lb = "{"
        rb = "}"
        if self._isLeaf():
            label_array = self.label.split("_")
            if len(label_array) >= 3 and label_array[-3] == "at":
                # this is because of the weird thing that numbers have to be separated by comma
                formatted_label = " ".join(label_array[:-1])
                formatted_label = formatted_label + ", "+label_array[-1]
                return formatted_label
            if len(label_array) == 2 and label_array[0] == "at":
                formatted_label = " ".join(label_array)
                return formatted_label
            else:
                return self.label
        else:
            if self.label in unary_operators:
                return lb + self.label + " " + self.left.reFormat() + rb

            if self.label in binary_operators:
                return lb + self.left.reFormat() + " " + self.label + " " + self.right.reFormat() + rb


    def prettyPrint(self, top=False):
        if top is True:
            lb = ""
            rb = ""
        else:
            lb = "("
            rb = ")"
        if self._isLeaf():
            return self.label
        if self.label in unary_operators:
            return lb + self.label +" "+ self.left.prettyPrint() + rb

        if self.label in binary_operators:
            return lb + self.left.prettyPrint() +" "+  self.label +" "+ self.right.prettyPrint() + rb

    
    
    def getAllVariables(self):
        allNodes = list(set(self.getAllNodes()))
        return [ node for node in allNodes if node._isLeaf() == True ]
    def getDepth(self):
        if self.left == None and self.right == None:
            return 0
        leftValue = -1
        rightValue = -1
        if self.left != None:
            leftValue = self.left.getDepth()
        if self.right != None:
            rightValue = self.right.getDepth()
        return 1 + max(leftValue, rightValue)
    
    def getNumberOfSubformulas(self):
        return len(self.getSetOfSubformulas())
    
    def getSetOfSubformulas(self):
        if self.left == None and self.right == None:
            return [self]
        leftValue = []
        rightValue = []
        if self.left != None:
            leftValue = self.left.getSetOfSubformulas()
        if self.right != None:
            rightValue = self.right.getSetOfSubformulas()
        return list(set([self] + leftValue + rightValue))

             

class TreeToFormula(Transformer):
        def formula(self, formulaArgs):
            return Formula(formulaArgs)
        def variable(self, varName):



            varStr = str(varName[0])
            varDesc = varStr.split("_")

            # if the variables are not as expected

            if varDesc[0] == constants.PICK and not (varDesc[2] in constants.COLORS and varDesc[3] in constants.SHAPES):
                if varDesc[2] in constants.SHAPES or varDesc[3] in constants.COLORS:
                    swap = varDesc[2]
                    varDesc[2] = varDesc[3]
                    varDesc[3] = swap

                if varDesc[2] in constants.SHAPES and varDesc[3] in constants.SHAPES:
                    varDesc[2] = "x"
                if varDesc[2] in constants.COLORS and varDesc[3] in constants.COLORS:
                    varDesc[3] = "x"
                varStr = "_".join(varDesc)

            return Formula([varStr, None, None])
        def constant(self, arg):
            if str(arg[0]) == "true":
                connector = encodingConstants.LOR
            elif str(arg[0]) == "false":
                connector = encodingConstants.LAND
            return Formula([connector, Formula(["x0", None, None]), Formula([encodingConstants.LNOT, Formula(["x0", None, None] ), None])])
                
        def binary_operator(self, args):
            return str(args[0])
        def unary_operator(self, args):
            return str(args[0])
    
        
        
        