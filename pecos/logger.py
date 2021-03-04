"""
The logger module contains a function to initialize the logger.  Logger
warnings are printed to the monitoring report.
"""
import logging
from os.path import abspath, dirname, join
#logging.getLogger('pecos').addHandler(logging.NullHandler())

def initialize():
    """
    Initialize the pecos logger.  
    Warnings are printed to the monitoring report.
    """
    pecos_logger = logging.getLogger('pecos')
    pecos_logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(join(dirname(abspath(__file__)),'logfile'), mode='w')
    fh.setLevel(logging.WARNING)
    
    # all info is sent to the screen
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter("%(asctime)s : %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    if not len(pecos_logger.handlers):
        pecos_logger.addHandler(fh)
        pecos_logger.addHandler(ch)
