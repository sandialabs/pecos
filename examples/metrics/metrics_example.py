"""
In this example, performance metrics from a pv system are analyzed to determine 
long term system health
* Daily performance metrics for 2015 are loaded from a csv file
* The files contain performance ratio and system availability.
* The metrics are loaded into a pecos PerformanceMonitoring 
  object and a series of quality control tests are run
* The results are printed to csv and html reports
"""
import pecos
import pandas as pd
import matplotlib.pyplot as plt
import os

# Initialize logger
pecos.logger.initialize()

# Create a Pecos PerformanceMonitoring data object
pm = pecos.monitoring.PerformanceMonitoring()

# Populate the object with a dataframe and translation dictionary
system_name = 'System1'
data_file = 'System1_2015_performance_metrics.xlsx'
df = pd.read_excel(data_file, index_col=0)
pm.add_dataframe(df)

# Check timestamp
pm.check_timestamp(24*3600) 
        
# Check missing
pm.check_missing()
        
# Check corrupt
pm.check_corrupt([-999]) 

# Check range for all columns
for key in pm.trans.keys():
    pm.check_range([0.5,1], key)

# Check increment for all columns
for key in pm.trans.keys():
    pm.check_increment([-0.5, None], key, absolute_value=False) 

# Define output file names and directories
results_directory = 'Results'
if not os.path.exists(results_directory):
    os.makedirs(results_directory)
graphics_file_rootname = os.path.join(results_directory, 'test_results')
custom_graphics_file = os.path.abspath(os.path.join(results_directory, 'custom.png'))
test_results_file = os.path.join(results_directory, system_name + '_test_results.csv')
report_file =  os.path.join(results_directory, system_name + '.html')

# Generate graphics
test_results_graphics = pecos.graphics.plot_test_results(graphics_file_rootname, pm)
plt.figure(figsize = (10.0,4.0))
ax = plt.gca()
df.plot(ax=ax, ylim=[-0.2,1.2])
plt.savefig(custom_graphics_file, format='png', dpi=500)

# Write test results and report files
pecos.io.write_test_results(test_results_file, pm.test_results)
pecos.io.write_monitoring_report(report_file, pm, test_results_graphics, [custom_graphics_file], 
                                 title='System1 2015 Performance Metrics')
