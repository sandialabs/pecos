"""
The utils module contains helper functions.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def convert_index_to_datetime(data, unit='s', origin='unix'):
    """
    Convert DataFrame index from int/float to datetime,
    rounds datetime to the nearest millisecond
    
    Parameters
    --------------
    data : pandas DataFrame
        Data with int/float index
    
    unit : str (optional)
        Units of the original index
    
    origin : str
        Reference date used to define the starting time.
        If origin = 'unix', the start time is '1970-01-01 00:00:00'
        The origin can also be defined using a datetime string in a similar 
        format (i.e. '2019-05-17 16:05:45')
        
    Returns
    ----------
    pandas DataFrame
        Data with DatetimeIndex
    """
    
    df = data.copy()
    
    df.index = pd.to_datetime(df.index, unit=unit, origin=origin)
    df.index = df.index.round('ms') # round to nearest milliseconds
        
    return df

def convert_index_to_elapsed_time(data, origin=0.0):
    """
    Convert DataFrame index from datetime to elapsed time in seconds
    
    Parameters
    --------------
    data : pandas DataFrame
        Data with DatetimeIndex
    
    origin : float
        Reference for elapsed time
    
    Returns
    ----------
    pandas DataFrame
        Data with index in elapsed seconds
    """
    
    df = data.copy()
    
    index = df.index - df.index[0]
    df.index = index.total_seconds() + origin
    
    return df

def convert_index_to_epoch_time(data):
    """
    Convert DataFrame index from datetime to epoch time
    
    Parameters
    --------------
    data : pandas DataFrame
        Data with DatetimeIndex
    
    Returns
    ----------
    pandas DataFrame
        Data with index in epoch time
    """
    
    df = data.copy()
    
    df.index = df.index.astype('int64')/10**9
    
    return df

def round_index(data, frequency, how='nearest'):
    """
    Round DataFrame index
    
    Parameters
    ----------
    data : pandas DataFrame
        Data with DatetimeIndex
    
    frequency : int
        Expected time series frequency, in seconds
    
    how : string (optional)
        Method for rounding, default = 'nearest'.  Options include:
        
        * nearest = round the index to the nearest frequency
        
        * floor = round the index to the smallest expected frequency
        
        * ceiling = round the index to the largest expected frequency 
        
    Returns
    -------
    pandas Datarame
        Data with rounded datetime index
    """
    df = data.copy()

    window_str=str(int(frequency*1e3)) + 'ms' # milliseconds
    
    if how=='nearest':
        rounded_index = df.index.round(window_str)
    elif how=='floor':
        rounded_index = df.index.floor(window_str)
    elif how=='ceiling':
        rounded_index = df.index.ceil(window_str)
    else:
        logger.info("Invalid input, index not rounded")
        rounded_index = df.index
        
    df.index = rounded_index
    
    return df
