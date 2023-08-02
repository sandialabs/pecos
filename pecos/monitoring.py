"""
The monitoring module contains the PerformanceMonitoring class used to run
quality control tests and store results.  The module also contains individual 
functions that can be used to run quality control tests.
"""
import pandas as pd
import numpy as np
import datetime
import logging

none_list = ['','none','None','NONE', None, [], {}]
NoneType = type(None)

logger = logging.getLogger(__name__)

def _documented_by(original, include_metadata=False):
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
        if include_metadata:
           new_docstring = docstring.replace(old, new) + \
        """   
        Returns    
        ----------
        dictionary
            Results include cleaned data, mask, test results summary, and metadata
        """
        else:
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
        self.tfilter = pd.Series(dtype='float64')
        self.test_results = pd.DataFrame(columns=['Variable Name',
                                                'Start Time', 'End Time',
                                                'Timesteps', 'Error Flag'])
        self.test_results['Start Time'] = self.test_results['Start Time'].astype('datetime64[ns]')
        self.test_results['End Time'] = self.test_results['End Time'].astype('datetime64[ns]')
        self.test_results['Timesteps'] = self.test_results['Timesteps'].astype('int64')
        

    @property
    def data(self):
        """
        Data used in quality control analysis, added to the PerformanceMonitoring
        object using ``add_dataframe``.
        """
        return self.df
    
    @property
    def mask(self):
        """
        Boolean mask indicating if data that failed a quality control test. 
        True = data point pass all tests, False = data point did not pass at least one test.
        """
        if self.df.empty:
            logger.info("Empty database")
            return

        # True = pass, False = fail
        mask = pd.DataFrame(True, index=self.df.index, columns=self.df.columns)

        for i in self.test_results.index:
            variable = self.test_results.loc[i, 'Variable Name']
            start_date = self.test_results.loc[i, 'Start Time']
            end_date = self.test_results.loc[i, 'End Time']
            if variable in mask.columns:
                try:
                    mask.loc[start_date:end_date,variable] = False
                except:
                    pass
            elif self.test_results.loc[i, 'Error Flag'] == 'Missing timestamp':
                mask.loc[start_date:end_date,:] = False
                
        return mask

    @property
    def cleaned_data(self):
        """
        Cleaned data set, data that failed a quality control test are replaced by NaN.
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
                df = self.df[self.trans[key]] #  copy is not needed
            except:
                logger.warning("Undefined key: " + key)
                return
        else:
            df = self.df.copy()

        return df

    def _generate_test_results(self, df, bound, min_failures, error_prefix):
        """
        Compare DataFrame to bounds to generate a True/False mask where
        True = passed, False = failed.  Append results to test_results.
        """
        
        # Lower Bound
        if bound[0] not in none_list:
            mask = ~(df < bound[0]) # True = passed test
            error_msg = error_prefix+' < lower bound, '+str(bound[0])
            self._append_test_results(mask, error_msg, min_failures)

        # Upper Bound
        if bound[1] not in none_list:
            mask = ~(df > bound[1]) # True = passed test
            error_msg = error_prefix+' > upper bound, '+str(bound[1])
            self._append_test_results(mask, error_msg, min_failures)

    def _append_test_results(self, mask, error_msg, min_failures=1, timestamp_test=False):
        """
        Append QC results to the PerformanceMonitoring object.

        Parameters
        ----------
        mask : pandas DataFrame
            Result from quality control test, boolean values

        error_msg : string
            Error message to store with the QC results

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1

        timestamp_test : boolean, optional
            When True, the mask comes from a timestamp test, and the variable 
            name should not be included in the test results
        """

        if not self.tfilter.empty:
            mask[~self.tfilter] = True
            
        if mask.sum(axis=1).sum(axis=0) == mask.shape[0]*mask.shape[1]:
            return
        
        # The mask is translated and then converted to an np array to improve performace.
        # Values are reversed (T/F) to find blocks where quality control tests failed.
        np_mask = ~mask.T.values 

        start_nans_mask = np.hstack(
            (np.resize(np_mask[:,0],(mask.shape[1],1)),
             np.logical_and(np.logical_not(np_mask[:,:-1]), np_mask[:,1:])))
        stop_nans_mask = np.hstack(
            (np.logical_and(np_mask[:,:-1], np.logical_not(np_mask[:,1:])),
             np.resize(np_mask[:,-1], (mask.shape[1],1))))
        
        start_col_idx, start_row_idx = np.where(start_nans_mask)
        stop_col_idx, stop_row_idx = np.where(stop_nans_mask)

        block = {'Start Row': list(start_row_idx),
                  'Start Col': list(start_col_idx),
                  'Stop Row': list(stop_row_idx),
                  'Stop Col': list(stop_col_idx)}

        # Extract test results from each block
        counter=0
        test_results = {}
        for i in range(len(block['Start Col'])):
            
            timesteps = block['Stop Row'][i] - block['Start Row'][i] + 1
            if timesteps >= min_failures:
                if timestamp_test:
                    var_name = ''
                else:
                    var_name = mask.iloc[:,block['Start Col'][i]].name 
                
                start_time = mask.index[block['Start Row'][i]]
                end_time = mask.index[block['Stop Row'][i]]
                    
                test_results[counter] = {'Variable Name': var_name,
                            'Start Time': start_time,
                            'End Time': end_time,
                            'Timesteps': timesteps, 
                            'Error Flag': error_msg}
                counter = counter + 1
    
        test_results = pd.DataFrame(test_results).T
        self.test_results = pd.concat([self.test_results, test_results], ignore_index=True)
        
    def add_dataframe(self, data):
        """
        Add data to the PerformanceMonitoring object

        Parameters
        -----------
        data : pandas DataFrame
            Data to add to the PerformanceMonitoring object, indexed by datetime
        """
        assert isinstance(data, pd.DataFrame), 'data must be of type pd.DataFrame'
        assert isinstance(data.index, pd.core.indexes.datetimes.DatetimeIndex), 'data.index must be a DatetimeIndex'
        
        if self.df is not None:
            self.df = data.combine_first(self.df)
        else:
            self.df = data.copy()

        # Add identity 1:1 translation dictionary
        trans = {}
        for col in data.columns:
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
        assert isinstance(trans, dict), 'trans must be of type dictionary'
        
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
            True = keep time index in the quality control results.
            False = remove time index from the quality control results.
        """
        assert isinstance(time_filter, (pd.Series, pd.DataFrame)), 'time_filter must be of type pd.Series or pd.DataFrame'
        
        if isinstance(time_filter, pd.DataFrame) and (time_filter.shape[1] == 1):
            self.tfilter = time_filter.squeeze()
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

        expected_start_time : Timestamp, optional
            Expected start time. If not specified, the minimum timestamp
            is used

        expected_end_time : Timestamp, optional
            Expected end time. If not specified, the maximum timestamp
            is used

        min_failures : int, optional
            Minimum number of consecutive failures required for
            reporting, default = 1

        exact_times : bool, optional
            Controls how missing times are checked.
            If True, times are expected to occur at regular intervals
            (specified in frequency) and the DataFrame is reindexed to match
            the expected frequency.
            If False, times only need to occur once or more within each
            interval (specified in frequency) and the DataFrame is not
            reindexed.
        """
        assert isinstance(frequency, (int, float)), 'frequency must be of type int or float'
        assert isinstance(expected_start_time, (NoneType, pd.Timestamp)), 'expected_start_time must be None or of type pd.Timestamp'
        assert isinstance(expected_end_time, (NoneType, pd.Timestamp)), 'expected_end_time must be None or of type pd.Timestamp'
        assert isinstance(min_failures, int), 'min_failures must be of type int'
        assert isinstance(exact_times, bool), 'exact_times must be of type bool'
        
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
        mask = ~(pd.Series(self.df.index).diff() < pd.Timedelta('0 days 00:00:00'))
        mask.index = self.df.index
        mask[mask.index[0]] = True
        mask = pd.DataFrame(mask)
        mask.columns = [0]

        self._append_test_results(mask, 'Nonmonotonic timestamp',
                                 timestamp_test=True,
                                 min_failures=min_failures)

        # If not monotonically increasing, sort df by timestamp
        if not self.df.index.is_monotonic_increasing:
            self.df = self.df.sort_index()

        # Check for duplicate timestamps
#        mask = pd.TimeSeries(self.df.index).diff() == 0
        mask = ~(pd.Series(self.df.index).diff() == pd.Timedelta('0 days 00:00:00'))
        mask.index = self.df.index
        mask[mask.index[0]] = True
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
                                 timestamp_test=True,
                                 min_failures=min_failures)
        del self.df['TEMP']

        if exact_times:
            temp = pd.Index(rng)
            missing = temp.difference(self.df.index).tolist()
            # reindex DataFrame
            self.df = self.df.reindex(index=rng)
            mask = pd.DataFrame(data=self.df.shape[0]*[True],
                                index=self.df.index)
            mask.loc[missing] = False
            self._append_test_results(mask, 'Missing timestamp',
                                 timestamp_test=True,
                                 min_failures=min_failures)
        else:
            # uses pandas >= 0.18 resample syntax
            df_index = pd.DataFrame(index=self.df.index)
            df_index[0]=1 # populate with placeholder values
            mask = ~(df_index.resample(str(int(frequency*1e3))+'ms').count() == 0) # milliseconds
            self._append_test_results(mask, 'Missing timestamp',
                                 timestamp_test=True,
                                 min_failures=min_failures)

    def check_range(self, bound, key=None, min_failures=1):
        """
        Check for data that is outside expected range

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string, optional
            Data column name or translation dictionary key.  If not specified, 
            all columns are used in the test.

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list), 'bound must be of type list'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(min_failures, int), 'min_failures must be of type int'
        
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

        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        increment : int, optional
            Time step shift used to compute difference, default = 1

        absolute_value : boolean, optional
            Use the absolute value of the increment data, default = True

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list), 'bound must be of type list'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(increment, int), 'increment must be of type int'
        assert isinstance(absolute_value, bool), 'absolute_value must be of type bool'
        assert isinstance(min_failures, int), 'min_failures must be of type int'
        
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
    

    def check_delta(self, bound, window, key=None, direction=None, 
                    min_failures=1):
        """
        Check for stagnant data and/or abrupt changes in the data using the 
        difference between max and min values (delta) within a rolling window
        
        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        window : int or float
            Size of the rolling window (in seconds) used to compute delta
            
        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        direction : str, optional
            Options = 'positive', 'negative', or None
            
            * If direction is positive, then only identify positive deltas 
              (the min occurs before the max) 
            * If direction is negative, then only identify negative deltas 
              (the max occurs before the min)
            * If direction is None, then identify both positive and negative 
              deltas
            
        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list), 'bound must be of type list'
        assert isinstance(window, (int, float)), 'window must be of type int or float'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert direction in [None, 'positive', 'negative'], "direction must None or the string 'positive' or 'negative'"
        assert isinstance(min_failures, int), 'min_failures must be of type int'
        assert self.df.index.is_monotonic_increasing, 'index must be monotonically increasing'
        
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
            mask2 = np.ones((len(mask1.index), len(mask1.columns)), dtype=bool)
            index = mask1.index
            # Loop over t, col in mask1 where condition is True
            for t,col in list(mask1[mask1 == 0].stack().index):
                icol = mask1.columns.get_loc(col)
                it = mask1.index.get_loc(t)
                t1 = t-pd.Timedelta(window_str)

                if (bound == 'lower') and (direction is None):
                    # set the entire time interval to True
                    mask2[(index >= t1) & (index <= t),icol] = False
                
                else: 
                    # extract the min and max time
                    min_time = df.loc[t1:t,col].idxmin()
                    max_time = df.loc[t1:t,col].idxmax()
                    
                    if bound == 'lower': # bound = upper, direction = positive or negative
                        # set the entire time interval to True
                        if (direction == 'positive') and (min_time <= max_time):
                            mask2[(index >= t1) & (index <= t),icol] = False
                        elif (direction == 'negative') and (min_time >= max_time):
                            mask2[(index >= t1) & (index <= t),icol] = False
                    
                    elif bound == 'upper': # bound = upper, direction = None, positive or negative
                        # set the initially flaged location to False
                        mask2[it,icol] = True
                        # set the time between max/min or min/max to true
                        if min_time < max_time and (direction is None or direction == 'positive'):
                            mask2[(index >= min_time) & (index <= max_time),icol] = False
                        elif min_time > max_time and (direction is None or direction == 'negative'):
                            mask2[(index >= max_time) & (index <= min_time),icol] = False
                        elif min_time == max_time:
                            mask2[it,icol] = False
                        
            mask2 = pd.DataFrame(mask2, columns=mask1.columns, index=mask1.index)
            return mask2
        
        if direction == 'positive':
            error_prefix = 'Delta (+)'
        elif direction == 'negative':
            error_prefix = 'Delta (-)'
        else:
            error_prefix = 'Delta'
        
        # Lower Bound
        if bound[0] not in none_list:
            mask = ~(diff_df < bound[0])
            error_msg = error_prefix+' < lower bound, '+str(bound[0])
            if not self.tfilter.empty:
                mask[~self.tfilter] = True
            mask = update_mask(mask, df, window_str, 'lower', direction) 
            self._append_test_results(mask, error_msg, min_failures)
        
        # Upper Bound
        if bound[1] not in none_list:
            mask = ~(diff_df > bound[1])
            error_msg = error_prefix+' > upper bound, '+str(bound[1])
            if not self.tfilter.empty:
                mask[~self.tfilter] = True
            mask = update_mask(mask, df, window_str, 'upper', direction) 
            self._append_test_results(mask, error_msg, min_failures)


    def check_outlier(self, bound, window=None, key=None, absolute_value=False, streaming=False, 
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

        window : int or float, optional
            Size of the rolling window (in seconds) used to normalize data,
            If window is set to None, data is normalized using
            the entire data sets mean and standard deviation (column by column).
            default = None.
        
        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.
            
        absolute_value : boolean, optional
            Use the absolute value the normalized data, default = True
        
        streaming : boolean, optional
            Indicates if streaming analysis should be used, default = False
            
        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(bound, list), 'bound must be of type list'
        assert isinstance(window, (NoneType, int, float)), 'window must be None or of type int or float'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(absolute_value, bool), 'absolute_value must be of type bool'
        assert isinstance(streaming, bool), 'streaming must be of type bool'
        assert isinstance(min_failures, int), 'min_failures must be type int'
        assert self.df.index.is_monotonic_increasing, 'index must be monotonically increasing'
        
        def outlier(data_pt, history):

            mean = history.mean()
            std = history.std()
            zt = (data_pt - mean)/std
            zt.replace([np.inf, -np.inf], np.nan, inplace=True)
            
            # True = pass, False = fail
            if absolute_value:
                zt = abs(zt)
            
            mask = pd.Series(True, index=zt.index)
            if bound[0] not in none_list:
                mask = mask & (zt >= bound[0])
            if bound[1] not in none_list:   
                mask = mask & (zt <= bound[1])
            
            return mask, zt

        logger.info("Check for outliers")

        df = self._setup_data(key)
        if df is None:
            return
        
        if absolute_value:
            error_prefix = '|Outlier|'
        else:
            error_prefix = 'Outlier'
            
        if streaming:
            metadata = self.check_custom_streaming(outlier, window, rebase=0.5, min_failures=min_failures, error_message=error_prefix)
        else:
            # Compute normalized data
            if window is not None:
                window_str = str(int(window*1e3)) + 'ms' # milliseconds
                df_mean = df.rolling(window_str, min_periods=2, closed='both').mean()
                df_std = df.rolling(window_str, min_periods=2, closed='both').std()
                df = (df - df_mean)/df_std
            else:
                df = (df - df.mean())/df.std()
            
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            
            if absolute_value:
                df = np.abs(df)
    
            #df[df.index[0]:df.index[0]+datetime.timedelta(seconds=window)] = np.nan
    
            self._generate_test_results(df, bound, min_failures, error_prefix)

    def check_missing(self, key=None, min_failures=1):
        """
        Check for missing data

        Parameters
        ----------
        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(min_failures, int), 'min_failures must be type int'
        
        logger.info("Check for missing data")

        df = self._setup_data(key)
        if df is None:
            return

        # Extract missing data
        mask = ~pd.isnull(df) # checks for np.nan, np.inf, True = passed test

        # Check to see if the missing data was already flagged as a missing timestamp
        missing_timestamps = self.test_results[
                self.test_results['Error Flag'] == 'Missing timestamp']
        for index, row in missing_timestamps.iterrows():
            mask.loc[row['Start Time']:row['End Time']] = True

        self._append_test_results(mask, 'Missing data', min_failures=min_failures)

    def check_corrupt(self, corrupt_values, key=None, min_failures=1):
        """
        Check for corrupt data

        Parameters
        ----------
        corrupt_values : list of int or floats
            List of corrupt data values

        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        assert isinstance(corrupt_values, list), 'corrupt_values must be of type list'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(min_failures, int), 'min_failures must be type int'
        
        logger.info("Check for corrupt data")

        df = self._setup_data(key)
        if df is None:
            return

        # Extract corrupt data
        mask = ~df.isin(corrupt_values) # True = passed test

        # Replace corrupt data with NaN
        self.df[~mask] = np.nan

        self._append_test_results(mask, 'Corrupt data', min_failures=min_failures)

    def check_custom_static(self, quality_control_func, key=None, min_failures=1,
                           error_message=None):
        """
        Use custom functions that operate on the entire dataset at once to 
        perform quality control analysis

        Parameters
        ----------
        quality_control_func : function
            Function that operates on self.df and returns a mask and metadata
        
        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
            
        error_message : str, optional
            Error message
        """
        assert callable(quality_control_func), 'quality_control_func must be a callable function'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(min_failures, int), 'min_failures must be type int'
        assert isinstance(error_message, (NoneType, str)), 'error_message must be None or of type string'

        df = self._setup_data(key)
        if df is None:
            return
        
        # Function that operates on the entire dataset and returns a mask and
        # metadata for the entire dataset
        mask, metadata = quality_control_func(df) 
        assert isinstance(mask, pd.DataFrame), 'mask returned by quality_control_func must be of type pd.DataFrame'
        assert isinstance(metadata, pd.DataFrame), 'metadata returned by quality_control_func must be of type pd.DataFrame'
        
        # Function that modifies the mask
        #if post_process_func is not None:
        #    mask = post_process_func(mask)
        
        self._append_test_results(mask, error_message, min_failures)
        
        return metadata
    
    def check_custom_streaming(self, quality_control_func, window, key=None, 
                               rebase=None, min_failures=1, error_message=None):
        """
        Check for anomolous data using a streaming framework which removes 
        anomolous data from the history after each timestamp.  A custom quality 
        control function is supplied by the user to determine if the data is anomolous.

        Parameters
        ----------
        quality_control_func : function
            Function that determines if the last data point is normal or anomalous.
            Returns a mask and metadata for the last data point.
        
        window : int or float
            Size of the rolling window (in seconds) used to define history
            If window is set to None, data is normalized using
            the entire data sets mean and standard deviation (column by column).
        
        key : string, optional
            Data column name or translation dictionary key. If not specified, 
            all columns are used in the test.
        
        rebase : int, float, or None
            Value between 0 and 1 that indicates the fraction of 
            default = None.

        min_failures : int, optional
            Minimum number of consecutive failures required for reporting,
            default = 1
            
        error_message : str, optional
            Error message
        """
        assert callable(quality_control_func), 'quality_control_func must be a callable function'
        assert isinstance(window, (int, float)), 'window must be of type int or float'
        assert isinstance(key, (NoneType, str)), 'key must be None or of type string'
        assert isinstance(rebase, (NoneType, int, float)), 'rebase must be None or type int or float'
        assert isinstance(min_failures, int), 'min_failures must be type int'
        assert isinstance(error_message, (NoneType, str)), 'error_message must be None or of type string'

        df = self._setup_data(key)
        if df is None:
            return
        
        metadata = {} 
        rebase_count = 0
        history_window = datetime.timedelta(seconds=window)
        
        # The mask must be the same size as data
        # The streaming framework uses numpy arrays to improve performance but
        # still expects pandas DataFrames and Series in the user defined quality 
        # control function to keep data types consitent on the user side.
        np_mask = pd.DataFrame(True, index=df.index, columns=df.columns).values
        np_data = df.values.astype('float64')
    
        ti = df.index.get_loc(df.index[0]+history_window)
        
        for i, t in enumerate(np.arange(ti,np_data.shape[0],1)):

            #t_start = df.index.get_loc(df.index[t]-history_window, method='nearest')
            t_start = df.index.get_indexer([df.index[t]-history_window], method='nearest')[0]
            t_timestamp = df.index[t]
            
            data_pt = pd.Series(np_data[t], index=df.columns)
            history = pd.DataFrame(np_data[t_start:t], index=range(t-t_start), columns=df.columns)

            mask_t, metadata[t_timestamp] = quality_control_func(data_pt, history)
            if i == 0:
                assert isinstance(mask_t, pd.Series), 'mask returned by quality_control_func must be of type pd.Series'
                assert isinstance(metadata[t_timestamp], pd.Series), 'metadata returned by quality_control_func must be of type pd.Series'

            np_mask[t] = mask_t.values
            np_data[~np_mask] = np.NAN
       
            # rebase
            if rebase is not None:
                data_history = np_data[t_start:t+1] # +1 so it includes history and current data point
                check_rebase = np.isnan(data_history).sum(axis=0)/data_history.shape[0] > rebase
                if sum(check_rebase) > 0:
                    np_data[t][check_rebase] = df.iloc[t][check_rebase]
                    rebase_count = rebase_count + sum(check_rebase)
        
        mask = pd.DataFrame(np_mask, index=df.index, columns=df.columns)
        self._append_test_results(mask, error_message, min_failures)
        
        # Convert metadata to a dataframe
        metadata = pd.DataFrame(metadata).T
        
        return metadata

        
### Functional approach
@_documented_by(PerformanceMonitoring.check_timestamp)
def check_timestamp(data, frequency, expected_start_time=None,
                    expected_end_time=None, min_failures=1, exact_times=True):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_timestamp(frequency, expected_start_time, expected_end_time,
                       min_failures, exact_times)
    mask = pm.mask

    return {'cleaned_data': pm.data, 'mask': mask, 'test_results': pm.test_results}


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
def check_delta(data, bound, window, key=None, direction=None, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_delta(bound, window, key, direction, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_outlier)
def check_outlier(data, bound, window=None, key=None, absolute_value=False, 
                  streaming=False, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_outlier(bound, window, key, absolute_value, streaming, min_failures)
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

@_documented_by(PerformanceMonitoring.check_custom_static, include_metadata=True)
def check_custom_static(data, quality_control_func, key=None, min_failures=1,
                           error_message=None):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    metadata = pm.check_custom_static(quality_control_func, key, min_failures, error_message)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results,
            'metadata': metadata}

@_documented_by(PerformanceMonitoring.check_custom_streaming, include_metadata=True)
def check_custom_streaming(data, quality_control_func, window, key=None, rebase=None,
                         min_failures=1, error_message=None):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    metadata = pm.check_custom_streaming(quality_control_func, window, key, rebase, min_failures, error_message)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results,
            'metadata': metadata}