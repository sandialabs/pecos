"""
This example is similar to dashboard_example_1.py, but the dashboard contains a
color indicator for each system and location.  The color (red, yellow, green) 
is an indicator of the number of test failures.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import pecos

# Initialize logger
pecos.logger.initialize()

# Define system names, location names, and analysis date
nLocations = 3
nSystems = 5
locations = ['location' + str(i+1) for i in range(nLocations)]
systems = ['system' + str(i+1) for i in range(nSystems)]
analysis_date = datetime.date(2016, 7, 28)

dashboard_content = {} # Initialize the dashboard content dictionary
np.random.seed(500) # Set a random seed for sine wave function

for location_name in locations:
    for system_name in systems:
        
        # Create a Pecos PerformanceMonitoring data object
        pm = pecos.monitoring.PerformanceMonitoring()
        
        # Populate the object with a dataframe and translation dictionary
        # In this example, fake data is generated using a sin wave function
        index = pd.date_range(analysis_date, periods=48, freq='30Min')
        data=np.sin(0.5*np.arange(0,48,1)) + 3*np.random.rand()**3
        df = pd.DataFrame(data=data.transpose(), index=index, columns=['A'])
        pm.add_dataframe(df)

        # Check range
        pm.check_range([None,1]) 
        
        # Compute metrics
        QCI = pecos.metrics.qci(pm.mask)
        
        # Define output files and subdirectories
        results_directory = 'example_2'
        results_subdirectory = os.path.join(results_directory, location_name+'_'+system_name)
        if not os.path.exists(results_subdirectory):
            os.makedirs(results_subdirectory)
        graphics_file_rootname = os.path.join(results_subdirectory, 'test_results')
        colorblock_graphics_file = os.path.abspath(os.path.join(results_subdirectory, 'colorblock.png'))
        custom_graphics_file = os.path.abspath(os.path.join(results_subdirectory, 'custom.png'))
        test_results_file = os.path.join(results_subdirectory, 'test_results.csv')
        report_file =  os.path.join(results_subdirectory, 'monitoring_report.html')
        
        # Generate graphics
        test_results_graphics = pecos.graphics.plot_test_results(pm.data, pm.test_results,
                                       pm.tfilter, filename_root=graphics_file_rootname)
        pecos.graphics.plot_heatmap(QCI, vmin=0, vmax=1)
        plt.savefig(colorblock_graphics_file, dpi=90, bbox_inches='tight', pad_inches = 0)
        
        df.plot(figsize=(6.0,2.0))
        plt.savefig(custom_graphics_file, format='png', dpi=250)

        # Write test results and report files
        pecos.io.write_test_results(pm.test_results, test_results_file)
        pecos.io.write_monitoring_report(pm.data, pm.test_results, test_results_graphics, 
                                         [custom_graphics_file], QCI, filename=report_file)
        
        # Store content to be displayed in the dashboard
        content = {'graphics': [colorblock_graphics_file],
                   'link': {'Link to Report': os.path.abspath(report_file)}}
        dashboard_content[(location_name, system_name)] = content

# Create dashboard   
pecos.io.write_dashboard(systems, locations, dashboard_content, im_width=100,
                         filename='dashboard_example_2.html')
