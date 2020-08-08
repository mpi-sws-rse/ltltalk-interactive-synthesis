import pdb

try:
    from utils.SimpleTree import SimpleTree, Formula
    import encodingConstants
except:
    from encoding.utils.SimpleTree import SimpleTree, Formula
    from encoding import encodingConstants

import io
import logging


def lineToTrace(line):
    traceData = line
    traceVector = [[bool(int(varValue)) for varValue in varsInTimestep.split(',')] for varsInTimestep in
                   traceData.split(';')]
    trace = Trace(traceVector)
    return trace


class Trace:
    def __init__(self, traceVector, intendedEvaluation=None, literals=None):

        self.lengthOfTrace = len(traceVector)
        self.intendedEvaluation = intendedEvaluation

        assert self.lengthOfTrace > 0
        self.numVariables = len(traceVector[0])
        self.traceVector = traceVector
        if literals == None:
            # pdb.set_trace()
            self.literals = ["x" + str(i) for i in range(self.numVariables)]
        else:
            self.literals = literals

    def __repr__(self):
        return repr([{self.literals[i]: self.traceVector[t][i] for i in range(len(self.literals))} for t in
                     range(self.lengthOfTrace)])

    def nextPos(self, currentPos):
        if currentPos == self.lengthOfTrace - 1:
            raise ValueError
        else:
            return currentPos + 1

    @classmethod
    def create_trace_from_events_list(cls, events_list, literals_to_consider=None):

        if literals_to_consider is None:
            literals = list(set([it for event in events_list for it in event]))
        else:
            literals = [str(l) for l in literals_to_consider]

        trace_vector = []
        for events in events_list:
            tmstp_events = []
            for lit in literals:
                if lit in events:
                    tmstp_events.append(1)
                else:
                    tmstp_events.append(0)
            trace_vector.append(tmstp_events)
        return cls(trace_vector, literals=literals)

    def futurePos(self, currentPos):
        return list(range(currentPos, self.lengthOfTrace))

    def evaluateFormulaOnTrace(self, formula):

        nodes = list(set(formula.getAllNodes()))
        self.truthAssignmentTable = {node: [None for _ in range(self.lengthOfTrace)] for node in nodes}

        for i in range(self.numVariables):
            literalFormula = Formula(self.literals[i])

            self.truthAssignmentTable[literalFormula] = [bool(measurement[i]) for measurement in self.traceVector]

        return self.truthValue(formula, 0)

    def truthValue(self, formula, timestep):

        futureTracePositions = self.futurePos(timestep)
        tableValue = self.truthAssignmentTable[formula][timestep]

        if tableValue != None:
            return tableValue
        # if the table Value is None, but formula is a prop variable
        elif formula.left is None and formula.right is None:
            return False
        else:
            label = formula.label
            if label == encodingConstants.LAND:
                return self.truthValue(formula.left, timestep) and self.truthValue(formula.right, timestep)
            elif label == encodingConstants.LOR:
                return self.truthValue(formula.left, timestep) or self.truthValue(formula.right, timestep)
            elif label == encodingConstants.LNOT:
                return not self.truthValue(formula.left, timestep)
            elif label == encodingConstants.IMPLIES:
                return not self.truthValue(formula.left, timestep) or self.truthValue(formula.right, timestep)
            elif label == encodingConstants.F:
                return max([self.truthValue(formula.left, futureTimestep) for futureTimestep in futureTracePositions])
                # return self.truthValue(formula.left, timestep) or self.truthValue(formula, self.nextPos(timestep))
            elif label == encodingConstants.G:
                return min([self.truthValue(formula.left, futureTimestep) for futureTimestep in futureTracePositions])
            elif label == encodingConstants.BEFORE:
                return Trace(self.traceVector[timestep:], literals=self.literals).evaluateFormulaOnTrace(
                    Formula([encodingConstants.F,
                             Formula([encodingConstants.LAND,
                                      formula.left,
                                      Formula([encodingConstants.F,
                                               formula.right])
                                      ])
                             ]))
            # strictly before
            elif label == encodingConstants.STRICTLY_BEFORE:
                if timestep == self.lengthOfTrace - 1:
                    return False
                if self.truthValue(formula.left, timestep) is True:
                    return Trace(self.traceVector[self.nextPos(timestep):],
                                 literals=self.literals).evaluateFormulaOnTrace(
                        Formula([encodingConstants.F, formula.right, None]))
                else:
                    return self.truthValue(formula, self.nextPos(timestep))

                # return self.truthValue(formula.left, timestep) and not self.truthValue(formula, self.nextPos(timestep))
            elif label == encodingConstants.UNTIL:
                # logging.debug(timestep, formula)
                qEventuallyTrue = max(
                    [self.truthValue(formula.right, futureTimestep) for futureTimestep in futureTracePositions]) == True
                if qEventuallyTrue == False:
                    return False
                qTrueNow = self.truthValue(formula.right, timestep)
                if qTrueNow:
                    return True
                promiseForTheNextStep = self.truthValue(formula.left, timestep) and self.truthValue(formula,
                                                                                                    self.nextPos(
                                                                                                        timestep))
                return promiseForTheNextStep
            elif label == encodingConstants.ENDS:
                return self.truthValue(formula.left, self.lengthOfTrace - 1)
            elif label == encodingConstants.X:
                if timestep == self.lengthOfTrace - 1:
                    return False
                else:
                    return self.truthValue(formula.left, self.nextPos(timestep))


defaultOperators = [encodingConstants.G, encodingConstants.F, encodingConstants.LNOT, encodingConstants.UNTIL,
                    encodingConstants.LAND, encodingConstants.LOR, encodingConstants.IMPLIES, encodingConstants.X]


class ExperimentTraces:
    def __init__(self, tracesToAccept=None, tracesToReject=None,
                 operators=[encodingConstants.G, encodingConstants.F, encodingConstants.LNOT, encodingConstants.UNTIL,
                            encodingConstants.LAND, encodingConstants.LOR, encodingConstants.IMPLIES,
                            encodingConstants.X, encodingConstants.BEFORE],
                 depth=None, possibleSolution=None, hints=None, literals=None):

        if tracesToAccept != None:
            self.acceptedTraces = tracesToAccept

        else:
            self.acceptedTraces = []

        if tracesToReject != None:
            self.rejectedTraces = tracesToReject
        else:
            self.rejectedTraces = []
        if tracesToAccept != None and tracesToAccept != None:
            self.maxLengthOfTraces = 0
            for trace in self.acceptedTraces + self.rejectedTraces:
                if trace.lengthOfTrace > self.maxLengthOfTraces:
                    self.maxLengthOfTraces = trace.lengthOfTrace

            if literals is None:
                self.literals = self.acceptedTraces[0].literals
            else:
                self.literals = literals

            try:
                self.numVariables = self.acceptedTraces[0].numVariables
            except:
                self.numVariables = self.rejectedTraces[0].numVariables



        self.operators = operators
        self.depthOfSolution = depth
        self.possibleSolution = possibleSolution
        self.hints_with_weights = hints

    def isFormulaConsistent(self, f):

        # not checking consistency in the case that traces are contradictory
        if f == None:
            return True
        for accTrace in self.acceptedTraces:
            if accTrace.evaluateFormulaOnTrace(f) == False:
                return False

        for rejTrace in self.rejectedTraces:
            if rejTrace.evaluateFormulaOnTrace(f) == True:
                return False
        return True

    def __repr__(self):
        returnString = ""
        returnString += "accepted traces:\n"
        for trace in self.acceptedTraces:
            returnString += repr(trace)
        returnString += "\nrejected traces:\n"

        for trace in self.rejectedTraces:
            returnString += repr(trace)
        returnString += "depth of solution: " + repr(self.depthOfSolution) + "\n"
        return returnString

    def writeTracesToFile(self, tracesFileName):
        with open(tracesFileName, "w") as tracesFile:
            for accTrace in self.acceptedTraces:
                line = ';'.join(','.join(str(k) for k in t) for t in accTrace.traceVector) + "\n"
                tracesFile.write(line)
            tracesFile.write("---\n")
            for rejTrace in self.rejectedTraces:
                line = ';'.join(','.join(str(k) for k in t) for t in rejTrace.traceVector) + "\n"
                tracesFile.write(line)
            tracesFile.write("---\n")
            tracesFile.write(','.join(self.operators) + '\n')
            tracesFile.write("---\n")
            tracesFile.write(str(self.depthOfSolution) + '\n')
            tracesFile.write("---\n")
            tracesFile.write(str(self.possibleSolution))

    def _flieLiteralsStringToVector(self, v, literals):
        vec = []
        true_literals = v.split(',')
        for l in literals:
            if l in true_literals:
                vec.append(1)
            else:
                vec.append(0)
        return vec

    def _flieTraceToTrace(self, tracesString):

        finiteTrace = tracesString.split(";")

        traceVector = [self._flieLiteralsStringToVector(v, self.literals) for v in finiteTrace]

        return Trace(traceVector, literals=self.literals)

    def _getLiteralsFromData(self, data):

        for tr in data:

            traceData = tr.split(";")
            for tmstp in traceData:
                lits = tmstp.split(",")
                for lit in lits:
                    lit = lit.strip()
                    if not lit == "null" and not lit in self.literals:
                        self.literals.append(lit)

    def readTracesFromFlieJson(self, data):

        try:
            positive = data["positive"]
        except:
            positive = []

        try:
            negative = data["negative"]
        except:
            negative = []
        self.literals = []
        try:
            self.literals = data["literals"]
        except:
            self._getLiteralsFromData(positive)
            self._getLiteralsFromData(negative)

        self.numVariables = len(self.literals)
        try:
            self.operators = data["operators"]
        except:
            self.operators = defaultOperators

        for tr in positive:
            trace = self._flieTraceToTrace(tr)
            self.acceptedTraces.append(trace)
        for tr in negative:
            trace = self._flieTraceToTrace(tr)
            self.rejectedTraces.append(trace)

        try:
            hints = data["hints"]
        except:
            hints = []
        self.hints_with_weights = {}
        for hint in hints:
            self.hints_with_weights[hint[0]] = hint[1]

    def readTracesFromString(self, s):
        stream = io.StringIO(s)
        self.readTracesFromStream(stream)

    def readTracesFromStream(self, stream):

        readingMode = 0

        operators = None
        for line in stream:

            if '---' in line:
                readingMode += 1
            else:
                if readingMode == 0:

                    trace = lineToTrace(line)
                    trace.intendedEvaluation = True

                    self.acceptedTraces.append(trace)

                elif readingMode == 1:
                    trace = lineToTrace(line)
                    trace.intendedEvaluation = False
                    self.rejectedTraces.append(trace)

                elif readingMode == 2:
                    operators = [s.strip() for s in line.split(',')]

                elif readingMode == 3:
                    self.depthOfSolution = int(line)
                elif readingMode == 4:
                    possibleSolution = line.strip()
                    if possibleSolution.lower() == "none":
                        self.possibleSolution = None
                    else:
                        self.possibleSolution = Formula.convertTextToFormula(possibleSolution)

                else:
                    break
        if operators == None:
            self.operators = defaultOperators
        else:
            self.operators = operators

        self.maxLengthOfTraces = 0
        for trace in self.acceptedTraces + self.rejectedTraces:
            if trace.lengthOfTrace > self.maxLengthOfTraces:
                self.maxLengthOfTraces = trace.lengthOfTrace

        # an assumption that number of variables is the same across all the traces
        try:
            self.numVariables = self.acceptedTraces[0].numVariables
            self.literals = self.acceptedTraces[0].literals
        except:
            self.literals = self.rejectedTraces[0].literals
            self.numVariables = self.rejectedTraces[0].numVariables
        for trace in self.acceptedTraces + self.rejectedTraces:
            if trace.numVariables != self.numVariables:
                raise Exception("wrong number of variables")

    def readTracesFromFile(self, tracesFileName):
        with open(tracesFileName) as tracesFile:
            self.readTracesFromStream(tracesFile)
