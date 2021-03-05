"""
In this example, performance metrics from a pv system are analyzed to determine 
long term system health
* Daily performance metrics for 2015 are loaded from a CSV file
* The files contain performance ratio and system availability.
* The metrics are loaded into a pecos PerformanceMonitoring 
  object and a series of quality control tests are run
* The results are printed to CSV and HTML reports
"""
import pandas as pd
import matplotlib.pyplot as plt
import pecos

# Initialize logger
pecos.logger.initialize()

# Create a Pecos PerformanceMonitoring data object
pm = pecos.monitoring.PerformanceMonitoring()

# Populate the object with a dataframe and translation dictionary
data_file = 'System1_2015_performance_metrics.csv'
df = pd.read_csv(data_file, index_col=0, parse_dates=True)
pm.add_dataframe(df)

# Check timestamp
pm.check_timestamp(24*3600) 
        
# Check missing
pm.check_missing()
        
# Check corrupt
pm.check_corrupt([-999]) 

# Check range for all columns
pm.check_range([0.5,1])

# Check to see if data decreases by more than -0.5 between consecutive days
pm.check_increment([-0.5, None], absolute_value=False)  

# Generate graphics
test_results_graphics = pecos.graphics.plot_test_results(pm.data, pm.test_results)
df.plot(ylim=[-0.2,1.2], figsize=(10.0,4.0))
plt.savefig('custom.png', format='png', dpi=500)

# Write test results and report files
pecos.io.write_test_results(pm.test_results)
pecos.io.write_monitoring_report(pm.data, pm.test_results, test_results_graphics, 
                                 ['custom.png'], title='System1 2015')
