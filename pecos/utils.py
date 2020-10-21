"""
The utils module contains helper functions.
"""
import numpy as np
import pandas as pd
import re
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
    
    unit : str, optional
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
    
    how : string, optional
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


def evaluate_string(string_to_eval, data=None, trans=None, specs=None, col_name='eval'):
    """
    Returns an evaluated Python string.  WARNING this function calls 'eval'. 
    Strings of Python code should be thoroughly tested by the user.
    
    This function can be useful when defining quality control configuration 
    options in a file, such as:
    
    * Time filters that depend on the data index
    * Quality control bounds that depend on system constants
    * Composite signals that are defined using existing data
    
    For each {keyword} in string_to_eval, {keyword} is expanded in the following order:
    
    * If keyword is ELAPSED_TIME, CLOCK_TIME or EPOCH_TIME then data.index is 
      converted to seconds (elapsed time, clock time, or epoch time) and used 
      in the evaluation (requires data)
    * If keyword is used to select a column (or columns) of data, then 
      data[keyword] is used in the evaluation (requires data) 
    * If a translation dictionary is used to select a column (or columns) of data, then 
      data[trans[keyword]] is used in the evaluation (requires data and trans) 
    * If the keyword is a key in a dictionary of constants, specs, then 
      specs[keyword] is used in the evaluation (requires specs)

    Parameters
    ----------
    string_to_eval : string
        String to evaluate, the string can included multiple keywords and 
        numpy (np.*) and pandas (pd.*) functions
		
    data : pandas DataFrame, optional
        Data, indexed by datetime
		
    trans: dictionary, optional
        Translation dictionary
		
    specs : dictionary, optional
        Keyword:value pairs used to define constants
		
    col_name : string, optional
        Column name used in the returned DataFrame.  If the DataFrame has more 
        than one column, columns are named col_name 0, col_name 1, ...
        
    Returns
    --------
    pandas DataFrame or float
        Evaluated string
    """

    if not isinstance(string_to_eval, str):
        return string_to_eval
    
    match = re.findall(r"\{(.*?)\}", string_to_eval)
    for m in set(match):
        m = m.replace('[','') # check for list

        if m == 'ELAPSED_TIME':
            ELAPSED_TIME = datetime_to_elapsedtime(data.index)
            ELAPSED_TIME = pd.Series(ELAPSED_TIME, index=data.index)
            string_to_eval = string_to_eval.replace("{"+m+"}",m)
        elif m == 'CLOCK_TIME':
            CLOCK_TIME = datetime_to_clocktime(data.index)
            CLOCK_TIME = pd.Series(CLOCK_TIME, index=data.index)
            string_to_eval = string_to_eval.replace("{"+m+"}",m)
        elif m == 'EPOCH_TIME':
            EPOCH_TIME = datetime_to_epochtime(data.index)
            EPOCH_TIME = pd.Series(EPOCH_TIME, index=data.index)
            string_to_eval = string_to_eval.replace("{"+m+"}",m)
        else:
            try:
                data[m]
                datastr = "data[['" + m + "']]" # dataframe
                string_to_eval = string_to_eval.replace("{"+m+"}",datastr)
            except:
                try:
                    data[trans[m]]
                    datastr = "data[trans['" + m + "']]"
                    string_to_eval = string_to_eval.replace("{"+m+"}",datastr)
                except:
                    try:
                        specs[m]
                        datastr = "specs['" + m + "']"
                        string_to_eval = string_to_eval.replace("{"+m+"}",datastr)
                    except:
                        pass

    try:
        signal = eval(string_to_eval)
        
        # Convert Series and tuple of Series to DataFrame
        if isinstance(signal, pd.Series): # Series
            signal = signal.to_frame(0)
        elif isinstance(signal, tuple): # A tuple of series
            signal = pd.DataFrame(signal).T
        
        assert isinstance(signal, (pd.DataFrame, int, float))
        
        # If DataFrame, update column names
        if isinstance(signal, pd.DataFrame): 
            if len(signal.columns) == 1:
                signal.columns = [col_name]
            else:
                signal.columns = [col_name + " " + str(i) for i in range(len(signal.columns))]
        
    except:
        signal = None

    return signal
    