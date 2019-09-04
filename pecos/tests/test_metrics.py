from nose.tools import *
from os.path import abspath, dirname, join
import pecos
import numpy as np
import pandas as pd

testdir = dirname(abspath(__file__))
datadir = join(testdir,'data')

def test_pd_far():
    index = pd.date_range('1/1/2016', periods=4, freq='H')
    
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
    
    assert_almost_equal(prob_detection, 3/6.0, 5)
    assert_almost_equal(false_alarm, 2/6.0, 5)
    
def test_time_integral():
    periods = 5
    index = pd.date_range('1/1/2016', periods=periods, freq='H')
    data = np.array([[1,2,3], [4,5,6], [7,8,9], [10,11,12], [13,14,15]])
    df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    
    df_integral = pecos.metrics.time_integral(df)
    
    assert_equal(df_integral['Time integral of A'].values[0], 100800)
    assert_equal(df_integral['Time integral of B'].values[0], 115200)
    assert_equal(df_integral['Time integral of C'].values[0], 129600)
    
def test_qci_no_test_results():
    periods = 5
    np.random.seed(100)
    index = pd.date_range('1/1/2016', periods=periods, freq='H')
    data=np.sin(np.random.rand(3,1)*np.arange(0,periods,1))
    df = pd.DataFrame(data=data.transpose(), index=index, columns=['A', 'B', 'C'])
    trans = dict(zip(df.columns, [[col] for col in df.columns]))
    
    pm = pecos.monitoring.PerformanceMonitoring()
    pm.add_dataframe(df)
    pm.add_translation_dictionary(trans)
    
    mask = pm.mask
    QCI = pecos.metrics.qci(mask, per_day=False)
    
    assert_equal(mask.any().any(), True)
    assert_equal(QCI, 1)
    
def test_qci_with_test_results():
    periods = 5
    np.random.seed(100)
    index = pd.date_range('1/1/2016', periods=periods, freq='H')
    data=np.sin(np.random.rand(3,1)*np.arange(0,periods,1))
    df = pd.DataFrame(data=data.transpose(), index=index, columns=['A', 'B', 'C'])
    trans = dict(zip(df.columns, [[col] for col in df.columns]))
    
    pm = pecos.monitoring.PerformanceMonitoring()
    pm.add_dataframe(df)
    pm.add_translation_dictionary(trans)
    
    test_result = {
    'Variable Name': 'A', 
    'Start Time': '2016-01-01 01:00:00', 
    'End Time': '2016-01-01 04:00:00', 
    'Timesteps': 4, 
    'Error Flag': 'Error Flag'}
    pm.test_results = pm.test_results.append(pd.DataFrame(test_result, index=[1]))
    
    test_result = {
    'Variable Name': 'B', 
    'Start Time': '2016-01-01 01:00:00', 
    'End Time': '2016-01-01 01:00:00', 
    'Timesteps': 1, 
    'Error Flag': 'Error Flag'}
    pm.test_results = pm.test_results.append(pd.DataFrame(test_result, index=[2]))
    mask = pm.mask
    QCI = pecos.metrics.qci(mask, per_day = False)
    
    expected_mask = pd.DataFrame(data=[[False, False, True],[False, True, True],[False, True, True],[False, True, True],[False, True, True]], 
                                 index=pm.df.index, 
                                 columns=pm.df.columns)
    
    assert_equal((mask == expected_mask).any().any(), True)
    assert_equal(QCI, (15-5)/15.0)

    tfilter = pd.Series(data = [True, False, True, True, True], index=pm.df.index)
    QCI_with_tfilter = pecos.metrics.qci(mask, tfilter = tfilter, per_day=False)
    
    assert_equal(QCI_with_tfilter, (12-3)/12.0)
    
def test_qci_perday():
    periods = 48
    np.random.seed(100)
    index = pd.date_range('1/1/2016', periods=periods, freq='H')
    data=np.sin(np.random.rand(3,1)*np.arange(0,periods,1))
    df = pd.DataFrame(data=data.transpose(), index=index, columns=['A', 'B', 'C'])
    trans = dict(zip(df.columns, [[col] for col in df.columns]))
    
    pm = pecos.monitoring.PerformanceMonitoring()
    pm.add_dataframe(df)
    pm.add_translation_dictionary(trans)
    
    test_result = {
    'Variable Name': 'A', 
    'Start Time': '2016-01-01 01:00:00', 
    'End Time': '2016-01-01 04:00:00', 
    'Timesteps': 4, 
    'Error Flag': 'Error Flag'}
    pm.test_results = pm.test_results.append(pd.DataFrame(test_result, index=[1]))
    
    test_result = {
    'Variable Name': 'B', 
    'Start Time': '2016-01-01 00:00:00', 
    'End Time': '2016-01-01 00:00:00', 
    'Timesteps': 1, 
    'Error Flag': 'Error Flag'}
    pm.test_results = pm.test_results.append(pd.DataFrame(test_result, index=[2]))
    
    mask = pm.mask
    QCI = pecos.metrics.qci(mask, per_day = False)
    assert_equal(QCI, (144-5)/144.0)
    
    QCI = pecos.metrics.qci(mask, per_day = True)
    assert_equal(QCI['Quality Control Index'][0], (72-5)/72.0)
    assert_equal(QCI['Quality Control Index'][1], 1.0)

def test_rmse():
    
    periods = 5
    index = pd.date_range('1/1/2016', periods=periods, freq='H')
    x1 = pd.DataFrame(data=np.array([4, 4, 4.5, 2.7, 6]), index=index, columns=['Power'])
    x2 = pd.DataFrame(data=np.array([5,10,4.5,3,4]), index=index, columns=['Expected Power'])
    
    RMSE = pecos.metrics.rmse(x1, x2)
    
    assert_almost_equal(RMSE.iloc[0,0], 2.8667, 4)