"""
The utils module contains helper functions.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def index_to_datetime(index, unit='s', origin='unix'):
    """
    Convert DataFrame index from int/float to datetime,
    rounds datetime to the nearest millisecond
    
    Parameters
    --------------
    index : pandas Index
        DataFrame index in int or float 
    
    unit : str (optional)
        Units of the original index
    
    origin : str
        Reference date used to define the starting time.
        If origin = 'unix', the start time is '1970-01-01 00:00:00'
        The origin can also be defined using a datetime string in a similar 
        format (i.e. '2019-05-17 16:05:45')
        
    Returns
    ----------
    pandas Index
        DataFrame index in datetime
    """
    
    index2 = pd.to_datetime(index, unit=unit, origin=origin)
    index2 = index2.round('ms') # round to nearest milliseconds
        
    return index2

def datetime_to_elapsedtime(index, origin=0.0):
    """
    Convert DataFrame index from datetime to elapsed time in seconds
    
    Parameters
    --------------
    index : pandas Index
        DataFrame index in datetime
    
    origin : float
        Reference for elapsed time
    
    Returns
    ----------
    pandas Index
        DataFrame index in elapsed seconds
    """

    index2 = index - index[0]
    index2 = index2.total_seconds() + origin
    
    return index2

def datetime_to_clocktime(index):
    """
    Convert DataFrame index from datetime to clocktime (seconds past midnight)
    
    Parameters
    --------------
    index : pandas Index
        DataFrame index in datetime
    
    Returns
    ----------
    pandas Index
        DataFrame index in clocktime
    """
    
    clocktime = index.hour*3600 + index.minute*60 + index.second + index.microsecond/1e6
    
    return clocktime
    
def datetime_to_epochtime(index):
    """
    Convert DataFrame index from datetime to epoch time
    
    Parameters
    --------------
    index : pandas Index
        DataFrame index in datetime
    
    Returns
    ----------
    pandas Index
        DataFrame index in epoch time
    """
    
    index2 = index.astype('int64')/10**9
    
    return index2

def round_index(index, frequency, how='nearest'):
    """
    Round DataFrame index
    
    Parameters
    ----------
    index : pandas Index
        Datetime index
    
    frequency : int
        Expected time series frequency, in seconds
    
    how : string (optional)
        Method for rounding, default = 'nearest'.  Options include:
        
        * nearest = round the index to the nearest frequency
        
        * floor = round the index to the smallest expected frequency
        
        * ceiling = round the index to the largest expected frequency 
        
    Returns
    -------
    pandas Index
        DataFrame index with rounded values
    """

    window_str=str(int(frequency*1e3)) + 'ms' # milliseconds
    
    if how=='nearest':
        rounded_index = index.round(window_str)
    elif how=='floor':
        rounded_index = index.floor(window_str)
    elif how=='ceiling':
        rounded_index = index.ceil(window_str)
    else:
        logger.info("Invalid input, index not rounded")
        rounded_index = index

    return rounded_index
