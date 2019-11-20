"""
The monitoring module contains the PerformanceMonitoring class used to run
quality control tests and store results.  The module also contains individual 
functions that can be used to run quality control tests.
"""
import pandas as pd
import numpy as np
import re
import logging
from pecos.utils import datetime_to_clocktime, datetime_to_elapsedtime

none_list = ['','none','None','NONE', None, [], {}]
NoneType = type(None)

logger = logging.getLogger(__name__)

def _documented_by(original):
    def wrapper(target):
        docstring = original.__doc__
        old = """
        Parameters
        ----------
        """
        new = """
        Parameters
        ----------
        data : pandas DataFrame
            Data used in the quality control test, indexed by datetime
            
        """
        new_docstring = docstring.replace(old, new) + \
        """   
        Returns    
        ----------
        dictionary
            Results include cleaned data, mask, and test results summary
        """

        target.__doc__ = new_docstring
        return target
    return wrapper

### Object-oriented approach
class PerformanceMonitoring(object):

    def __init__(self):
        """
        PerformanceMonitoring class
        """
        self.df = pd.DataFrame()
        self.trans = {}
        self.tfilter = pd.Series()
        self.test_results = pd.DataFrame(columns=['Variable Name',
                                                'Start Time', 'End Time',
                                                'Timesteps', 'Error Flag'])

    @property
    def mask(self):
        """
        Boolean mask indicating data that failed a quality control test

        Returns
        --------
        pandas DataFrame
            Boolean values for each data point,
            True = data point pass all tests,
            False = data point did not pass at least one test (or data is NaN).
        """
        if self.df.empty:
            logger.info("Empty database")
            return

        mask = ~pd.isnull(self.df) # False if NaN
        for i in self.test_results.index:
            variable = self.test_results.loc[i, 'Variable Name']
            start_date = self.test_results.loc[i, 'Start Time']
            end_date = self.test_results.loc[i, 'End Time']
            if variable in mask.columns:
                try:
                    mask.loc[start_date:end_date,variable] = False
                except:
                    pass

        return mask

    @property
    def cleaned_data(self):
        """
        Cleaned data set
        
        Returns
        --------
        pandas DataFrame
            Cleaned data set, data that failed a quality control test are
            replaced by NaN
        """
        return self.df[self.mask]

    def _setup_data(self, key):
        """
        Setup data to use in the quality control test
        """
        if self.df.empty:
            logger.info("Empty database")
            return

        # Isolate subset if key is not None
        if key is not None:
            try:
                df = self.df[self.trans[key]]
            except:
                logger.warning("Undefined key: " + key)
                return
        else:
            df = self.df

        return df

    def _generate_test_results(self, df, bound, min_failures, error_prefix):
        """
        Compare DataFrame to bounds to generate a True/False mask where
        True = passed, False = failed.  Append results to test_results.
        """
        
        # Lower Bound
        if bound[0] not in none_list:
            mask = (df < bound[0])
            error_msg = error_prefix+' < lower bound, '+str(bound[0])
            self._append_test_results(mask, error_msg, min_failures)

        # Upper Bound
        if bound[1] not in none_list:
            mask = (df > bound[1])
            error_msg = error_prefix+' > upper bound, '+str(bound[1])
            self._append_test_results(mask, error_msg, min_failures)

    def _append_test_results(self, mask, error_msg, min_failures=1, use_mask_only=False):
        """
        Append QC results to the PerformanceMonitoring object.

        Parameters
        ----------
        mask : pandas DataFrame
            Result from quality control test, boolean values

        error_msg : string
            Error message to store with the QC results

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1

        use_mask_only : boolean  (optional)
            When True, the mask is used directly to determine test
            results and the variable name is not included in the
            test_results. When False, the mask is used in combination with
            pm.df to extract test results. Default = False
        """
        if not self.tfilter.empty:
            mask[~self.tfilter] = False
        if mask.sum(axis=1).sum(axis=0) == 0:
            return

        if use_mask_only:
            sub_df = mask
        else:
            sub_df = self.df[mask.columns]

        # Find blocks
        order = 'col'
        if order == 'col':
            mask = mask.T

        np_mask = mask.values

        start_nans_mask = np.hstack(
            (np.resize(np_mask[:,0],(mask.shape[0],1)),
             np.logical_and(np.logical_not(np_mask[:,:-1]), np_mask[:,1:])))
        stop_nans_mask = np.hstack(
            (np.logical_and(np_mask[:,:-1], np.logical_not(np_mask[:,1:])),
             np.resize(np_mask[:,-1], (mask.shape[0],1))))

        start_row_idx,start_col_idx = np.where(start_nans_mask)
        stop_row_idx,stop_col_idx = np.where(stop_nans_mask)

        if order == 'col':
            temp = start_row_idx; start_row_idx = start_col_idx; start_col_idx = temp
            temp = stop_row_idx; stop_row_idx = stop_col_idx; stop_col_idx = temp
            #mask = mask.T

        block = {'Start Row': list(start_row_idx),
                 'Start Col': list(start_col_idx),
                 'Stop Row': list(stop_row_idx),
                 'Stop Col': list(stop_col_idx)}

        #if sub_df is None:
        #    sub_df = self.df

        for i in range(len(block['Start Col'])):
            length = block['Stop Row'][i] - block['Start Row'][i] + 1
            if length >= min_failures:
                if use_mask_only:
                    var_name = ''
                else:
                    var_name = sub_df.iloc[:,block['Start Col'][i]].name #sub_df.icol(block['Start Col'][i]).name

                frame = pd.DataFrame([var_name,
                    sub_df.index[block['Start Row'][i]],
                    sub_df.index[block['Stop Row'][i]],
                    length, error_msg],
                    index=['Variable Name', 'Start Time',
                    'End Time', 'Timesteps', 'Error Flag'])
                self.test_results = self.test_results.append(frame.T, ignore_index=True)

    def add_dataframe(self, data):
        """
        Add data to the PerformanceMonitoring object

        Parameters
        -----------
        data : pandas DataFrame
            Data to add to the PerformanceMonitoring object, indexed by datetime
        """
        assert isinstance(data, pd.DataFrame)
        assert isinstance(data.index, pd.core.indexes.datetimes.DatetimeIndex)
        
        temp = data.copy()

        if self.df is not None:
            self.df = temp.combine_first(self.df)
        else:
            self.df = temp

        # Add identity 1:1 translation dictionary
        trans = {}
        for col in temp.columns:
            trans[col] = [col]

        self.add_translation_dictionary(trans)

    def add_translation_dictionary(self, trans):
        """
        Add translation dictionary to the PerformanceMonitoring object

        Parameters
        -----------
        trans : dictionary
            Translation dictionary
        """
        assert isinstance(trans, dict)
        
        for key, values in trans.items():
            self.trans[key] = []
            for value in values:
                self.trans[key].append(value)

    def add_time_filter(self, time_filter):
        """
        Add a time filter to the PerformanceMonitoring object

        Parameters
        ----------
        time_filter : pandas DataFrame with a single column or pandas Series
            Time filter containing boolean values for each time index
        """
        assert isinstance(time_filter, (pd.Series, pd.DataFrame))
        
        if isinstance(time_filter, pd.DataFrame):
            self.tfilter = pd.Series(data = time_filter.values[:,0], index = self.df.index)
        else:
            self.tfilter = time_filter


    def check_timestamp(self, frequency, expected_start_time=None,
                        expected_end_time=None, min_failures=1,
                        exact_times=True):
        """
        Check time series for missing, non-monotonic and duplicate
        timestamps

        Parameters
        ----------
        frequency : int or float
            Expected time series frequency, in seconds

        expected_start_time : Timestamp (optional)
            Expected start time. If not specified, the minimum timestamp
            is used

        expected_end_time : Timestamp (optional)
            Expected end time. If not specified, the maximum timestamp
            is used

        min_failures : int (optional)
            Minimum number of consecutive failures required for
            reporting, default = 1

        exact_times : bool (optional)
            Controls how missing times are checked.
            If True, times are expected to occur at regular intervals
            (specified in frequency) and the DataFrame is reindexed to match
            the expected frequency.
            If False, times only need to occur once or more within each
            interval (specified in frequency) and the DataFrame is not
            reindexed.
        """
        assert isinstance(frequency, (int, float))
        assert isinstance(expected_start_time, (NoneType, pd.Timestamp))
        assert isinstance(expected_end_time, (NoneType, pd.Timestamp))
        assert isinstance(min_failures, int)
        assert isinstance(exact_times, bool)
        
        logger.info("Check timestamp")

        if self.df.empty:
            logger.info("Empty database")
            return
        if expected_start_time is None:
            expected_start_time = min(self.df.index)
        if expected_end_time is None:
            expected_end_time = max(self.df.index)

        rng = pd.date_range(start=expected_start_time, end=expected_end_time,
                            freq=str(int(frequency*1e3)) + 'ms') # milliseconds

        # Check to see if timestamp is monotonic
#        mask = pd.TimeSeries(self.df.index).diff() < 0
        mask = pd.Series(self.df.index).diff() < pd.Timedelta('0 days 00:00:00')
        mask.index = self.df.index
        mask[mask.index[0]] = False
        mask = pd.DataFrame(mask)
        mask.columns = [0]

        self._append_test_results(mask, 'Nonmonotonic timestamp',
                                 use_mask_only=True,
                                 min_failures=min_failures)

        # If not monotonic, sort df by timestamp
        if not self.df.index.is_monotonic:
            self.df = self.df.sort_index()

        # Check for duplicate timestamps
#        mask = pd.TimeSeries(self.df.index).diff() == 0
        mask = pd.Series(self.df.index).diff() == pd.Timedelta('0 days 00:00:00')
        mask.index = self.df.index
        mask[mask.index[0]] = False
        mask = pd.DataFrame(mask)
        mask.columns = [0]
        mask['TEMP'] = mask.index # remove duplicates in the mask
        mask.drop_duplicates(subset='TEMP', keep='last', inplace=True)
        del mask['TEMP']

        # Drop duplicate timestamps (this has to be done before the
        # results are appended)
        self.df['TEMP'] = self.df.index
        #self.df.drop_duplicates(subset='TEMP', take_last=False, inplace=True)
        self.df.drop_duplicates(subset='TEMP', keep='first', inplace=True)

        self._append_test_results(mask, 'Duplicate timestamp',
                                 use_mask_only=True,
                                 min_failures=min_failures)
        del self.df['TEMP']

        if exact_times:
            temp = pd.Index(rng)
            missing = temp.difference(self.df.index).tolist()
            # reindex DataFrame
            self.df = self.df.reindex(index=rng)
            mask = pd.DataFrame(data=self.df.shape[0]*[False],
                                index=self.df.index)
            mask.loc[missing] = True
            self._append_test_results(mask, 'Missing timestamp',
                                 use_mask_only=True,
                                 min_failures=min_failures)
        else:
            # uses pandas >= 0.18 resample syntax
            df_index = pd.DataFrame(index=self.df.index)
            df_index[0]=1 # populate with placeholder values
            mask = df_index.resample(str(int(frequency*1e3))+'ms').count() == 0 # milliseconds
            self._append_test_results(mask, 'Missing timestamp',
                                 use_mask_only=True,
                                 min_failures=min_failures)

    def check_range(self, bound, key=None, min_failures=1):
        """
        Check for data that is outside expected range

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Data column name or translation dictionary key.  If not specified, 
            all columns are used in the test.

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list)
        assert isinstance(key, (NoneType, str))
        assert isinstance(min_failures, int)
        
        logger.info("Check for data outside expected range")

        df = self._setup_data(key)
        if df is None:
            return

        error_prefix = 'Data'

        self._generate_test_results(df, bound, min_failures, error_prefix)

    def check_increment(self, bound, key=None, increment=1, absolute_value=True, 
                        min_failures=1):
        """
        Check data increments using the difference between values

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        increment : int (optional)
            Time step shift used to compute difference, default = 1

        absolute_value : boolean (optional)
            Use the absolute value of the increment data, default = True

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list)
        assert isinstance(key, (NoneType, str))
        assert isinstance(increment, int)
        assert isinstance(absolute_value, bool)
        assert isinstance(min_failures, int)
        
        logger.info("Check for data increment outside expected range")

        df = self._setup_data(key)
        if df is None:
            return

        if df.isnull().all().all():
            logger.warning("Check increment range failed (all data is Null): " + key)
            return

        # Compute interval
        if absolute_value:
            df = np.abs(df.diff(periods=increment))
        else:
            df = df.diff(periods=increment)

        if absolute_value:
            error_prefix = '|Increment|'
        else:
            error_prefix = 'Increment'

        self._generate_test_results(df, bound, min_failures, error_prefix)
    

    def check_delta(self, bound, key=None, window=3600,  direction='both', 
                    min_failures=1):
        """
        Check for stagant data and/or abrupt changes in the data using the 
        difference between max and min values (delta) within a rolling window
        
        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        window : int or float (optional)
            Size of the rolling window (in seconds) used to compute delta,
            default = 3600

        direction : str (optional)
            If direction is 'positive', then only identify data that has a 
            positive slope within the rolling window (the min occurs before the max).  
            If direction is 'negative', then only identify data that has a 
            negative slope within the rolling window (the max occurs before the min).  
            If direction is 'both', then identify both positive and negative 
            slopes within the rolling window.
            
        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list)
        assert isinstance(key, (NoneType, str))
        assert isinstance(window, (int, float))
        assert direction in ['both', 'positive', 'negative']
        assert isinstance(min_failures, int)
        
        logger.info("Check for stagant data and/or abrupt changes using delta (max-min) within a rolling window")
        
        df = self._setup_data(key)
        if df is None:
            return

        window_str = str(int(window*1e3)) + 'ms' # milliseconds

        min_df = df.rolling(window_str, min_periods=2, closed='both').min()
        max_df = df.rolling(window_str, min_periods=2, closed='both').max()

        diff_df = max_df - min_df
        diff_df.loc[diff_df.index[0]:diff_df.index[0]+pd.Timedelta(window_str),:] = None
        
        def update_mask(mask1, df, window_str, bound, direction):
            # While the mask flags data at the time at which the failure occurs, 
            # the actual timespan betwen the min and max should be flagged so that 
            # the final results include actual data points that caused the failure.
            # This function uses numpy arrays to improve performance and returns
            # a mask DataFrame.
            mask2 = np.zeros((len(mask1.index), len(mask1.columns)), dtype=bool)
            index = mask1.index
            # Loop over t, col in mask1 where condition is True
            for t,col in list(mask1[mask1 > 0].stack().index):
                icol = mask1.columns.get_loc(col)
                it = mask1.index.get_loc(t)
                t1 = t-pd.Timedelta(window_str)

                if (bound == 'lower') and (direction == 'both'):
                    # set the entire time interval to True
                    mask2[(index >= t1) & (index <= t),icol] = True
                
                else: 
                    # extract the min and max time
                    min_time = df.loc[t1:t,col].idxmin()
                    max_time = df.loc[t1:t,col].idxmax()
                    
                    if bound == 'lower': # bound = upper, direction = positive or negative
                        # set the entire time interval to True
                        if (direction == 'positive') and (min_time <= max_time):
                            mask2[(index >= t1) & (index <= t),icol] = True
                        elif (direction == 'negative') and (min_time >= max_time):
                            mask2[(index >= t1) & (index <= t),icol] = True
                    
                    elif bound == 'upper': # bound = upper, direction = both, positive or negative
                        # set the initially flaged location to False
                        mask2[it,icol] = False
                        # set the time between max/min or min/max to true
                        if min_time < max_time and (direction == 'both' or direction == 'positive'):
                            mask2[(index >= min_time) & (index <= max_time),icol] = True
                        elif min_time > max_time and (direction == 'both' or direction == 'negative'):
                            mask2[(index >= max_time) & (index <= min_time),icol] = True
                        elif min_time == max_time:
                            mask2[it,icol] = True
                        
            mask2 = pd.DataFrame(mask2, columns=mask1.columns, index=mask1.index)
            #mask2.loc[diff_df.index[0]:diff_df.index[0]+pd.Timedelta(window_str),:] = False
            return mask2
        
        if direction == 'positive':
            error_prefix = 'Delta (+)'
        elif direction == 'negative':
            error_prefix = 'Delta (-)'
        else:
            error_prefix = 'Delta'
        
        #diff_df.to_csv('diff_df.csv')
        
        # Lower Bound
        if bound[0] not in none_list:
            mask = (diff_df < bound[0])
            error_msg = error_prefix+' < lower bound, '+str(bound[0])
            if not self.tfilter.empty:
                mask[~self.tfilter] = False
            #mask.to_csv('lb'+str(bound[0])+'_mask1.csv')
            mask = update_mask(mask, df, window_str, 'lower', direction) 
            #mask.to_csv('lb'+str(bound[0])+'_mask2.csv')
            self._append_test_results(mask, error_msg, min_failures)
        
        # Upper Bound
        if bound[1] not in none_list:
            mask = (diff_df > bound[1])
            error_msg = error_prefix+' > upper bound, '+str(bound[1])
            if not self.tfilter.empty:
                mask[~self.tfilter] = False
            mask = update_mask(mask, df, window_str, 'upper', direction) 
            self._append_test_results(mask, error_msg, min_failures)


    def check_outlier(self, bound, key=None, window=3600, absolute_value=True, 
                      min_failures=1):
        """
        Check for outliers using normalized data within a rolling window
        
        The upper and lower bounds are specified in standard deviations.
        Data normalized using (data-mean)/std.

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        window : int or float (optional)
            Size of the rolling window (in seconds) used to normalize data,
            default = 3600.  If window is set to None, data is normalized using
            the entire data sets mean and standard deviation (column by column).

        absolute_value : boolean (optional)
            Use the absolute value the normalized data, default = True

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list)
        assert isinstance(key, (NoneType, str))
        assert isinstance(window, (NoneType, int, float))
        assert isinstance(absolute_value, bool)
        assert isinstance(min_failures, int)
        
        logger.info("Check for outliers")

        df = self._setup_data(key)
        if df is None:
            return

        # Compute normalized data
        if window is not None:
            window_str = str(int(window*1e3)) + 'ms' # milliseconds
            df_mean = df.rolling(window_str, min_periods=2, closed='both').mean()
            df_std = df.rolling(window_str, min_periods=2, closed='both').std()
            df = (df - df_mean)/df_std
        else:
            df = (df - df.mean())/df.std()
        if absolute_value:
            df = np.abs(df)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

        if absolute_value:
            error_prefix = '|Outlier|'
        else:
            error_prefix = 'Outlier'

        #df[df.index[0]:df.index[0]+datetime.timedelta(seconds=window)] = np.nan

        self._generate_test_results(df, bound, min_failures, error_prefix)

    def check_missing(self, key=None, min_failures=1):
        """
        Check for missing data

        Parameters
        ----------
        key : string (optional)
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(key, (NoneType, str))
        assert isinstance(min_failures, int)
        
        logger.info("Check for missing data")

        df = self._setup_data(key)
        if df is None:
            return

        # Extract missing data
        mask = pd.isnull(df) # checks for np.nan, np.inf

        missing_timestamps = self.test_results[
                self.test_results['Error Flag'] == 'Missing timestamp']
        for index, row in missing_timestamps.iterrows():
            mask.loc[row['Start Time']:row['End Time']] = False

        self._append_test_results(mask, 'Missing data', min_failures=min_failures)

    def check_corrupt(self, corrupt_values, key=None, min_failures=1):
        """
        Check for corrupt data

        Parameters
        ----------
        corrupt_values : list of int or floats
            List of corrupt data values

        key : string (optional)
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(corrupt_values, list)
        assert isinstance(key, (NoneType, str))
        assert isinstance(min_failures, int)
        
        logger.info("Check for corrupt data")

        df = self._setup_data(key)
        if df is None:
            return

        # Extract corrupt data
        mask = pd.DataFrame(data = np.zeros(df.shape), index = df.index, columns = df.columns, dtype = bool) # all False
        for i in corrupt_values:
            mask = mask | (df == i)
        self.df[mask] = np.nan

        self._append_test_results(mask, 'Corrupt data', min_failures=min_failures)


### Functional approach
@_documented_by(PerformanceMonitoring.check_timestamp)
def check_timestamp(data, frequency, expected_start_time=None,
                    expected_end_time=None, min_failures=1, exact_times=True):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_timestamp(frequency, expected_start_time, expected_end_time,
                       min_failures, exact_times)
    mask = pm.mask

    return {'cleaned_data': pm.df, 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_range)
def check_range(data, bound, key=None, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_range(bound, key, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_increment)
def check_increment(data, bound, key=None, increment=1, absolute_value=True,
                    min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_increment(bound, key, increment, absolute_value, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_delta)
def check_delta(data, bound, key=None, window=3600, direction='both', min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_delta(bound, key, window, direction, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_outlier)
def check_outlier(data, bound, key=None, window=3600, absolute_value=True, 
                  min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_outlier(bound, key, window, absolute_value, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_missing)
def check_missing(data, key=None, min_failures=1):
    
    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_missing(key, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_corrupt)
def check_corrupt(data, corrupt_values, key=None, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_corrupt(corrupt_values, key, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}
