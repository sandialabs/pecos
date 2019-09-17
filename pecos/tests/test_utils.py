import unittest
import sys
from nose import SkipTest
from nose.tools import *
from pandas.util.testing import assert_frame_equal, assert_index_equal
import pandas as pd
import pecos

class TestConvertIndex(unittest.TestCase):

    @classmethod
    def setUp(self):
        index_dt = pd.DatetimeIndex(['1/1/2016 00:00:14', 
                          '1/1/2016 00:00:30',
                          '1/1/2016 00:00:40',
                          '1/1/2016 00:00:44',
                          '1/1/2016 00:00:59',
                          '1/1/2016 00:01:00',
                          '1/1/2016 00:01:14',
                          '1/1/2016 00:01:32',
                          '1/1/2016 00:01:45',
                          '1/1/2016 00:02:05',
                          '1/2/2016 00:00:05'])
    
        index_float = [14.0,30.0,40.0,44.0,59.0,60.0,74.0,92.0,105.0,125.0,86405.0]
        index_clock = [14.0,30.0,40.0,44.0,59.0,60.0,74.0,92.0,105.0,125.0,5.0]
        index_epoch = [1451606414.0, 1451606430.0, 1451606440.0, 1451606444.0, 1451606459.0,
               1451606460.0, 1451606474.0, 1451606492.0, 1451606505.0, 1451606525.0, 1451692805.0]
        
        data = {'A': range(11)}
        self.df_dt = pd.DataFrame(data, index=index_dt)
        self.df_float = pd.DataFrame(data, index=index_float)
        self.df_clock = pd.DataFrame(data, index=index_clock)
        self.df_epoch = pd.DataFrame(data, index=index_epoch)
        
    @classmethod
    def tearDown(self):
        pass
    
    def test_index_to_datetime(self):
        index = pecos.utils.index_to_datetime(self.df_float.index, unit='s', origin='1/1/2016')
        assert_index_equal(index, self.df_dt.index)
        
    def test_datetime_to_elapsedtime(self):
        index = pecos.utils.datetime_to_elapsedtime(self.df_dt.index, 14.0)
        assert_index_equal(index, self.df_float.index)
        
        # with timezone
        index_tz = self.df_dt.index.tz_localize('MST')
        index = pecos.utils.datetime_to_elapsedtime(index_tz, 14.0)
        assert_index_equal(index, self.df_float.index)
        
    def test_datetime_to_epochtime(self):
        if sys.version_info.major < 3:
            raise SkipTest # skip if python version < 3
        index = pecos.utils.datetime_to_epochtime(self.df_dt.index)
        assert_index_equal(index, self.df_epoch.index)
        
    def test_datetime_to_clocktime(self):
        index = pecos.utils.datetime_to_clocktime(self.df_dt.index)
        assert_index_equal(index, self.df_clock.index)
        
        # with timezone
        index_tz = self.df_dt.index.tz_localize('MST')
        index = pecos.utils.datetime_to_clocktime(index_tz)
        assert_index_equal(index, self.df_clock.index)
        
class TestRoundIndex(unittest.TestCase):

    @classmethod
    def setUp(self):
        index = pd.DatetimeIndex(['1/1/2016 00:00:14', 
                          '1/1/2016 00:00:30',
                          '1/1/2016 00:00:40',
                          '1/1/2016 00:00:44',
                          '1/1/2016 00:00:59',
                          '1/1/2016 00:01:00',
                          '1/1/2016 00:01:14',
                          '1/1/2016 00:01:32',
                          '1/1/2016 00:01:45',
                          '1/1/2016 00:02:05'])

        self.df = pd.DataFrame(index=index)

    @classmethod
    def tearDown(self):
        pass
    
    def test_round_index_nearest(self):
        index = pecos.utils.round_index(self.df.index, 15, 'nearest')
        nearest_index = pd.DatetimeIndex([
                              '1/1/2016 00:00:15', 
                              '1/1/2016 00:00:30',
                              '1/1/2016 00:00:45',
                              '1/1/2016 00:00:45',
                              '1/1/2016 00:01:00',
                              '1/1/2016 00:01:00',
                              '1/1/2016 00:01:15',
                              '1/1/2016 00:01:30',
                              '1/1/2016 00:01:45',
                              '1/1/2016 00:02:00'])
        diff = index.difference(nearest_index)
        assert_equals(len(diff), 0)
    
    def test_round_index_floor(self):
        index = pecos.utils.round_index(self.df.index, 15, 'floor')
        floor_index = pd.DatetimeIndex([
                              '1/1/2016 00:00:00', 
                              '1/1/2016 00:00:30',
                              '1/1/2016 00:00:30',
                              '1/1/2016 00:00:30',
                              '1/1/2016 00:00:45',
                              '1/1/2016 00:01:00',
                              '1/1/2016 00:01:00',
                              '1/1/2016 00:01:30',
                              '1/1/2016 00:01:45',
                              '1/1/2016 00:02:00'])
        diff = index.difference(floor_index)
        assert_equals(len(diff), 0)
    
    def test_round_index_ceiling(self):
        index = pecos.utils.round_index(self.df.index, 15, 'ceiling')
        ceiling_index = pd.DatetimeIndex([
                              '1/1/2016 00:00:15', 
                              '1/1/2016 00:00:30',
                              '1/1/2016 00:00:45',
                              '1/1/2016 00:00:45',
                              '1/1/2016 00:01:00',
                              '1/1/2016 00:01:00',
                              '1/1/2016 00:01:15',
                              '1/1/2016 00:01:45',
                              '1/1/2016 00:01:45',
                              '1/1/2016 00:02:15'])
        diff = index.difference(ceiling_index)
        assert_equals(len(diff), 0)
    
    def test_round_index_invalid(self):
        index = pecos.utils.round_index(self.df.index, 15, 'invalid')
        diff = index.difference(self.df.index)
        assert_equals(len(diff), 0)

if __name__ == '__main__':
    unittest.main()