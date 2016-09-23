"""
In this example, simple time series data is used to demonstrate basic functions
in pecos.  
* Data is loaded from an excel file which contains four columns of values that 
  are expected to follow linear, random, and sine models.
* A translation dictionary is defined to map and group the raw data into 
  common names for analysis
* A time filter is established to screen out data between 3 AM and 9 PM
* The data is loaded into a pecos PerformanceMonitoring object and a series of 
  quality control tests are run, including range tests and increment tests 
* The results are printed to csv and html reports
"""
import pecos
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import datetime

# Initialize logger
pecos.logger.initialize()

# Create a Pecos PerformanceMonitoring data object
pm = pecos.monitoring.PerformanceMonitoring()

# Populate the object with a dataframe and translation dictionary
system_name = 'Simple'
data_file = 'simple.xlsx'
df = pd.read_excel(data_file)
translation_dictionary = {
    'Linear': ['A'],
    'Random': ['B'],
    'Wave': ['C','D']}
pm.add_dataframe(df, system_name)
pm.add_translation_dictionary(translation_dictionary, system_name)

# Check timestamp
pm.check_timestamp(900)
 
# Generate a time filter

#clock_time = pm.get_clock_time()
#time_filter = (clock_time > 3*3600) & (clock_time < 21*3600)

#Faster time_filter without using get_clock_time
SetLimits = (df.index.time > datetime.time(1,00,00)) & (df.index.time < datetime.time(23,00,00))
time_filter = pd.DataFrame(data = SetLimits, index = df.index)

pm.add_time_filter(time_filter)

# Check missing
pm.check_missing()
        
# Check corrupt
pm.check_corrupt([-999]) 

# Add composite signals
elapsed_time= pm.get_elapsed_time()
wave_model = np.sin(10*(elapsed_time/86400))
wave_model.columns=['Wave Model']
pm.add_signal('Wave Model', wave_model)
wave_model_abs_error = np.abs(np.subtract(pm.df[pm.trans['Wave']], wave_model))
wave_model_abs_error.columns=['Wave Absolute Error C', 'Wave Absolute Error D']
pm.add_signal('Wave Absolute Error', wave_model_abs_error)

# Check range
pm.check_range([0, 1], 'Random')
pm.check_range([-1, 1], 'Wave')
pm.check_range([None, 0.25], 'Wave Absolute Error')

# Check increment
pm.check_increment([0.0001, None], 'Linear') 
pm.check_increment([0.0001, None], 'Random') 
pm.check_increment([0.0001, 0.6], 'Wave') 
    
# Compute metrics
mask = pm.get_test_results_mask()
QCI = pecos.metrics.qci(mask, pm.tfilter)

# Define output file names and directories
results_directory = 'Results'
if not os.path.exists(results_directory):
    os.makedirs(results_directory)
graphics_file_rootname = os.path.join(results_directory, 'test_results')
custom_graphics_file = os.path.abspath(os.path.join(results_directory, 'custom.png'))
metrics_file = os.path.join(results_directory, system_name + '_metrics.csv')
test_results_file = os.path.join(results_directory, system_name + '_test_results.csv')
report_file =  os.path.join(results_directory, system_name + '.html')

# Generate graphics
test_results_graphics = pecos.graphics.plot_test_results(graphics_file_rootname, pm)
plt.figure(figsize = (7.0,3.5))
ax = plt.gca()
df.plot(ax=ax, ylim=[-1.5,1.5])
plt.savefig(custom_graphics_file, format='png', dpi=500)

# Write metrics, test results, and report files
pecos.io.write_metrics(metrics_file, QCI)
pecos.io.write_test_results(test_results_file, pm.test_results)
pecos.io.write_monitoring_report(report_file, pm, test_results_graphics, [custom_graphics_file], QCI)
                                 
