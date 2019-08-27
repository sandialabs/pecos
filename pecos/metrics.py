"""
The metrics module contains metrics that describe the quality control 
analysis or compute quantities that might be of use in the analysis
"""
import pandas as pd
import numpy as np
import datetime
import logging

logger = logging.getLogger(__name__)

def qci(mask, tfilter=None, per_day=True):
    """
    Compute the quality control index (QCI), defined as:
    
    :math:`QCI=\dfrac{\sum_{d\in D}\sum_{t\in T}X_{dt}}{|DT|}`
    
    where 
    :math:`D` is the set of data columns and 
    :math:`T` is the set of timestamps in the analysis.  
    :math:`X_{dt}` is a data point for column :math:`d` time t` that passed all quality control test.  
    :math:`|DT|` is the number of data points in the analysis.
    
    Parameters
    ----------
    mask : pandas DataFrame
        Test results mask, returned from pm.mask
    
    tfilter : pandas Series (optional)
        Time filter containing boolean values for each time index
        
    per_day : boolean (optional)
        Flag indicating if the results should be computed per day, default = True
    
    Returns
    -------
    pandas DataFrame with quality control index
    """
    logger.info("Compute QCI")
    
    # Remove time filter
    if tfilter is not None:
        mask = mask[tfilter]
    
    if per_day:     
        dates = [mask.index[0].date() + datetime.timedelta(days=x) for x in range(0, (mask.index[-1].date()-mask.index[0].date()).days+1)]
    
        QCI = pd.DataFrame(index=pd.to_datetime(dates))
    
        for date in dates:
            mask_date = mask.loc[date.strftime('%m/%d/%Y')]
            try:
                QCIndex = mask_date.sum().sum()/float(mask_date.shape[0]*mask_date.shape[1])
                if np.isnan(QCIndex):
                    QCIndex = 0
                QCI.loc[date, 'Quality Control Index'] = QCIndex
            except:
                QCI.loc[date, 'Quality Control Index'] = 0
    else:
        QCI = mask.sum().sum()/float(mask.shape[0]*mask.shape[1])
        
    return QCI   

def rmse(x1, x2, tfilter=None, per_day=True):
    """
    Compute the root mean squared error (RMSE), defined as:
    
    :math:`RMSE=\sqrt{\dfrac{\sum{(x_1-x_2)^2}}{n}}`
    
    where
    :math:`x_1` is a time series,
    :math:`x_2` is a time series, and 
    :math:`n` is a number of data points.
    
    Parameters
    -----------
    x1 : pandas DataFrame with a single column or pandas Series
        Data
        
    x2 : pandas DataFrame with a single column or pandas Series
        Data
         
    tfilter : pandas Series (optional)
        Time filter containing boolean values for each time index
        
    per_day : boolean (optional)
        Flag indicating if the results should be computed per day, default = True
    
    Returns
    -------
    pandas DataFrame with root mean squared error
    """
    logger.info("Compute RMSE")
    
    if type(x1) is pd.core.frame.DataFrame:
        x1 = pd.Series(x1.values[:,0], index=x1.index)
    if type(x2) is pd.core.frame.DataFrame:
        x2 = pd.Series(x2.values[:,0], index=x2.index)
        
    if tfilter is not None:
        x1 = x1[tfilter]
        x2 = x2[tfilter]
        
    def compute_rmse(data1, data2):
        val = np.sqrt(np.mean(np.power(data1 - data2,2)))
        return val
        
    if per_day:
        dates = [x1.index[0].date() + datetime.timedelta(days=x) for x in range(0, (x1.index[-1].date()-x1.index[0].date()).days+1)]
        rmse = pd.DataFrame(index=pd.to_datetime(dates))
        for date in dates:
            x1_date1 = x1.loc[date.strftime('%m/%d/%Y')] 
            x2_date2 = x2.loc[date.strftime('%m/%d/%Y')] 
            val = compute_rmse(x1_date1, x2_date2)
            rmse.loc[date, 'RMSE'] = val
    else:
        val = compute_rmse(x1, x2)
        rmse = pd.DataFrame(val, index=[0], columns=['RMSE'])

    return rmse
    
def time_integral(data, tfilter=None, per_day=True):
    """
    Compute the time integral (F) of each column in the DataFrame, defined as:
    
    :math:`F=\int{fdt}`
    
    where 
    :math:`f` is a column of data 
    :math:`dt` is the time step between observations.
    The time integral is computed using the trapezoidal rule from numpy.trapz.
    Results are given in [original data units]*seconds.
    NaN values are set to 0 for integration.
    
    Parameters
    -----------
    data : pandas DataFrame
        Data
         
    tfilter : pandas Series (optional)
        Time filter containing boolean values for each time index
        
    per_day : boolean (doptional)
        Flag indicating if the results should be computed per day, default = True
    
    Returns
    -------
    pandas DataFrame with time integral of the data, each column is named 
    'Time integral of ' + original column name
    """
    logger.info("Compute time integral")
    
    if tfilter is not None:
        data = data[tfilter]
    
    data = data.fillna(0) # fill NaN with 0
    
    def compute_integral(d):
        val = {}
        tdelta = ((d.index - d.index[0]).values)/1000000000 # convert ns to seconds
        for col in d.columns:
            val['Time integral of ' + col] = float(np.trapz(d.loc[:,col], tdelta))
        return val
        
    if per_day:
        dates = [data.index[0].date() + datetime.timedelta(days=x) for x in range(0, (data.index[-1].date()-data.index[0].date()).days+1)]
        F = pd.DataFrame(index=pd.to_datetime(dates))
        for date in dates:
            df_date = data.loc[date.strftime('%m/%d/%Y')] 
            df_int = compute_integral(df_date)
            for col in df_int:
                F.loc[date, col] = df_int[col]
    else:
        F = compute_integral(data)
        F = pd.DataFrame(F, index=[0])
    
    return F

def probability_of_detection(observed, actual, tfilter=None):
    """ 
    Compute probability of detection (PD), defined as:
        
    :math:`PD=\dfrac{TP}{TP+FN}`
    
    where 
    :math:`TP` is number of true positives and  
    :math:`FN` is the number of false negatives.
    
    Parameters
    ----------
    observed : pandas DataFrame
        Estimated conditions (True = background, False = anomolous), 
        returned from pm.mask
    
    actual : pandas DataFrame
        Actual conditions, (True = background, False = anomolous)
   
    Returns
    -------
    Probability of detection, float
    """
    # Remove time filter
    if tfilter is not None:
        observed = observed[tfilter]
        actual = actual[tfilter]

    # True positive (TP) = anomolous condition where tests fail
    # TP is 1 where the statement is true, Nan where the statement is false
    TP = (observed.where(observed == False)+1) == (actual.where(actual == False)+1)
    TP_count = TP.sum().sum()
    
    # False negative (FN) = anomolous condition where tests pass
    # FN is 1 where the statement is true, Nan where the statement is false
    FN = (observed.where(observed == True)) == (actual.where(actual == False)+1)
    FN_count = FN.sum().sum()
    
    # Probability of detection
    PD = TP_count/float(TP_count+FN_count)
    
    return PD

def false_alarm_rate(observed, actual, tfilter=None):
    """ 
    Compute false alarm rate (FAR), defined as:
        
    :math:`FAR=\dfrac{TN}{TN+FP}`
    
    where 
    :math:`TN` is number of true negatives and  
    :math:`FP` is the number of false positives.
    
    Parameters
    ----------
    estimated : pandas DataFrame
        Estimated conditions (True = background, False = anomolous), 
        returned from pm.mask
    
    actual : pandas DataFrame
        Actual conditions, (True = background, False = anomolous)
    
    Returns
    -------
    False alarm rate, float
    """
    # Remove time filter
    if tfilter is not None:
        observed = observed[tfilter]
        actual = actual[tfilter]

    # True negative (TN) = normal condition where tests pass
    # TN is 1 where the statement is true, Nan where the statement is false
    TN = (observed.where(observed == True)) == (actual.where(actual == True))
    TN_count = TN.sum().sum()
    
    # False positive (FP) = normal condition where tests fail
    # FP is 1 where the statement is true, Nan where the statement is false
    FP = (observed.where(observed == False)+1) == (actual.where(actual == True))
    FP_count = FP.sum().sum()
    
    # False alarm rate
    FAR = 1-TN_count/float(TN_count+FP_count)
    
    return FAR