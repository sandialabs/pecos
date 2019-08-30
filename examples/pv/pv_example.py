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
* A performance model is computed using pvlib, additional quality control test
  is run to compare observed to predicted power output
* PV performance metrics are computed
* The results are printed to csv and html reports
"""
import datetime
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import pvlib
import pv_model
import pecos

# Initialize logger
pecos.logger.initialize()

# Define system name and analysis date
system_name = 'Baseline_System'
analysis_date = datetime.date(2015, 11, 11)

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
database_file = 'Baseline6kW' + analysis_date.strftime('_%Y_%m_%d') + '.dat'
df = pecos.io.read_campbell_scientific(database_file)
df.index = df.index.tz_localize(location['Timezone'])
pm.add_dataframe(df)
pm.add_translation_dictionary(BASE_translation_dictionary)

database_file = 'MET' + analysis_date.strftime('_%Y_%m_%d') + '.dat'
df = pecos.io.read_campbell_scientific(database_file)
df.index = df.index.tz_localize(location['Timezone'])
pm.add_dataframe(df)
pm.add_translation_dictionary(MET_translation_dictionary)

# Check timestamp
pm.check_timestamp(60) 
    
# Generate a time filter based on sun position
solarposition = pvlib.solarposition.ephemeris(pm.df.index, location['Latitude'], location['Longitude'])
time_filter = solarposition['apparent_elevation'] > 10 
pm.add_time_filter(time_filter)

# Check missing
pm.check_missing()

# Check corrupt
pm.check_corrupt(corrupt_values) 

# Add composite signals
for composite_signal in composite_signals:
    for key,value in composite_signal.items():
        signal = pm.evaluate_string(key, value)
        pm.add_dataframe(signal)
        pm.add_translation_dictionary({key: list(signal.columns)})

# Check range
for key,value in range_bounds.items():
    pm.check_range(value, key, sapm_parameters) 

# Check increment
for key,value in increment_bounds.items():
    pm.check_increment([value[0], value[1]], key, min_failures=value[2]) 
    
# Compute QCI only using columns defined in the translation dictionary
mask = pm.mask
col = [item for sublist in pm.trans.values() for item in sublist]
QCI = pecos.metrics.qci(mask[col], pm.tfilter)

# Generate a performance model using observed POA, wind speed, and air temp.
# Remove data points that failed a previous quality control test before running the model (using 'mask').
# Check range on DC power relative error and normlized efficiency.
# Compute PV metrics.  
poa = pm.df[pm.trans['POA']][mask[pm.trans['POA']]]
wind = pm.df[pm.trans['Wind Speed']][mask[pm.trans['Wind Speed']]]
temp = pm.df[pm.trans['Ambient Temperature']][mask[pm.trans['Ambient Temperature']]]
pv_metrics = pv_model.sapm(pm, poa, wind, temp, sapm_parameters, location)
metrics = pd.concat([QCI, pv_metrics], axis=1)

# Generate graphics
test_results_graphics = pecos.graphics.plot_test_results(pm.df, pm.test_results, pm.tfilter)
pm.df[pm.trans['DC Power']].plot(figsize=(7,3.5))
plt.savefig('custom1.png', format='png', dpi=500)
pm.df[['Diffuse_Wm2_Avg', 'Direct_Wm2_Avg', 'Global_Wm2_Avg']].plot(figsize=(7,3.5))
plt.savefig('custom2.png', format='png', dpi=500)

# Write metrics, test results, and report files
pecos.io.write_metrics(metrics)
pecos.io.write_test_results(pm.test_results)
pecos.io.write_monitoring_report(pm.df, pm.test_results, test_results_graphics, 
                                 ['custom1.png', 'custom2.png'], metrics.transpose(), 
                                 'Baseline System, Performance Monitoring Report', config)
