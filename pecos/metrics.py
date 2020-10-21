"""
The metrics module contains metrics that describe the quality control 
analysis or compute quantities that might be of use in the analysis
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def qci(mask, tfilter=None):
    """
    Compute the quality control index (QCI) for each column, defined as:
    
    :math:`QCI=\dfrac{\sum_{t\in T}X_{dt}}{|T|}`
    
    where 
    :math:`T` is the set of timestamps in the analysis.  
    :math:`X_{dt}` is a data point for column :math:`d` time t` that passed 
    all quality control test.  
    :math:`|T|` is the number of data points in the analysis.
    
    Parameters
    ----------
    mask : pandas DataFrame
        Test results mask, returned from pm.mask
    
    tfilter : pandas Series, optional
        Time filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        Quality control index
    """
    
    if tfilter is not None:
        mask = mask[tfilter]

    qci = mask.sum()/mask.shape[0]
        
    return qci   

def rmse(data1, data2, tfilter=None):
    """
    Compute the root mean squared error (RMSE) for each column, defined as:
    
    :math:`RMSE=\sqrt{\dfrac{\sum{(data_1-data_2)^2}}{n}}`
    
    where
    :math:`data_1` is a time series,
    :math:`data_2` is a time series, and 
    :math:`n` is a number of data points.
    
    Parameters
    -----------
    data1 : pandas DataFrame
        Data
        
    data2 : pandas DataFrame
        Data. Note, the column names in data1 must equal the column names in data2
         
    tfilter : pandas Series, optional
        Time filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        Root mean squared error
    """
    
    if len(set(data1.columns).symmetric_difference(set(data2.columns))) > 0:
        logger.warning("The column names in 'data1' must equal the column names in 'data2'")
        return
    
    if tfilter is not None:
        data1 = data1[tfilter]
        data2 = data2[tfilter]
    
    rmse = {}
    for col in data1.columns:
        rmse[col] = np.sqrt(np.mean(np.power(data1[col] - data2[col],2)))
    
    rmse = pd.Series(rmse)

    return rmse
    
def time_integral(data, tfilter=None):
    """
    Compute the time integral (F) for each column, defined as:
    
    :math:`F=\int{fdt}`
    
    where 
    :math:`f` is a column of data 
    :math:`dt` is the time step between observations.
    The integral is computed using the trapezoidal rule from numpy.trapz.
    Results are given in [original data units]*seconds.
    NaN values are set to 0 for integration.
    
    Parameters
    -----------
    data : pandas DataFrame
        Data
         
    tfilter : pandas Series, optional
        Time filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        Integral
    """
    
    if isinstance(data, pd.Series):
        data = data.to_frame()
        
    if tfilter is not None:
        data = data[tfilter]
    
    data = data.fillna(0) # fill NaN with 0
    
    tdelta = (data.index - data.index[0]).total_seconds() # convert to seconds
    
    F = {}
    for col in data.columns:
        F[col] = float(np.trapz(data.loc[:,col], tdelta))
    
    F = pd.Series(F)
        
    return F

def time_derivative(data, tfilter=None):
    """
    Compute the derivative (f') of each column, defined as:
    
    :math:`f'=\dfrac{df}{dt}`
    
    where 
    :math:`f` is a column of data 
    :math:`dt` is the time step between observations.
    The derivative is computed using central differences from numpy.gradient.
    Results are given in [original data units]/seconds.
    
    Parameters
    -----------
    data : pandas DataFrame
        Data
         
    tfilter : pandas Series, optional
        Filter containing boolean values for each time index
        
    Returns
    -------
    pandas DataFrame
        Derivative of the data
    """
    
    if tfilter is not None:
        data = data[tfilter]
    
    tdelta = (data.index - data.index[0]).total_seconds() # convert to seconds
    
    f = {}
    for col in data.columns:
        f[col] = np.gradient(data.loc[:,col], tdelta)
    
    f = pd.DataFrame(f, index=data.index)
    
    return f

def probability_of_detection(observed, actual, tfilter=None):
    """ 
    Compute probability of detection (PD) for each column, defined as:
        
    :math:`PD=\dfrac{TP}{TP+FN}`
    
    where 
    :math:`TP` is number of true positives and  
    :math:`FN` is the number of false negatives.
    
    Parameters
    ----------
    observed : pandas DataFrame
        Estimated conditions (True = background, False = anomalous), 
        returned from pm.mask
    
    actual : pandas DataFrame
        Actual conditions, (True = background, False = anomalous).
        Note, the column names in observed must equal the column names in actual
    
    tfilter : pandas Series, optional
        Filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        Probability of detection
    """
    
    if len(set(observed.columns).symmetric_difference(set(actual.columns))) > 0:
        logger.warning("The column names in 'observed' must equal the column names in 'actual'")
        return
    
    if tfilter is not None:
        observed = observed[tfilter]
        actual = actual[tfilter]

    PD = {}
    for col in observed.columns:
        obs = observed[col]
        act = actual[col]
        
        # True positive (TP) = anomalous condition where tests fail
        # TP is 1 where the statement is true, Nan where the statement is false
        TP = (obs.where(obs == False)+1) == (act.where(act == False)+1)
        TP_count = TP.sum()
    
        # False negative (FN) = anomalous condition where tests pass
        # FN is 1 where the statement is true, Nan where the statement is false
        FN = (obs.where(obs == True)) == (act.where(act == False)+1)
        FN_count = FN.sum()                            
                              
        PD[col] = TP_count/float(TP_count+FN_count)
    
    PD = pd.Series(PD)
    
    return PD

def false_alarm_rate(observed, actual, tfilter=None):
    """ 
    Compute false alarm rate (FAR) for each column, defined as:
        
    :math:`FAR=\dfrac{TN}{TN+FP}`
    
    where 
    :math:`TN` is number of true negatives and  
    :math:`FP` is the number of false positives.
    
    Parameters
    ----------
    estimated : pandas DataFrame
        Estimated conditions (True = background, False = anomalous), 
        returned from pm.mask
    
    actual : pandas DataFrame
        Actual conditions, (True = background, False = anomalous).
        Note, the column names in observed must equal the column names in actual.
    
    tfilter : pandas Series, optional
        Filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        False alarm rate
    """
    
    if len(set(observed.columns).symmetric_difference(set(actual.columns))) > 0:
        logger.warning("The column names in 'observed' must equal the column names in 'actual'")
        return
    
    # Remove time filter
    if tfilter is not None:
        observed = observed[tfilter]
        actual = actual[tfilter]

    FAR = {}
    for col in observed.columns:
        obs = observed[col]
        act = actual[col]
        
        # True negative (TN) = normal condition where tests pass
        # TN is 1 where the statement is true, Nan where the statement is false
        TN = (obs.where(obs == True)) == (act.where(act == True))
        TN_count = TN.sum()
        
        # False positive (FP) = normal condition where tests fail
        # FP is 1 where the statement is true, Nan where the statement is false
        FP = (obs.where(obs == False)+1) == (act.where(act == True))
        FP_count = FP.sum()                                
                      
        FAR[col] = 1-TN_count/float(TN_count+FP_count)
    
    FAR = pd.Series(FAR)
    
    return FAR