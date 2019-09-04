"""
The monitoring module contains the PerformanceMonitoring class used to run
quality control tests and store results.  The module also contains individual 
functions that can be used to run quality control tests.
"""
import pandas as pd
import numpy as np
import re
import logging

none_list = ['','none','None','NONE', None, [], {}]

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
                Dictionary
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

    def _setup_data(self, key, rolling_mean):
        """
        Setup DataFrame, by (optionally) extracting a column and/or smoothing
        data using rolling window mean.
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

        # Compute moving average
        if rolling_mean > 0:
            rolling_mean_str = str(rolling_mean) + 's'
            df = df.rolling(rolling_mean_str).mean()

        return df

    def _generate_test_results(self, df, bound, specs, min_failures, error_prefix):
        """
        Compare DataFrame to bounds to generate a True/False mask where
        True = passed, False = failed.  Append results to test_results.
        """

        # Evaluate strings in bound values
        for i in range(len(bound)):
            if bound[i] in none_list:
                bound[i] = None
            elif type(bound[i]) is str:
                bound[i] = self.evaluate_string('', bound[i], specs)

        # Lower Bound
        if bound[0] is not None:
            mask = (df < bound[0])
            error_msg = error_prefix+' < lower bound, '+str(bound[0])
            self._append_test_results(mask, error_msg, min_failures)

        # Upper Bound
        if bound[1] is not None:
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
                frame_t = frame.transpose()
                self.test_results = self.test_results.append(frame_t, ignore_index=True)

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
            self.df = temp.copy()

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
        if isinstance(time_filter, pd.DataFrame):
            self.tfilter = pd.Series(data = time_filter.values[:,0], index = self.df.index)
        else:
            self.tfilter = time_filter

#    def add_signal(self, col_name, data):
#        """
#        Add signal to the PerformanceMonitoring DataFrame.
#
#        Parameters
#        -----------
#        col_name : string
#            Column name to add to translation dictionary
#
#        data : pandas DataFrame or pandas Series
#            Data to add to df
#        """
#        if type(data) is pd.core.series.Series:
#            data = data.to_frame(col_name)
#        if type(data) is not pd.core.frame.DataFrame:
#            logger.warning("Add signal failed")
#            return
#
#        if col_name in self.trans.keys():
#            logger.info(col_name + ' already exists in trans')
#            return
#        for col in data.columns.values.tolist():
#            if col in self.df.columns.values.tolist():
#                logger.info(col + ' already exists in df')
#                return
#        try:
#            self.trans[col_name] = data.columns.values.tolist()
#            #self.df[df.columns] = df
#            for col in data.columns:
#                self.df[col] = data[col]
#        except:
#            logger.warning("Add signal failed: " + col_name)
#            return

    def check_timestamp(self, frequency, expected_start_time=None,
                        expected_end_time=None, min_failures=1,
                        exact_times=True):
        """
        Check time series for missing, non-monotonic and duplicate
        timestamps

        Parameters
        ----------
        frequency : int
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
        logger.info("Check timestamp")

        if self.df.empty:
            logger.info("Empty database")
            return
        if expected_start_time is None:
            expected_start_time = min(self.df.index)
        if expected_end_time is None:
            expected_end_time = max(self.df.index)

        rng = pd.date_range(start=expected_start_time, end=expected_end_time,
                            freq=str(int(frequency*1e6)) + 'us') # microseconds

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
            mask = df_index.resample('{}s'.format(frequency)).count() == 0
            self._append_test_results(mask, 'Missing timestamp',
                                 use_mask_only=True,
                                 min_failures=min_failures)

    def check_range(self, bound, key=None, specs={}, rolling_mean=0, min_failures=1):
        """
        Check upper and lower bounds on data

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Translation dictionary key.  If not specified, all columns are
            used in the test.

        specs : dictionary (optional)
            Constants used in bound

        rolling_mean : int (optional)
            Size of the moving window (in seconds) used to smooth data using a
            rolling mean before the test is run, default = 0 (i.e., not used)

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        logger.info("Check data range")

        df = self._setup_data(key, rolling_mean)
        if df is None:
            return

        error_prefix = 'Data'

        self._generate_test_results(df, bound, specs, min_failures, error_prefix)

    def check_increment(self, bound, key=None, specs={}, increment=1,
                        absolute_value=True, rolling_mean=0, min_failures=1):
        """
        Check upper and lower bounds on the difference between data values, 
        separated by a set increment

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Translation dictionary key. If not specified, all columns are
            used in the test.

        specs : dictionary (optional)
            Constants used in bound

        increment : int (optional)
            Time step shift used to compute difference, default = 1

        absolute_value : boolean (optional)
            Take the absolute value of the increment data, default = True

        rolling_mean : int (optional)
            Size of the moving window (in seconds) used to smooth data using a
            rolling mean before the test is run, default = 0 (i.e., not used)

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        logger.info("Check increment range")

        df = self._setup_data(key, rolling_mean)
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

        self._generate_test_results(df, bound, specs, min_failures, error_prefix)

    def check_delta(self, bound, key=None, specs={}, window=3600,
                    absolute_value=True, rolling_mean=0, min_failures=1):
        """
        Check upper and lower bounds on the difference between max and min data 
        values within a rolling window
          
        Note, this method is currently NOT efficient for large
        data sets (> 100000 pts) because it uses df.rolling().apply() to find
        the position of the min and max). This method requires pandas 0.23 or greater.

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Translation dictionary key. If not specified, all columns are used
            in the test.

        specs : dictionary (optional)
            Constants used in bound

        window : int (optional)
            Size of the moving window (in seconds) used to compute delta,
            default = 3600

        absolute_value : boolean (optional)
            Take the absolute value of delta, default = True

        rolling_mean : int (optional)
            Size of the moving window (in seconds) used to smooth data using a
            rolling mean before the test is run, default = 0 (i.e., not used)

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        logger.info("Check delta (max-min) range")
        
        df = self._setup_data(key, rolling_mean)
        if df is None:
            return

        window_str = str(int(window*1e6)) + 'us'

        def f(data=None, method=None):
            if data.notnull().sum() < 2: # there has to be at least two numbers
                return np.nan
            else:
                if method == 'idxmin':
                    # Can't return a timestamp, convert to num, then back to timestamp
                    return data.idxmin().value
                elif method == 'min':
                    return data.min()
                elif method == 'idxmax':
                    return data.idxmax().value
                elif method == 'max':
                    return data.max()
                else:
                    return np.nan

        tmin_df = df.rolling(window_str).apply(lambda x: f(x, 'idxmin'), raw=False) # raw = False passes a Series
        tmin_df = tmin_df.astype('datetime64[ns]')
        # Note, the next line should be replaced with df.rolling(window_str).min(),
        # but the solution is not the same with pandas 0.23
        min_df = df.rolling(window_str).apply(lambda x: f(x, 'min'), raw=False)

        tmax_df = df.rolling(window_str).apply(lambda x: f(x, 'idxmax'), raw=False)
        tmax_df = tmax_df.astype('datetime64[ns]')
        # Same note as above, for max
        max_df = df.rolling(window_str).apply(lambda x: f(x, 'max'), raw=False)

        diff_df = max_df - min_df
        if not absolute_value:
            reverse_order = tmax_df < tmin_df
            diff_df[reverse_order] = -diff_df[reverse_order]

        if absolute_value:
            error_prefix = '|Delta|'
        else:
            error_prefix = 'Delta'

        # Evaluate strings for bound values
        for i in range(len(bound)):
            if bound[i] in none_list:
                bound[i] = None
            elif type(bound[i]) is str:
                bound[i] = self.evaluate_string('', bound[i], specs)

        def extract_exact_position(mask1, tmin_df, tmax_df):
            mask2 = pd.DataFrame(False, columns=mask1.columns, index=mask1.index)
            # Loop over t, col in mask1 where condition is True
            for t,col in list(mask1[mask1 > 0].stack().index):
                # set the initially flaged location to False
                mask2.loc[t,col] = False
                # extract the start and end time
                start_time = tmin_df.loc[t,col]
                end_time = tmax_df.loc[t,col]
                # update mask2
                if start_time < end_time:
                    mask2.loc[start_time:end_time,col] = True # set the time between max and min to true
                else:
                    mask2.loc[end_time:start_time,col] = True # set the time between max and min to true
            return mask2

        # Lower Bound
        if bound[0] is not None:
            mask = (diff_df < bound[0])
            if not self.tfilter.empty:
                mask[~self.tfilter] = False
            if mask.sum(axis=1).sum(axis=0) > 0:
                mask = extract_exact_position(mask, tmin_df, tmax_df)
                self._append_test_results(mask, error_prefix+' < lower bound, '+str(bound[0]),
                                         min_failures=min_failures)

        # Upper Bound
        if bound[1] is not None:
            mask = (diff_df > bound[1])
            if not self.tfilter.empty:
                mask[~self.tfilter] = False
            if mask.sum(axis=1).sum(axis=0) > 0:
                mask = extract_exact_position(mask, tmin_df, tmax_df)
                self._append_test_results(mask, error_prefix+' > upper bound, '+str(bound[1]),
                                         min_failures=min_failures)

    def check_outlier(self, bound, key=None, specs={}, window=3600,
                        absolute_value=True, rolling_mean=0, min_failures=1):
        """
        Check upper and lower bounds on normalized data within a moving window
        to find outliers
        
        The upper and lower bounds are specified in standard deviations.
        Data normalized using (data-mean)/std.

        Parameters
        ----------
        bound : list of floats
            [lower bound, upper bound], None can be used in place of a lower
            or upper bound

        key : string (optional)
            Translation dictionary key. If not specified, all columns are used
            in the test.

        specs : dictionary (optional)
            Constants used in bound

        window : int or None (optional)
            Size of the moving window (in seconds) used to normalize data,
            default = 3600.  If window is set to None, data is normalized using
            the entire data sets mean and standard deviation (column by column).

        absolute_value : boolean (optional)
            Take the absolute value the normalized data, default = True

        rolling_mean : int (optional)
            Size of the moving window (in seconds) used to smooth data using a
            rolling mean before the test is run, default = 0 (i.e., not used)

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        logger.info("Check for outliers")

        df = self._setup_data(key, rolling_mean)
        if df is None:
            return

        # Compute normalized data
        if window is not None:
            window_str = str(int(window*1e6)) + 'us'
            df = (df - df.rolling(window_str).mean())/df.rolling(window_str).std()
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

        self._generate_test_results(df, bound, specs, min_failures, error_prefix)

    def check_missing(self, key=None, min_failures=1):
        """
        Check for missing data

        Parameters
        ----------
        key : string (optional)
            Translation dictionary key. If not specified, all columns are used
            in the test.

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        logger.info("Check for missing data")

        df = self._setup_data(key, 0)
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
        corrupt_values : list of floats
            List of corrupt data values

        key : string (optional)
            Translation dictionary key. If not specified, all columns are used
            in the test.

        min_failures : int (optional)
            Minimum number of consecutive failures required for reporting,
            default = 1
        """
        logger.info("Check for corrupt data")

        df = self._setup_data(key, 0)
        if df is None:
            return

        # Extract corrupt data
        mask = pd.DataFrame(data = np.zeros(df.shape), index = df.index, columns = df.columns, dtype = bool) # all False
        for i in corrupt_values:
            mask = mask | (df == i)
        self.df[mask] = np.nan

        self._append_test_results(mask, 'Corrupt data', min_failures=min_failures)

    def evaluate_string(self, col_name, string_to_eval, specs={}):
        """
        Returns the evaluated Python equation written as a string (BETA)
        
        For each {keyword} in string_to_eval,
        {keyword} is first expanded to self.df[self.trans[keyword]],
        if that fails, then {keyword} is expanded to specs[keyword].

        Parameters
        ----------
        col_name : string
            Column name for the new signal

        string_to_eval : string
            String to evaluate

        specs : dictionary (optional)
            Constants used as keywords

        Returns
        --------
        pandas DataFrame or pandas Series with the evaluated string
        """

        match = re.findall(r"\{(.*?)\}", string_to_eval)
        for m in set(match):
            m = m.replace('[','') # check for list

            if m == 'ELAPSED_TIME':
                ELAPSED_TIME = self.get_elapsed_time()
                string_to_eval = string_to_eval.replace("{"+m+"}",m)
            elif m == 'CLOCK_TIME':
                CLOCK_TIME = self.get_clock_time()
                string_to_eval = string_to_eval.replace("{"+m+"}",m)
            else:
                try:
                    self.df[self.trans[m]]
                    datastr = "self.df[self.trans['" + m + "']]"
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
            if type(signal) is tuple: # A tuple of series
                col_name = [col_name + " " + str(i+1)  for i in range(len(signal))]
                signal = pd.concat(signal, axis=1)
                signal.columns = col_name
                signal.index = self.df.index
            elif type(signal) is float:
                signal = signal
            else:
                signal = pd.DataFrame(signal)
                if len(signal.columns) == 1:
                    signal.columns = [col_name]
                else:
                    signal.columns = [col_name + " " + str(i+1)  for i in range(signal.shape[1])]
                signal.index = self.df.index
        except:
            signal = None
            logger.warning("Insufficient data for Composite Signals: " + col_name + ' -- ' + string_to_eval)

        return signal

    def get_elapsed_time(self):
        """
        Returns the elapsed time in seconds for each Timestamp in the
        DataFrame index.

        Returns
        --------
        pandas DataFrame with elapsed time of the DataFrame index
        """
        elapsed_time = ((self.df.index - self.df.index[0]).values)/1000000000 # convert ns to s
        elapsed_time = pd.DataFrame(data=elapsed_time, index=self.df.index, dtype=int)

        return elapsed_time

    def get_clock_time(self):
        """
        Returns the time of day in seconds past midnight for each Timestamp
        in the DataFrame index.

        Returns
        --------
        pandas DataFrame with clock time of the DataFrame index
        """

        secofday = self.df.index.hour*3600 + \
                   self.df.index.minute*60 + \
                   self.df.index.second + \
                   self.df.index.microsecond/1000000.0
        clock_time = pd.DataFrame(secofday, index=self.df.index)

        return clock_time

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
def check_range(data, bound, key=None, specs={}, rolling_mean=0, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_range(bound, key, specs, rolling_mean, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_increment)
def check_increment(data, bound, key=None, specs={}, increment=1, absolute_value=True,
                    rolling_mean=0, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_increment(bound, key, specs, increment, absolute_value, rolling_mean, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_delta)
def check_delta(data, bound, key=None, specs={}, window=3600, absolute_value=True,
                rolling_mean=0, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_delta(bound, key, specs, window, absolute_value, rolling_mean, min_failures)
    mask = pm.mask

    return {'cleaned_data': data[mask], 'mask': mask, 'test_results': pm.test_results}


@_documented_by(PerformanceMonitoring.check_outlier)
def check_outlier(data, bound, key=None, specs={}, window=3600, absolute_value=True,
                  rolling_mean=0, min_failures=1):

    pm = PerformanceMonitoring()
    pm.add_dataframe(data)
    pm.check_outlier(bound, None, {}, window, absolute_value, rolling_mean, min_failures)
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
