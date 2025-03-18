import unittest
from os.path import abspath, dirname, join, isfile
import os
import pandas as pd
import numpy as np
import inspect
import matplotlib.pylab as plt

import pecos

testdir = dirname(abspath(inspect.getfile(inspect.currentframe())))
datadir = abspath(join(testdir, 'data'))


class TestGraphics(unittest.TestCase):

    def test_plot_scatter1(self):            
        filename = abspath(join(testdir, 'plot_scatter1.png'))
        if isfile(filename):
            os.remove(filename)
            
        x = pd.DataFrame({'x1' : pd.Series([1., 2., 3.], index=['a', 'b', 'c'])})
        y = pd.DataFrame({'y1' : pd.Series([1., 2., 3.], index=['a', 'b', 'c'])})
        
        plt.figure()
        pecos.graphics.plot_scatter(x,y,xaxis_min=0.5, xaxis_max=6.5, yaxis_min=0.5, yaxis_max=3.5)
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_scatter2(self):
        filename = abspath(join(testdir, 'plot_scatter2.png'))
        if isfile(filename):
            os.remove(filename)
            
        x = pd.DataFrame({'x1' : pd.Series([1., 2., 3.], index=['a', 'b', 'c']),
             'x2' : pd.Series([4., 5., 6.], index=['a', 'b', 'c'])})
        y = pd.DataFrame({'y1' : pd.Series([1., 2., 3.], index=['a', 'b', 'c'])})
        
        plt.figure()
        pecos.graphics.plot_scatter(x,y,title='scatter2')
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_scatter3(self):
        filename = abspath(join(testdir, 'plot_scatter3.png'))
        if isfile(filename):
            os.remove(filename)
            
        y = pd.DataFrame({'y1' : pd.Series([1., 2., 3.], index=['a', 'b', 'c']),
             'y2' : pd.Series([4., 5., 6.], index=['a', 'b', 'c'])})
        x = pd.DataFrame({'x1' : pd.Series([1., 2., 3.], index=['a', 'b', 'c'])})
        
        plt.figure()
        pecos.graphics.plot_scatter(x,y,xaxis_min=0.5, xaxis_max=3.5, yaxis_min=0.5, yaxis_max=6.5)
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_timeseries1(self):
        filename = abspath(join(testdir, 'plot_timeseries1.png'))
        if isfile(filename):
            os.remove(filename)
            
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,5,6], [7,8,9], [10,11,12], [13,14,15]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
        
        plt.figure()
        pecos.graphics.plot_timeseries(df,yaxis_min=0, yaxis_max=20)
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_timeseries2(self):
        filename = abspath(join(testdir, 'plot_timeseries2.png'))
        if isfile(filename):
            os.remove(filename)
            
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,5,6], [7,8,9], [10,11,12], [13,14,15]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
        tfilter = pd.Series(data = (df.index < index[3]), index = df.index)
        
        plt.figure()
        pecos.graphics.plot_timeseries(df,tfilter, yaxis_min=0, yaxis_max=20)
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_interactive_timeseries1(self):
        filename = abspath(join(testdir, 'plot_interactive_timeseries1.html'))
        if isfile(filename):
            os.remove(filename)
            
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='D')
        data = np.random.rand(periods, 4)
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C', 'D'])
    
        pecos.graphics.plot_interactive_timeseries(df, filename=filename, auto_open=False)
        
        self.assertTrue(isfile(filename))

    def test_plot_heatmap1(self):
        filename = abspath(join(testdir, 'plot_heatmap1.png'))
        if isfile(filename):
            os.remove(filename)
            
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='D')
        data = np.random.rand(periods, 4)
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C', 'D'])
        
        plt.figure()
        pecos.graphics.plot_heatmap(df)
        plt.savefig(filename, format='png', bbox_inches='tight', pad_inches = 0)
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_heatmap2(self):
        filename = abspath(join(testdir, 'plot_heatmap2.png'))
        if isfile(filename):
            os.remove(filename)
            
        data = np.array([[1,2],[3,4]])
        
        plt.figure()
        pecos.graphics.plot_heatmap(data, cmap='jet', show_axis=True)
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_doy_heatmap1(self):
        filename = abspath(join(testdir, 'plot_doy_heatmap1.png'))
        if isfile(filename):
            os.remove(filename)
            
        periods = 5*24 # 5 days
        index = pd.date_range('3/1/2016', periods=periods, freq='h')
        data = np.random.rand(periods)
        df = pd.DataFrame(data=data, index=index, columns=['A'])
        
        plt.figure()
        pecos.graphics.plot_doy_heatmap(df['A'])
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_doy_heatmap2(self):
        filename = abspath(join(testdir, 'plot_doy_heatmap2.png'))
        if isfile(filename):
            os.remove(filename)
            
        periods = 365*12
        index = pd.date_range('1/1/2016', periods=periods, freq='2h')
        data = np.random.rand(periods)
        df = pd.DataFrame(data=data, index=index, columns=['A'])
        overlay = pd.DataFrame(index=[1,100,200,300,365], 
                               data={'A': [40000,20000,60000,10000,5000],
                                     'B': [60000,70000,75000,50000,65000]})
        
        plt.figure()
        pecos.graphics.plot_doy_heatmap(df['A'], cmap='gray', overlay=overlay)
        plt.savefig(filename, format='png')
        plt.close()
        
        self.assertTrue(isfile(filename))

    def test_plot_test_results1(self):
        filename_root = abspath(join(testdir, 'plot_test_results1'))
        pm = pecos.monitoring.PerformanceMonitoring()
        
        graphics = pecos.graphics.plot_test_results(pm.df, pm.test_results, pm.tfilter, 
                                                    filename_root=filename_root)
        
        self.assertEqual(graphics,[])

    def test_plot_test_results2(self):
        filename_root = abspath(join(testdir, 'plot_test_results2'))
        pm = pecos.monitoring.PerformanceMonitoring()
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,5,6], [7,8,9], [10,11,12], [13,14,15]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
        tfilter = pd.Series(data = (df.index < index[3]), index = df.index)
        
        pm.add_dataframe(df)
        pm.add_time_filter(tfilter)
        
        pm.check_range([0,7]) # 2 test failures
        
        graphics = pecos.graphics.plot_test_results(pm.df, pm.test_results, pm.tfilter, 
                                                    filename_root=filename_root)
        
        self.assertEqual(len(graphics),2)


if __name__ == '__main__':
    unittest.main()
