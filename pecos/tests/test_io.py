import unittest
import os
from os.path import abspath, dirname, join, isfile
import pandas as pd
import numpy as np
import inspect
import matplotlib.pylab as plt
import logging

import pecos

testdir = dirname(abspath(inspect.getfile(inspect.currentframe())))
datadir = abspath(join(testdir, 'data'))    

class TestIO(unittest.TestCase):
    
    def test_read_campbell_scientific(self):
        file_name = join(datadir,'TEST_db1_2014_01_01.dat')
        self.assertTrue(isfile(file_name))
        
        df = pecos.io.read_campbell_scientific(file_name, 'TIMESTAMP')
        self.assertEqual((48,11), df.shape)
    
    def test_write_metrics1(self):
        filename = abspath(join(testdir, 'metrics.csv'))
        if isfile(filename):
            os.remove(filename)
            
        metrics = pd.DataFrame({'metric1' : pd.Series([1.], index=[pd.to_datetime("2016-01-01")])})
        filename = pecos.io.write_metrics(metrics, filename)
        self.assertTrue(isfile(filename))
        
        from_file1 = pd.read_csv(filename)
        self.assertEqual(from_file1.shape, (1,2))
        
        # append another date
        metrics = pd.DataFrame({'metric1' : pd.Series([2.], index=[pd.to_datetime("2016-01-02")])})
        filename = pecos.io.write_metrics(metrics, filename)
        
        from_file2 = pd.read_csv(filename)
        self.assertEqual(from_file2.shape, (2,2))
        
        # append another metric
        metrics = pd.DataFrame({'metric2' : pd.Series([3.], index=[pd.to_datetime("2016-01-02")])})
        filename = pecos.io.write_metrics(metrics, filename)
        
        from_file3 = pd.read_csv(filename)
        self.assertEqual(from_file3.shape, (2,3))
    
    def test_write_test_results1(self):
        filename = abspath(join(testdir, 'test_results.csv'))
        if isfile(filename):
            os.remove(filename)
            
        pm = pecos.monitoring.PerformanceMonitoring()
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,5,6], [7,8,9], [10,11,12], [13,14,15]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
        tfilter = pd.Series(data = (df.index < index[3]), index = df.index)
        pm.add_dataframe(df)
        pm.add_time_filter(tfilter)    
        pm.check_range([0,7]) # 2 test failures
        
        filename = pecos.io.write_test_results(pm.test_results)
        from_file = pd.read_csv(filename)
        
        self.assertTrue(isfile(filename))
        self.assertEqual(from_file.shape, (2,6))
    
    def test_write_monitoring_report1(self): # empty database
        filename = abspath(join(testdir, 'monitoring_report.html'))
        if isfile(filename):
            os.remove(filename)
            
        pm = pecos.monitoring.PerformanceMonitoring()
    
        filename = pecos.io.write_monitoring_report(pm.df, pm.test_results) 
        
        self.assertTrue(isfile(filename))
        
    def test_write_monitoring_report2(self):# with test results and graphics (encoded and linked)
        filename1 = abspath(join(testdir, 'test_write_monitoring_report2_linked_graphics.html'))
        filename2 = abspath(join(testdir, 'test_write_monitoring_report2_encoded_graphics.html'))
        graphics_filename = abspath(join(testdir, 'custom_graphic.png'))
        if isfile(filename1):
            os.remove(filename1)
        if isfile(filename2):
            os.remove(filename2)
        if isfile(graphics_filename):
            os.remove(graphics_filename)
            
        pecos.logger.initialize()
        logger = logging.getLogger('pecos')
        
        pm = pecos.monitoring.PerformanceMonitoring()
        periods = 5
        index = pd.date_range('1/1/2016', periods=periods, freq='h')
        data = np.array([[1,2,3], [4,5,6], [7,8,9], [10,11,12], [13,14,15]])
        df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
        tfilter = pd.Series(data = (df.index < index[3]), index = df.index)
        pm.add_dataframe(df)
        pm.add_time_filter(tfilter)    
        pm.check_range([0,7]) # 2 test failures
        
        filename_root = abspath(join(testdir, 'monitoring_report_graphic'))
        test_results_graphics = pecos.graphics.plot_test_results(pm.df, pm.test_results, 
                                                                 filename_root=filename_root)
        
        plt.figure()
        plt.plot([1, 2, 3],[1, 2, 3])
        plt.savefig(graphics_filename, format='png')
        plt.close()
        custom_graphics = [graphics_filename]
        
        logger.warning('Add a note')
        
        filename1 = pecos.io.write_monitoring_report(pm.df, pm.test_results, 
                                         test_results_graphics, custom_graphics, encode=False,
                                         filename='test_write_monitoring_report2_linked_graphics.html')
        
        self.assertTrue(isfile(filename1))
        
        filename2 = pecos.io.write_monitoring_report(pm.df, pm.test_results, 
                                         test_results_graphics, custom_graphics, encode=True,
                                         filename=filename2)
        
        self.assertTrue(isfile(filename2))
    
        
    def test_write_dashboard1(self): # empty content
        filename = abspath(join(testdir, 'dashboard.html'))
        if isfile(filename):
            os.remove(filename)
            
        column_names = ['loc1', 'loc2']
        row_names = ['sys1', 'sys2']
        content = {}
        content[('sys1', 'loc1')] = {}
        content[('sys1', 'loc2')] = {}
        content[('sys2', 'loc1')] = {}
        content[('sys2', 'loc2')] = {}
        
        filename = pecos.io.write_dashboard(column_names, row_names, content)
        
        self.assertTrue(isfile(filename))
    
    
    def test_write_dashboard2(self): # with text, graphics (encoded and linked), tables, and links
        filename1 = abspath(join(testdir, 'test_write_dashboard2_linked_graphics.html.html'))
        filename2 = abspath(join(testdir, 'test_write_dashboard2_encoded_graphics.html.html'))
        graphics_filename = abspath(join(testdir, 'dashboard_graphic.png'))
        if isfile(filename1):
            os.remove(filename1)
        if isfile(filename2):
            os.remove(filename2)
        if isfile(graphics_filename):
            os.remove(graphics_filename)
            
        plt.figure()
        plt.plot([1, 2, 3],[1, 2, 3])
        plt.savefig(graphics_filename, format='png')
        plt.close()
        
        column_names = ['loc1', 'loc2']
        row_names = ['sys1', 'sys2']
        content = {}
        content[('sys1', 'loc1')] = {'text': 'sys1-loc1 text', 
                                     'graphics': [graphics_filename], 
                                     'link': {'Google': 'https://www.google.com', 'Pecos': 'http://pecos.readthedocs.io'} }
        content[('sys1', 'loc2')] = {'text': 'sys1-loc2 text',
                                     'table': pd.DataFrame({'sys1': [1,2,3]}).to_html()}
        content[('sys2', 'loc1')] = {'text': 'sys2-loc1 text',
                                     'graphics': [graphics_filename],
                                     'link': {'Google': 'https://www.google.com', 'Pecos': 'http://pecos.readthedocs.io'} }
        content[('sys2', 'loc2')] = {'text': 'sys2-loc2 text',
                                     'table': pd.DataFrame({'sys2': [2,4,6]}).to_html()}
        
        filename1 = pecos.io.write_dashboard(column_names, row_names, content, filename1, encode=False)
        
        self.assertTrue(isfile(filename1))
        
        filename2 = pecos.io.write_dashboard(column_names, row_names, content, filename2, encode=True)
        
        self.assertTrue(isfile(filename2))
        
    def test_email_message(self):
        subject = 'test subject'
        body = 'test body'
        recipient = ['recipient.email.address']
        sender = 'sender.email.address'
        
        msg = pecos.io._create_email_message(subject, body, recipient, sender)
    
        self.assertTrue(subject in msg.as_string())
        self.assertTrue(body in msg.as_string())
        self.assertTrue(recipient[0] in msg.as_string())
        self.assertTrue(sender in msg.as_string())

if __name__ == '__main__':
    unittest.main()