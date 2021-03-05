"""
In this example, data from a 6KW PV system is used to demonstrate integration
between pecos and pvlib.  
* Time series data is loaded from two text files in Campbell Scientific format
* The files contain electrical output from the pv system and associated 
  weather data. 
* Translation dictionaries are defined to map and group the raw data into 
  common names for analysis
* A time filter is established based on sun position
* Electrical and weather data are loaded into a pecos PerformanceMonitoring 
  object and a series of quality control tests are run
* A performance model is computed using pvlib, additional quality control tests
  are run to compare observed to predicted power output
* PV performance metrics are computed
* The results are written to an HTML report
"""
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import pvlib
import pv_model
import pecos

# Initialize logger
pecos.logger.initialize()

# Open config file and extract information
config_file = 'Baseline_config.yml'
fid = open(config_file, 'r')
config = yaml.load(fid)
fid.close()
location = config['Location']
sapm_parameters = config['SAPM Parameters']
MET_translation_dictionary = config['MET Translation'] # translation dictionary for weather file
BASE_translation_dictionary = config['Baseline6kW Translation'] # translation dictionary for pv file
composite_signals = config['Composite Signals']
corrupt_values = config['Corrupt Values']
range_bounds = config['Range Bounds']
increment_bounds = config['Increment Bounds']

# Create a Pecos PerformanceMonitoring data object
pm = pecos.monitoring.PerformanceMonitoring()

# Populate the object with pv and weather dataframes and translation dictionaries
database_file = 'Baseline6kW_2015_11_11.dat'
df = pecos.io.read_campbell_scientific(database_file)
df.index = df.index.tz_localize(location['Timezone'])
pm.add_dataframe(df)
pm.add_translation_dictionary(BASE_translation_dictionary)

database_file = 'MET_2015_11_11.dat'
df = pecos.io.read_campbell_scientific(database_file)
df.index = df.index.tz_localize(location['Timezone'])
pm.add_dataframe(df)
pm.add_translation_dictionary(MET_translation_dictionary)

# Check timestamp
pm.check_timestamp(60) 
    
# Generate a time filter based on sun position
solarposition = pvlib.solarposition.ephemeris(pm.data.index, location['Latitude'], 
                                              location['Longitude'])
time_filter = solarposition['apparent_elevation'] > 10 
pm.add_time_filter(time_filter)

# Check missing
pm.check_missing()

# Check corrupt
pm.check_corrupt(corrupt_values) 

# Add composite signals
for composite_signal in composite_signals:
    for key,value in composite_signal.items():
        signal = pecos.utils.evaluate_string(value, data=pm.data, 
                                             trans=pm.trans, col_name=key)
        pm.add_dataframe(signal)
        pm.add_translation_dictionary({key: list(signal.columns)})

# Check range
for key,value in range_bounds.items():
    value[0] = pecos.utils.evaluate_string(value[0], specs=sapm_parameters) 
    value[1] = pecos.utils.evaluate_string(value[1], specs=sapm_parameters)
    pm.check_range(value, key) 

# Check increment
for key,value in increment_bounds.items():
    pm.check_increment([value[0], value[1]], key, min_failures=value[2]) 
    
# Compute QCI
QCI = pecos.metrics.qci(pm.mask, pm.tfilter)

# Run the SAPM and compute metrics. Remove data points that failed a previous 
# quality control test before running the model (using pm.cleaned_data). Check range 
# on DC power relative error and normalized efficiency. Compute PV metrics.  
metrics = pv_model.sapm(pm, sapm_parameters, location)

# Add QCI to the metrics
metrics['QCI'] = QCI.mean()
metrics = pd.Series(metrics)

# Generate graphics
test_results_graphics = pecos.graphics.plot_test_results(pm.data, pm.test_results, pm.tfilter)
pm.data[pm.trans['DC Power']].plot(figsize=(7,3.5))
plt.savefig('custom1.png', format='png', dpi=500)
pm.data[['Diffuse_Wm2_Avg', 'Direct_Wm2_Avg', 'Global_Wm2_Avg']].plot(figsize=(7,3.5))
plt.savefig('custom2.png', format='png', dpi=500)

# Write test results and report files
pecos.io.write_test_results(pm.test_results)
pecos.io.write_monitoring_report(pm.data, pm.test_results, test_results_graphics, 
                                 ['custom1.png', 'custom2.png'], metrics)
