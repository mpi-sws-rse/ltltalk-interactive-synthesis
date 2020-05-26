import pdb
import sys, os
import logging
try:
    from encoding.utils.SimpleTree import SimpleTree
except:
    from traces2LTL.utils.SimpleTree import SimpleTree
from encoding import encodingConstants

def test_basic():
    root = SimpleTree(label=encodingConstants.LOR)
    root.addChildren(encodingConstants.LOR, "x2")
    left = root.left
    left.addChildren("x0", "x1")
    
    
    
    logging.info(root)
    logging.info(root.getAllLabels())
    logging.info(root.getAllNodes())

    

if __name__ == "__main__":
    test_basic()