import unittest
from nose.tools import *
from pandas.util.testing import assert_frame_equal
import pandas as pd
import pecos

class TestConvertIndex(unittest.TestCase):

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
    
        index_int = [14,30,40,44,59,60,74,92,105,125]

        self.df = pd.DataFrame(index=index)
        self.df_int = pd.DataFrame(index=index_int)
        
    @classmethod
    def tearDown(self):
        pass
    
    def convert_index_to_datetime(self):
        df = pecos.utils.convert_index_to_datetime(self.df_int, unit='s', origin='1/1/2016')
        assert_frame_equal(df, self.df)
    
    def convert_index_to_elapsed_time(self):
        df_int = pecos.utils.convert_index_to_elapsed_time(self.df)
        assert_frame_equal(df_int, self.df_int)
    
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
        new_df = pecos.utils.round_index(self.df, 15, 'nearest')
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
        diff = new_df.index.difference(nearest_index)
        assert_equals(len(diff), 0)
    
    def test_round_index_floor(self):
        new_df = pecos.utils.round_index(self.df, 15, 'floor')
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
        diff = new_df.index.difference(floor_index)
        assert_equals(len(diff), 0)
    
    def test_round_index_ceiling(self):
        new_df = pecos.utils.round_index(self.df, 15, 'ceiling')
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
        diff = new_df.index.difference(ceiling_index)
        assert_equals(len(diff), 0)
    
    def test_round_index_invalid(self):
        new_df = pecos.utils.round_index(self.df, 15, 'invalid')
        diff = new_df.index.difference(self.df.index)
        assert_equals(len(diff), 0)

if __name__ == '__main__':
    unittest.main()