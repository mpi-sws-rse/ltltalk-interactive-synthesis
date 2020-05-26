import glob
import sys
import pdb
from z3 import *

from encoding.smtEncoding.dagSATEncoding import DagSATEncoding
from encoding.utils.Traces import ExperimentTraces





testTracesFolder ='traces/experiments/'
maxDepth = 5



def test_run():
    run(DagSATEncoding)

def run(encoder):
    allFiles =glob.glob(testTracesFolder+'*') 
    
    for testFileName in allFiles:
        foundSat = False
        logging.debug(testFileName)
        if '~' in testFileName:
            continue
        
        #acceptedTraces, rejectedTraces, availableOperators, expectedResult, depth = readTestTraceFile(testFileName, maxDepth)
        
        traces = ExperimentTraces()
        traces.readTracesFromFile(testFileName)
        logging.debug(traces)
        
        if traces.depthOfSolution == None or traces.depthOfSolution < 0:
            finalDepth = maxDepth
        else:
            finalDepth = traces.depthOfSolution

        with open('log/solver.txt', 'w+') as debugFile:
            for i in range(1,finalDepth+1):
                fg = encoder(i, traces)
                fg.encodeFormula()

                debugFile.write(repr(fg.solver))
            if fg.solver.check() == sat:
                foundSat = True
                logging.debug("depth %d: sat"%i)
                m = fg.solver.model()
                with open('log/model.txt', 'w+') as debugFile:
                    debugFile.write(repr(m))
                
                formula = fg.reconstructWholeFormula(m)
                logging.debug(formula)
                assert(traces.isFormulaConsistent(formula))
                break
            elif fg.solver.check() == unsat:
                logging.debug("depth %d: unsat"% i)
                
                
            else:
                assert(False)
        if foundSat == False:
            logging.debug("unsat even after reaching max depth")
            assert(traces.isFormulaConsistent(None))
                    
if __name__ == "__main__":
    test_run()
    
        
        



