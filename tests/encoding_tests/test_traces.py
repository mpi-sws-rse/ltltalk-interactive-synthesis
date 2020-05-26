from encoding.utils.Traces import Trace, ExperimentTraces
import glob
import logging


testTracesFolder ='traces/experiments/'



def test_next_and_future():
    allFiles =glob.glob(testTracesFolder+'*') 
    for testFileName in allFiles:
        
        if 'And' not in testFileName or '~' in testFileName:
            continue
        
        #acceptedTraces, rejectedTraces, availableOperators, expectedResult, depth = readTestTraceFile(testFileName, maxDepth)
        traces = ExperimentTraces()
        traces.readTracesFromFile(testFileName)
        
        
        for trace in traces.acceptedTraces + traces.rejectedTraces:
        
            for currentPos in range(trace.lengthOfTrace):
                
                logging.info("current position %d"%currentPos)
                logging.info("next: "+str(trace.nextPos(currentPos)))
                logging.info("future: %s\n"%str(trace.futurePos(currentPos)))
            logging.info("=========\n\n")
        
if __name__ == "__main__":
    test_next_and_future()