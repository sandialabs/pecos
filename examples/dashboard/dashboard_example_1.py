"""
In this example, a dashboard is generated to view quality control analysis 
results using analysis from several systems and locations.  Each system and 
location links to a detailed report which includes test failures.
For illustrative purposes, the data used in this example is generated within 
the script, using a sine wave function.
"""
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import pecos

# Initialize logger
pecos.logger.initialize()

# Define system names, location names, and analysis date
systems = ['system1', 'system2', 'system3']
locations = ['location1', 'location2']
analysis_date = datetime.date.today()-datetime.timedelta(days=1)

dashboard_content = {} # Initialize the dashboard content dictionary
np.random.seed(500) # Set a random seed for sine wave function

for location_name in locations:
    for system_name in systems:
        # Open config file and extract information
        config_file = system_name + '_config.yml'
        fid = open(config_file, 'r')
        config = yaml.safe_load(fid)
        fid.close()
        trans = config['Translation']
        specs = config['Specifications']
        range_bounds = config['Range Bounds']
    
        # Create a Pecos PerformanceMonitoring data object
        pm = pecos.monitoring.PerformanceMonitoring()
        
        # Populate the object with a dataframe and translation dictionary
        # In this example, fake data is generated using a sin wave function
        index = pd.date_range(analysis_date, periods=24, freq='h')
        data=np.sin(np.random.rand(3,1)*np.arange(0,24,1))
        df = pd.DataFrame(data=data.transpose(), index=index, columns=['A', 'B', 'C'])
        pm.add_dataframe(df)
        pm.add_translation_dictionary(trans)

        # Check timestamp
        pm.check_timestamp(specs['Frequency']) 
        
        # Generate a time filter
        clock_time = pecos.utils.datetime_to_clocktime(pm.data.index)
        time_filter = pd.Series((clock_time > specs['Time Filter Min']*3600) & \
                                (clock_time < specs['Time Filter Max']*3600),
                                index=pm.data.index)
        pm.add_time_filter(time_filter)
        
        # Check missing
        pm.check_missing()
        
        # Check range
        for key,value in range_bounds.items():
            pm.check_range(value, key) 
        
        # Compute metrics
        QCI = pecos.metrics.qci(pm.mask, pm.tfilter)
        
        # Define output files and subdirectories
        results_directory = 'example_1'
        results_subdirectory = os.path.join(results_directory, location_name+'_'+system_name)
        if not os.path.exists(results_subdirectory):
            os.makedirs(results_subdirectory)
        graphics_file_rootname = os.path.join(results_subdirectory, 'test_results')
        custom_graphics_file = os.path.abspath(os.path.join(results_subdirectory, 'custom.png'))
        test_results_file = os.path.join(results_subdirectory, 'test_results.csv')
        report_file =  os.path.join(results_subdirectory, 'monitoring_report.html')
        
        # Generate graphics
        test_results_graphics = pecos.graphics.plot_test_results(pm.data, 
                                        pm.test_results, filename_root=graphics_file_rootname)
        df.plot()
        plt.savefig(custom_graphics_file, format='png', dpi=500)

        # Write test results and report files
        pecos.io.write_test_results(pm.test_results, test_results_file)
        pecos.io.write_monitoring_report(pm.data, pm.test_results, test_results_graphics, 
                                         [custom_graphics_file], QCI, filename=report_file)
        
        # Store content to be displayed in the dashboard
        content = {'text': "Example text for " + location_name+'_'+system_name, 
                   'graphics': [custom_graphics_file], 
                   'table':  QCI.to_frame('QCI').transpose().to_html(), 
                   'link': {'Link to Report': os.path.abspath(report_file)}}
        dashboard_content[(system_name, location_name)] = content

# Create dashboard   
pecos.io.write_dashboard(locations, systems, dashboard_content, 
                         filename='dashboard_example_1.html')
