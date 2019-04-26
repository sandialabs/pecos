"""
This example is the same as simple_example.py, but it uses a configuration 
file to define the quality control analysis input.
"""
import pecos
import pandas as pd
import matplotlib.pyplot as plt
import os
import yaml

# Initialize logger
pecos.logger.initialize()

# Open configuration file and extract information
config_file = 'simple_config.yml'
fid = open(config_file, 'r')
config = yaml.load(fid)
fid.close()
specs = config['Specifications']
translation_dictionary = config['Translation']
composite_signals = config['Composite Signals']
time_filter = config['Time Filter']
corrupt_values = config['Corrupt Values']
range_bounds = config['Range Bounds']
increment_bounds = config['Increment Bounds']
   
# Create a Pecos PerformanceMonitoring data object
pm = pecos.monitoring.PerformanceMonitoring()

# Populate the object with a DataFrame and translation dictionary
system_name = 'Simple'
data_file = 'simple.xlsx'
df = pd.read_excel(data_file, index_col=0)
pm.add_dataframe(df)
pm.add_translation_dictionary(translation_dictionary)

# Check the expected frequency of the timestamp
pm.check_timestamp(specs['Frequency'])
 
# Generate a time filter to exclude data points early and late in the day
time_filter = pm.evaluate_string('Time Filter', time_filter)
pm.add_time_filter(time_filter)

# Check for missing data
pm.check_missing()
        
# Check for corrupt data values
pm.check_corrupt(corrupt_values) 

# Add a composite signal which compares measurements to a model
for composite_signal in composite_signals:
    for key, value in composite_signal.items():
        signal = pm.evaluate_string(key, value, specs)
        pm.add_dataframe(signal)
        pm.add_translation_dictionary({key: list(signal.columns)})

# Check data for expected ranges
for key,value in range_bounds.items():
    pm.check_range(value, key)

# Check data for stagnant and abrupt changes
for key,value in increment_bounds.items():
    pm.check_increment(value, key) 
    
# Compute the quality control index
mask = pm.get_test_results_mask()
del mask['Wave Model'] # Not counted in the QCI
QCI = pecos.metrics.qci(mask, pm.tfilter)

 # Define output files and directories
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
