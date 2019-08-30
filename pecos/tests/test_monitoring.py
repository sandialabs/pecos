import unittest
from nose.tools import *
from os.path import abspath, dirname, join
import pecos
import pandas as pd
from pandas import Timestamp, RangeIndex
from pandas.util.testing import assert_frame_equal
import numpy as np
from numpy import array

#pd.set_option('expand_frame_repr', False)

testdir = dirname(abspath(__file__))
datadir = join(testdir,'data')
simpleexampledir = join(testdir,'..', '..', 'examples','simple')

def simple_example_run_analysis(df):
    # Input
    system_name = 'Simple'
    translation_dictionary = {'Wave': ['C','D']}
    expected_frequency = 900 # s
    corrupt_values = [-999]
    range_bounds = {
        'B': [0, 1],
        'Wave': [-1, 1],
        'Wave Error': [None, 0.25]}
    increment_bounds = {
        'A': [0.0001, None],
        'B': [0.0001, None],
        'Wave': [0.0001, 0.6]}

    # Create an PerformanceMonitoring instance
    pm = pecos.monitoring.PerformanceMonitoring()

    # Populate the PerformanceMonitoring instance
    pm.add_dataframe(df)
    pm.add_translation_dictionary(translation_dictionary)

    # Check timestamp
    pm.check_timestamp(expected_frequency)

    # Generate time filter
    clock_time = pm.get_clock_time()
    time_filter = (clock_time > 3*3600) & (clock_time < 21*3600)
    pm.add_time_filter(time_filter)

    # Check missing
    pm.check_missing()

    # Check corrupt
    pm.check_corrupt(corrupt_values)

    # Add composite signals
    elapsed_time= pm.get_elapsed_time()
    wave_model = np.sin(10*(elapsed_time/86400))
    wave_model_abs_error = np.abs(np.subtract(pm.df[pm.trans['Wave']], wave_model))
    wave_model_abs_error.columns=['Wave Error C', 'Wave Error D']
    pm.add_dataframe(wave_model_abs_error)
    pm.add_translation_dictionary({'Wave Error': ['Wave Error C', 'Wave Error D']})

    # Check range
    for key,value in range_bounds.items():
        pm.check_range(value, key)

    # Check increment
    for key,value in increment_bounds.items():
        pm.check_increment(value, key)

    # Compute metrics
    QCI = pecos.metrics.qci(pm.mask, pm.tfilter)

    # Write metrics, test results, and report files
    pecos.io.write_metrics(QCI)
    pecos.io.write_test_results(pm.test_results)

    return QCI

class Test_simple_example(unittest.TestCase):

    @classmethod
    def setUp(self):
        trans = {
            'Linear': ['A'],
            'Random': ['B'],
            'Wave': ['C','D']}

        file_name = join(simpleexampledir,'simple.xlsx')

        self.raw_data = pd.read_excel(file_name, index_col=0)
        self.pm = pecos.monitoring.PerformanceMonitoring()
        self.pm.add_dataframe(self.raw_data)
        self.pm.add_translation_dictionary(trans)
        self.pm.check_timestamp(900)
        clock_time = self.pm.get_clock_time()
        self.time_filter = (clock_time > 3*3600) & (clock_time < 21*3600)
        self.pm.add_time_filter(self.time_filter)
        
    @classmethod
    def tearDown(self):
        pass
    
    def test_evaluate_string(self):
        time_filter_string = "({CLOCK_TIME} > 3*3600) & ({CLOCK_TIME} < 21*3600)"
        time_filter = self.pm.evaluate_string('Time Filter', time_filter_string)
        
        expected = pd.DataFrame(index=self.pm.df.index, columns=['Time Filter'])
        expected['Time Filter'] = False
        expected[(self.pm.df.index > pd.Timestamp('2015-01-01 03:00:00')) & 
                 (self.pm.df.index < pd.Timestamp('2015-01-01 21:00:00'))] = True
                
        assert_frame_equal(time_filter, expected, check_dtype=False)
        
    def test_check_timestamp(self):
        #Missing timestamp at 5:00
        #Duplicate timestamp 17:00
        #Non-monotonic timestamp 19:30
        expected = pd.DataFrame(
            [('', pd.Timestamp('2015-01-01 19:30:00'), pd.Timestamp('2015-01-01 19:30:00'), 1.0, 'Nonmonotonic timestamp'),
             ('', pd.Timestamp('2015-01-01 17:00:00'), pd.Timestamp('2015-01-01 17:00:00'), 1.0, 'Duplicate timestamp'),
             ('', pd.Timestamp('2015-01-01 05:00:00'), pd.Timestamp('2015-01-01 05:00:00'), 1.0, 'Missing timestamp')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])
        
        # Object-oriented test
        test_results = self.pm.test_results
        assert_frame_equal(test_results, expected, check_dtype=False)
        
        # Functional test
        results = pecos.monitoring.check_timestamp(self.raw_data, 900)
        test_results = results['test_results']
        assert_frame_equal(test_results, expected, check_dtype=False)

    def test_check_missing(self):
        #Column D is missing data from 17:45 until 18:15
        expected = pd.DataFrame(
            [('D', pd.Timestamp('2015-01-01 17:45:00'), pd.Timestamp('2015-01-01 18:15:00'), 3.0, 'Missing data')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])
        
        # Object-oriented test
        self.pm.check_missing()
        test_results = self.pm.test_results[self.pm.test_results['Error Flag'] == 'Missing data']
        assert_frame_equal(test_results.reset_index(drop=True), expected, check_dtype=False)
        
        # Functional test
        results = pecos.monitoring.check_missing(self.raw_data)
        test_results = results['test_results']
        assert_frame_equal(test_results, expected, check_dtype=False)
        
    def test_check_corrupt(self):
        #Column C has corrupt data (-999) between 7:30 and 9:30
        expected = pd.DataFrame(
            [('C', pd.Timestamp('2015-01-01 07:30:00'), pd.Timestamp('2015-01-01 09:30:00'), 9.0, 'Corrupt data')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])
        
        # Object-oriented test
        self.pm.check_corrupt([-999])
        test_results = self.pm.test_results[self.pm.test_results['Error Flag'] == 'Corrupt data']
        assert_frame_equal(test_results.reset_index(drop=True), expected, check_dtype=False)
        
        # Functional test
        results = pecos.monitoring.check_corrupt(self.raw_data, [-999])
        test_results = results['test_results']
        assert_frame_equal(test_results, expected, check_dtype=False)

    def test_check_range(self):
        #Column B is below the expected lower bound of 0 at 6:30 and above the expected upper bound of 1 at 15:30
        #Column D is occasionally below the expected lower bound of -1 around midday (2 time steps) and above the expected upper bound of 1 in the early morning and late evening (10 time steps).
        expected = pd.DataFrame(
            [('B', pd.Timestamp('2015-01-01 06:30:00'), pd.Timestamp('2015-01-01 06:30:00'), 1.0, 'Data < lower bound, 0'),
             ('B', pd.Timestamp('2015-01-01 15:30:00'), pd.Timestamp('2015-01-01 15:30:00'), 1.0, 'Data > upper bound, 1'),
             ('D', pd.Timestamp('2015-01-01 11:15:00'), pd.Timestamp('2015-01-01 11:15:00'), 1.0, 'Data < lower bound, -1'),
             ('D', pd.Timestamp('2015-01-01 12:45:00'), pd.Timestamp('2015-01-01 12:45:00'), 1.0, 'Data < lower bound, -1'),
             ('D', pd.Timestamp('2015-01-01 03:15:00'), pd.Timestamp('2015-01-01 03:30:00'), 2.0, 'Data > upper bound, 1'),
             ('D', pd.Timestamp('2015-01-01 04:00:00'), pd.Timestamp('2015-01-01 04:00:00'), 1.0, 'Data > upper bound, 1'),
             ('D', pd.Timestamp('2015-01-01 04:30:00'), pd.Timestamp('2015-01-01 04:45:00'), 2.0, 'Data > upper bound, 1'),
             ('D', pd.Timestamp('2015-01-01 18:30:00'), pd.Timestamp('2015-01-01 18:45:00'), 2.0, 'Data > upper bound, 1'),
             ('D', pd.Timestamp('2015-01-01 19:15:00'), pd.Timestamp('2015-01-01 19:45:00'), 3.0, 'Data > upper bound, 1')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])

        # Object-oriented test
        self.pm.check_corrupt([-999])
        self.pm.check_range([0, 1], 'Random')
        self.pm.check_range([-1, 1], 'Wave')
        test_results = self.pm.test_results[['Data' in ef for ef in self.pm.test_results['Error Flag']]]
        assert_frame_equal(test_results.reset_index(drop=True), expected, check_dtype=False)
        
        # Functional tests
        results = pecos.monitoring.check_timestamp(self.raw_data, 900)
        results = pecos.monitoring.check_corrupt(results['cleaned_data'], [-999])
        raw_data = results['cleaned_data'].loc[self.time_filter[0],:]
        
        results = pecos.monitoring.check_range(raw_data[['B']],[0, 1])
        test_results = results['test_results']
        assert_frame_equal(test_results,
                           expected.loc[expected['Variable Name'] == 'B',:].reset_index(drop=True), 
                           check_dtype=False)
        
        results = pecos.monitoring.check_range(raw_data[['C','D']],[-1, 1])
        test_results = results['test_results']
        assert_frame_equal(test_results,
                           expected.loc[expected['Variable Name'] == 'D',:].reset_index(drop=True), 
                           check_dtype=False)
        
    def test_check_increment(self):
        #Column A has the same value (0.5) from 12:00 until 14:30
        #Column C does not follow the expected sine function from 13:00 until 16:15. The change is abrupt and gradually corrected.
        expected = pd.DataFrame(
            [('A', pd.Timestamp('2015-01-01 12:15:00'), pd.Timestamp('2015-01-01 14:30:00'), 10.0, '|Increment| < lower bound, 0.0001'),
             ('C', pd.Timestamp('2015-01-01 13:00:00'), pd.Timestamp('2015-01-01 13:00:00'), 1.0, '|Increment| > upper bound, 0.6')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])
        
        # Object-oriented test
        self.pm.check_corrupt([-999])
        self.pm.check_increment([0.0001, None], 'Linear')
        self.pm.check_increment([0.0001, None], 'Random')
        self.pm.check_increment([0.0001, 0.6], 'Wave')
        test_results = self.pm.test_results[['Increment' in ef for ef in self.pm.test_results['Error Flag']]]
        assert_frame_equal(test_results.reset_index(drop=True), expected, check_dtype=False)
        
        # Functional tests
        results = pecos.monitoring.check_timestamp(self.raw_data, 900)
        results = pecos.monitoring.check_corrupt(results['cleaned_data'], [-999])
        raw_data = results['cleaned_data'].loc[self.time_filter[0],:]
        
        results = pecos.monitoring.check_increment(raw_data[['A']],[0.0001, None])
        test_results = results['test_results']
        assert_frame_equal(test_results,
                           expected.loc[expected['Variable Name'] == 'A',:].reset_index(drop=True), 
                           check_dtype=False)
    
    def test_check_delta(self):
        #Column A has the same value (0.5) from 12:00 until 14:30
        #Column C does not follow the expected sine function from 13:00 until 16:15. 
        #The change is abrupt and gradually corrected.
        expected = pd.DataFrame(
            [('A', pd.Timestamp('2015-01-01 12:15:00'), pd.Timestamp('2015-01-01 14:15:00'), 9.0, '|Delta| < lower bound, 0.0001'),
             ('C', pd.Timestamp('2015-01-01 12:45:00'), pd.Timestamp('2015-01-01 13:00:00'), 2.0, '|Delta| > upper bound, 0.6')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])
        
        # Object-oriented test
        self.pm.check_corrupt([-999])
        self.pm.check_delta([0.0001, None], window=2*3600)
        self.pm.check_delta([None, 0.6], 'Wave', window=1800)
        test_results = self.pm.test_results[['Delta' in ef for ef in self.pm.test_results['Error Flag']]]
        assert_frame_equal(test_results.reset_index(drop=True), expected, check_dtype=False)

        # Functional tests
        results = pecos.monitoring.check_timestamp(self.raw_data, 900)
        results = pecos.monitoring.check_corrupt(results['cleaned_data'], [-999])
        raw_data = results['cleaned_data'].loc[self.time_filter[0],:]
        
        results = pecos.monitoring.check_delta(raw_data[['A']],[0.0001, None], window=2*3600)
        test_results = results['test_results']
        print(test_results)
        assert_frame_equal(test_results,
                           expected.loc[expected['Variable Name'] == 'A',:].reset_index(drop=True), 
                           check_dtype=False)

    def test_composite_signal(self):
        self.pm.check_corrupt([-999])

        elapsed_time = self.pm.get_elapsed_time()
        wave_model = np.sin(10*(elapsed_time/86400))
        wave_model_abs_error = np.abs(np.subtract(self.pm.df[self.pm.trans['Wave']], wave_model))
        wave_model_abs_error.columns=['Wave Error C', 'Wave Error D']
        self.pm.add_dataframe(wave_model_abs_error)
        self.pm.add_translation_dictionary({'Wave Error': ['Wave Error C', 'Wave Error D']})

        self.pm.check_range([None, 0.25], 'Wave Error')

        temp = self.pm.test_results[['Data' in ef for ef in self.pm.test_results['Error Flag']]]
        temp.index = np.arange(temp.shape[0])

        expected = pd.DataFrame(
            [('Wave Error C',pd.Timestamp('2015-01-01 13:00:00'),pd.Timestamp('2015-01-01 14:45:00'),8.0,'Data > upper bound, 0.25')],
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'])

        assert_frame_equal(temp, expected, check_dtype=False)

    def test_full_example(self):
        data_file = join(simpleexampledir,'simple.xlsx')
        df = pd.read_excel(data_file, index_col=0)

        QCI = simple_example_run_analysis(df)

        assert_almost_equal(QCI.iloc[0,0],0.852113,6)

        actual = pd.read_csv('test_results.csv', index_col=0)
        # Convert back to datetime just so that they are in the same format
        actual['Start Time'] = pd.to_datetime(actual['Start Time'])
        actual['End Time'] = pd.to_datetime(actual['End Time'])
        
        expected = pd.read_csv(join(datadir,'Simple_test_results.csv'), index_col=0)
        # Convert back to datetime just so that they are in the same format
        expected['Start Time'] = pd.to_datetime(expected['Start Time'])
        expected['End Time'] = pd.to_datetime(expected['End Time'])
        
        assert_frame_equal(actual, expected, check_dtype=False)

    def test_full_example_with_timezone(self):
        data_file = join(simpleexampledir,'simple.xlsx')
        df = pd.read_excel(data_file, index_col=0)
        df.index = df.index.tz_localize('MST')

        QCI = simple_example_run_analysis(df)

        assert_almost_equal(QCI.iloc[0,0],0.852113,6)

        actual = pd.read_csv('test_results.csv', index_col=0)
        expected = pd.read_csv(join(datadir,'Simple_test_results_with_timezone.csv'), index_col=0)
        assert_frame_equal(actual, expected, check_dtype=False)

class Test_get_time(unittest.TestCase):

    @classmethod
    def setUp(self):
        self.nPeriods = 48
        index = pd.date_range('1/1/1990 2:15', periods=self.nPeriods, freq='H')
        data = np.random.rand(self.nPeriods)
        df = pd.DataFrame(data=data, index=index, columns=['test'])

        self.pm = pecos.monitoring.PerformanceMonitoring()
        self.pm.add_dataframe(df)

    @classmethod
    def tearDown(self):
        pass

    def test_get_elapsed_time(self):
        elapsed_time = self.pm.get_elapsed_time()
        expected = np.arange(0,self.nPeriods*3600,3600)
        assert_list_equal(elapsed_time.iloc[:,0].values.tolist(), expected.tolist())

    def test_get_clock_time(self):
        clock_time = self.pm.get_clock_time()
        expected = np.mod(np.arange(2.25*3600,(self.nPeriods+2.25)*3600,3600), 86400)
        assert_list_equal(clock_time.iloc[:,0].values.tolist(), expected.tolist())

    def test_get_elapsed_time_with_timezone(self):
        self.pm.df.index = self.pm.df.index.tz_localize('MST')
        elapsed_time = self.pm.get_elapsed_time()
        expected = np.arange(0,self.nPeriods*3600,3600)
        assert_list_equal(elapsed_time.iloc[:,0].values.tolist(), expected.tolist())

    def test_get_clock_time_with_timezone(self):
        self.pm.df.index = self.pm.df.index.tz_localize('MST')
        clock_time = self.pm.get_clock_time()
        expected = np.mod(np.arange(2.25*3600,(self.nPeriods+2.25)*3600,3600), 86400)
        assert_list_equal(clock_time.iloc[:,0].values.tolist(), expected.tolist())


class Test_check_timestamp(unittest.TestCase):

    @classmethod
    def setUp(self):
        # one occurance in the first hour, none in the second, and two in
        # the third
        index = pd.DatetimeIndex([pd.Timestamp('20161017 01:05:00'),
                                  pd.Timestamp('20161017 03:03:00'),
                                  pd.Timestamp('20161017 03:50:00')])
        df = pd.DataFrame({'A': [0, 2, 3], 'B': [4, np.nan, 6]}, index=index)

        self.pm = pecos.monitoring.PerformanceMonitoring()
        self.pm.add_dataframe(df)

    @classmethod
    def tearDown(self):
        pass

    def test_check_exact_times_true(self):
        self.pm.check_timestamp(3600, exact_times=True)
        expected = pd.DataFrame(
            array([['', Timestamp('2016-10-17 02:05:00'),
                   Timestamp('2016-10-17 03:05:00'), 2,
                   'Missing timestamp']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=1, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)

    def test_check_exact_times_false(self):
        self.pm.check_timestamp(3600, exact_times=False)
        expected = pd.DataFrame(
            array([['', Timestamp('2016-10-17 02:00:00'),
                    Timestamp('2016-10-17 02:00:00'), 1, 'Missing timestamp']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=1, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)

    def test_check_exact_times_true_with_start_time(self):
        self.pm.check_timestamp(3600, expected_start_time=Timestamp('2016-10-17 01:00:00'), exact_times=True)
        expected = pd.DataFrame(
            array([['', Timestamp('2016-10-17 01:00:00'),
                   Timestamp('2016-10-17 03:00:00'), 3,
                   'Missing timestamp']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=1, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)

class Test_check_delta(unittest.TestCase):

    @classmethod
    def setUp(self):
        index = pd.date_range('1/1/2017', periods=24, freq='H')
        data = {'A': [0.5,-0.3,0.2,0,0.5,-0.45,0.35,-0.4,0.5,1.5,0.5,-0.5,0.5,-0.5,5,6,10,10.5,10,10.3,10,10.8,10,9.9], 
                'B': [0,1,2.2,3,3.8,5,6,7.1,8,9,10,5,-2,1,0,0.5,0,5,3,9.5,8.2,7,np.nan,5]}
        df = pd.DataFrame(data, index=index)
        trans = dict(zip(df.columns, [[col] for col in df.columns]))
        
        self.pm = pecos.monitoring.PerformanceMonitoring()
        self.pm.add_dataframe(df)
        self.pm.add_translation_dictionary(trans)

    @classmethod
    def tearDown(self):
        pass
    
    def test_deadsensor(self):
        # dead sensor = < 1 in 5 hours
        self.pm.check_delta([1, None], window=5*3600+1, absolute_value=True)
        expected = pd.DataFrame(
            array([['A', Timestamp('2017-01-01 00:00:00'), Timestamp('2017-01-01 05:00:00'), 6, '|Delta| < lower bound, 1'],
                   ['A', Timestamp('2017-01-01 16:00:00'), Timestamp('2017-01-01 23:00:00'), 8, '|Delta| < lower bound, 1']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=2, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)
        
    def test_abrupt_change(self):
        # abrupt change = > 7 in 3 hours
        self.pm.check_delta([None, 7], window=3*3600+1, absolute_value=True)
        expected = pd.DataFrame(
            array([['A', Timestamp('2017-01-01 13:00:00'), Timestamp('2017-01-01 16:00:00'), 4, '|Delta| > upper bound, 7'],
                   ['B', Timestamp('2017-01-01 10:00:00'), Timestamp('2017-01-01 12:00:00'), 3, '|Delta| > upper bound, 7'],
                   ['B', Timestamp('2017-01-01 16:00:00'), Timestamp('2017-01-01 19:00:00'), 4, '|Delta| > upper bound, 7']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=3, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)
    
    def test_abrupt_positive_change(self):
        # abrupt positive change = > 7 in 3 hours
        self.pm.check_delta([None, 7], window=3*3600+1, absolute_value=False)
        expected = pd.DataFrame(
            array([['A', Timestamp('2017-01-01 13:00:00'), Timestamp('2017-01-01 16:00:00'), 4, 'Delta > upper bound, 7'],
                   ['B', Timestamp('2017-01-01 16:00:00'), Timestamp('2017-01-01 19:00:00'), 4, 'Delta > upper bound, 7']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=2, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)
        
    def test_abrupt_negative_change(self):
        # abrupt negative change = < -7 in 3 hours
        self.pm.check_delta([-7, None], window=3*3600+1, absolute_value=False)
        expected = pd.DataFrame(
            array([['B', Timestamp('2017-01-01 10:00:00'), Timestamp('2017-01-01 12:00:00'), 3, 'Delta < lower bound, -7']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=1, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)

class Test_check_outlier(unittest.TestCase):

    @classmethod
    def setUp(self):
        index = pd.date_range('1/1/2017', periods=24, freq='H')
        data = {'A': [112,114,113,132,134,127,150,120,117,112,107,99,140,
                      98,88,98,106,110,107,79,102,115,np.nan,91]}
        df = pd.DataFrame(data, index=index)
        trans = dict(zip(df.columns, [[col] for col in df.columns]))
        
        self.pm = pecos.monitoring.PerformanceMonitoring()
        self.pm.add_dataframe(df)
        self.pm.add_translation_dictionary(trans)
        
    @classmethod
    def tearDown(self):
        pass
    
    def test_outlier(self):
        # outlier if stdev > 1.9
        self.pm.check_outlier([-1.9, 1.9], window=None, absolute_value=False)
        expected = pd.DataFrame(
            array([['A', Timestamp('2017-01-01 19:00:00'), Timestamp('2017-01-01 19:00:00'), 1, 'Outlier < lower bound, -1.9'],
                   ['A', Timestamp('2017-01-01 06:00:00'), Timestamp('2017-01-01 06:00:00'), 1, 'Outlier > upper bound, 1.9']], dtype=object),
            columns=['Variable Name', 'Start Time', 'End Time', 'Timesteps', 'Error Flag'],
            index=RangeIndex(start=0, stop=2, step=1)
            )
        assert_frame_equal(expected, self.pm.test_results)

if __name__ == '__main__':
    unittest.main()
