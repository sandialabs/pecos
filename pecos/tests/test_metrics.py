import unittest
from pandas.testing import assert_frame_equal
from os.path import abspath, dirname, join
import numpy as np
import pandas as pd

import pecos

testdir = dirname(abspath(__file__))
datadir = join(testdir,'data')


class TestMetrics(unittest.TestCase):

    def test_pd_far(self):
        index = pd.date_range('1/1/2016', periods=4, freq='h')
        
        actual = np.array([[True,  False, False], 
                           [False, False, True], 
                           [True,  False, False], 
                           [True,  True,  True]])
        actual = pd.DataFrame(data=actual, index=index, columns=['A', 'B', 'C'])
        
        obser = np.array([[True, False, True], 
                          [True, False, True], 
                          [True, True,  False], 
                          [True, False, False]])
        obser = pd.DataFrame(data=obser, index=index, columns=['A', 'B', 'C'])
        
        prob_detection = pecos.metrics.probability_of_detection(obser, actual)
        false_alarm = pecos.metrics.false_alarm_rate(obser, actual)
        
        self.assertAlmostEqual(prob_detection['A'], 0/1.0, 5)
        self.assertAlmostEqual(prob_detection['B'], 2/3.0, 5)
        self.assertAlmostEqual(prob_detection['C'], 1/2.0, 5)
        
        self.assertAlmostEqual(false_alarm['A'], 1-3/3.0, 5)
        self.assertAlmostEqual(false_alarm['B'], 1-0/1.0, 5)
        self.assertAlmostEqual(false_alarm['C'], 1-1/2.0, 5)

    def test_integral(self):
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,4,3], [7,6,np.nan], [4,8,4], [1,8.5,6]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
        
        integral = pecos.metrics.time_integral(df)
        print(integral)
        self.assertEqual(integral['A'], 57600)
        self.assertEqual(integral['B'], 83700)
        self.assertEqual(integral['C'], 41400)
    
        # test with irregular timesteps
        index = index[[0,1,3,4]]
        data = data[[0,1,3,4]]
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    
        integral = pecos.metrics.time_integral(df)
    
        self.assertEqual(integral['A'], 46800)
        self.assertEqual(integral['B'], 83700)
        self.assertEqual(integral['C'], 54000)

    def test_derivative(self):
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,4,3], [7,6,np.nan], [4,8,4], [1,8.5,6]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    
        derivative = pecos.metrics.time_derivative(df)
    
        expected = np.array([[3.0/3600, 2.0/3600, 0], 
                             [3.0/3600, 2.0/3600, np.nan], 
                             [0, 2.0/3600, 1.0/7200], 
                             [-3.0/3600, 1.25/3600, np.nan],
                             [-3.0/3600, 0.5/3600, 2.0/3600]])
        expected = pd.DataFrame(data=expected, index=index, columns=['A', 'B', 'C'])
    
        assert_frame_equal(expected, derivative)
    
        # test with irregular timesteps
        index = index[[0,1,2,4]]
        data = data[[0,1,2,4]]
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    
        derivative = pecos.metrics.time_derivative(df)
    
        expected = np.array([[3.0/3600, 2.0/3600, 0], 
                             [3.0/3600, 2.0/3600, np.nan], 
                             [1.0/3600, 1.75/3600, np.nan],
                             [-3.0/3600, 1.25/3600, np.nan]])
        expected = pd.DataFrame(data=expected, index=index, columns=['A', 'B', 'C'])
    
        assert_frame_equal(expected, derivative)

    def test_qci_no_test_results(self):
        periods = 5
        np.random.seed(100)
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data=np.sin(np.random.rand(3,1)*np.arange(0,periods,1))
        df = pd.DataFrame(data=data.transpose(), index=index, columns=['A', 'B', 'C'])
        trans = dict(zip(df.columns, [[col] for col in df.columns]))
        
        pm = pecos.monitoring.PerformanceMonitoring()
        pm.add_dataframe(df)
        pm.add_translation_dictionary(trans)
        
        mask = pm.mask
        QCI = pecos.metrics.qci(mask)
        
        self.assertEqual(mask.any().any(), True)
        self.assertEqual(QCI['A'], 1)
        self.assertEqual(QCI['B'], 1)
        self.assertEqual(QCI['C'], 1)

    def test_qci_with_test_results(self):
        periods = 5
        np.random.seed(100)
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data=np.sin(np.random.rand(3,1)*np.arange(0,periods,1))
        df = pd.DataFrame(data=data.transpose(), index=index, columns=['A', 'B', 'C'])
        trans = dict(zip(df.columns, [[col] for col in df.columns]))
        
        pm = pecos.monitoring.PerformanceMonitoring()
        pm.add_dataframe(df)
        pm.add_translation_dictionary(trans)
        
        test_result = pd.DataFrame({
        'Variable Name': 'A', 
        'Start Time': '2016-01-01 01:00:00', 
        'End Time': '2016-01-01 04:00:00', 
        'Timesteps': 4, 
        'Error Flag': 'Error Flag'}, index=[1])
        pm.test_results = pd.concat([pm.test_results, test_result])
        
        test_result = pd.DataFrame({
        'Variable Name': 'B', 
        'Start Time': '2016-01-01 01:00:00', 
        'End Time': '2016-01-01 01:00:00', 
        'Timesteps': 1, 
        'Error Flag': 'Error Flag'}, index=[2])
        pm.test_results = pd.concat([pm.test_results, test_result])
        mask = pm.mask
        QCI = pecos.metrics.qci(mask)
        
        expected_mask = pd.DataFrame(data=[[False, False, True],[False, True, True],[False, True, True],[False, True, True],[False, True, True]], 
                                     index=pm.df.index, 
                                     columns=pm.df.columns)
        
        self.assertEqual((mask == expected_mask).any().any(), True)
        self.assertEqual(QCI.mean(), (15-5)/15.0)
    
        tfilter = pd.Series(data = [True, False, True, True, True], index=pm.df.index)
        QCI_with_tfilter = pecos.metrics.qci(mask, tfilter = tfilter)
        
        self.assertEqual(QCI_with_tfilter.mean(), (12-3)/12.0)

    def test_rmse(self):
        
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        x1 = pd.DataFrame(data=np.array([4, 4, 4.5, 2.7, 6]), index=index, columns=['Power'])
        x2 = pd.DataFrame(data=np.array([5,10,4.5,3,4]), index=index, columns=['Power'])
        
        RMSE = pecos.metrics.rmse(x1, x2)
    
        self.assertAlmostEqual(RMSE['Power'], 2.8667, 4)


if __name__ == '__main__':
    unittest.main()
