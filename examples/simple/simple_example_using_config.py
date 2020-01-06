"""
This example is the same as simple_example.py, but it uses a configuration 
file to define the quality control analysis input.
"""
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import pecos

# Initialize logger
pecos.logger.initialize()

# Open configuration file
config_file = 'simple_config.yml'
fid = open(config_file, 'r')
config = yaml.load(fid)
fid.close()
   
# Create a Pecos PerformanceMonitoring data object
pm = pecos.monitoring.PerformanceMonitoring()

# Populate the object with a DataFrame and translation dictionary
data_file = 'simple.xlsx'
df = pd.read_excel(data_file, index_col=0)
pm.add_dataframe(df)
pm.add_translation_dictionary(config['Translation'])

# Check the expected frequency of the timestamp
pm.check_timestamp(config['Specifications']['Frequency'])
 
# Generate a time filter to exclude data points early and late in the day
time_filter = pecos.utils.evaluate_string(config['Time Filter'], df)
pm.add_time_filter(time_filter)

# Check for missing data
pm.check_missing()
        
# Check for corrupt data values
pm.check_corrupt(config['Corrupt']) 

# Add a composite signal which compares measurements to a model
specs = config['Specifications']
for composite_signal in config['Composite Signals']:
    for key, value in composite_signal.items():
        signal = pecos.utils.evaluate_string(value, pm.df, pm.trans, specs, key)
        pm.add_dataframe(signal)
        pm.add_translation_dictionary({key: list(signal.columns)})

# Check data for expected ranges
for key,value in config['Range'].items():
    pm.check_range(value, key)

# Check for stagnant data within a 1 hour moving window
for key,value in config['Delta'].items():
    pm.check_delta(value, key, 3600) 

# Check for abrupt changes between consecutive time steps
for key,value in config['Increment'].items():
    pm.check_increment(value, key) 
    
# Compute the quality control index for A, B, C, and D
mask = pm.mask[['A','B','C','D']]
QCI = pecos.metrics.qci(mask, pm.tfilter)

# Generate graphics
test_results_graphics = pecos.graphics.plot_test_results(pm.df, pm.test_results)
df.plot(ylim=[-1.5,1.5], figsize=(7.0,3.5))
plt.savefig('custom.png', format='png', dpi=500)

# Write test results and report files
pecos.io.write_test_results(pm.test_results)
pecos.io.write_monitoring_report(pm.df, pm.test_results, test_results_graphics, 
                                 ['custom.png'], QCI)
