Automation
=============

Task scheduler 
------------------

To run Pecos on an automated schedule, create a task using your operating systems.  
On Windows, open the Control Panel and search for *Schedule Tasks*.
On Linux and OSX, use the *cron* utility.  

Tasks are defined by a trigger and an action.  
The trigger indicates when the task should be run (i.e. Daily at 1:00 pm).
The action can be set to run a batch file.
A batch file (.bat or .cmd filename extension) can be easily 
written to start a Python script which runs Pecos.  
For example, the following batch file runs driver.py::

	cd your_working_directory
	C:\Users\username\Anaconda3\python.exe driver.py

.. _continuous:

Continuous analysis
------------------------

The following example illustrates a framework that analyzes continuous streaming data and provides reports.  
For continuous data streams, it is often advantageous to provide quality control analysis and reports at a regular interval.  While the analysis and reporting can occur every time new data is available, it is often more informative and more efficient to run analysis and create reports that cover a longer time interval.  For example, data might be collected every minute and quality control analysis might be run every day. 

The following example pulls data from an SQL database that includes a table of raw data (data), table of data that has completed quality control analysis (qc_data), and a table that stores a summary of quality control test failures (qc_summary).  
After the analysis, quality control results are appended to the database. This process could also include metrics that describe the quality control results.  
The following code could be used as a Python driver that runs using a task scheduler every day, pulling in yesterday's data.  In this example, 1 hour of cleaned data is used to initialize the moving window and a streaming outlier test is run.

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> from sqlalchemy import create_engine
    >>> from sqlalchemy.types import DateTime, Date, Time, Float
    >>> import datetime
    >>> import numpy as np
    >>> import os
    
    >>> try: os.remove('monitor.db')
    ... except: pass
    
    >>> engine = create_engine('sqlite:///monitor.db', echo=False)
    >>> date = datetime.date.today()-datetime.timedelta(days=1)
    >>> N = 24*60
    >>> index = pd.date_range(date, periods=N, freq='Min')
    >>> df1 = {'A': np.random.normal(size=N),'B': np.random.normal(size=N)}
    >>> df1 = pd.DataFrame(df1, index=index)
    >>> df1.index.name = 'timestamp'
    >>> df1.to_sql('data', engine, dtype={'timestamp': DateTime(), 'A': Float(), 'B': Float()})
    
    >>> index = pd.date_range(date-datetime.timedelta(days=1), periods=N, freq='Min')
    >>> df2 = {'A': np.random.normal(size=N),'B': np.random.normal(size=N)}
    >>> df2 = pd.DataFrame(df2, index=index)
    >>> df2.index.name = 'timestamp'
    >>> df2.to_sql('qc_data', engine, dtype={'timestamp': DateTime(), 'A': Float(), 'B': Float()})
    
    >>> #data1 = engine.execute("SELECT * FROM data").fetchall()
    >>> #history1 = engine.execute("SELECT * FROM qc_data").fetchall()

.. doctest::

    >>> import pandas as pd
    >>> from sqlalchemy import create_engine
    >>> import datetime
    >>> import pecos
	
    >>> # Create the SQLite engine
    >>> engine = create_engine('sqlite:///monitor.db', echo=False)

    >>> # Define the date to extract yesterday's data
    >>> date = datetime.date.today()-datetime.timedelta(days=1)
	
    >>> # Load data and recent history from the database
    >>> data = pd.read_sql("SELECT * FROM data WHERE timestamp BETWEEN '" + str(date) + \
    ...                    " 00:00:00' AND '" + str(date) + " 23:59:59';" , engine, 
    ...                    parse_dates='timestamp', index_col='timestamp')

    >>> history = pd.read_sql("SELECT * FROM qc_data WHERE timestamp BETWEEN '" + \
    ...                       str(date-datetime.timedelta(days=1)) + " 23:00:00' AND '" + \
    ...                       str(date-datetime.timedelta(days=1)) + " 23:59:59';" , engine, 
    ...                       parse_dates='timestamp', index_col='timestamp')
	
    >>> # Setup the PerformanceMonitoring with data and history and run a streaming outlier test
    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> pm.add_dataframe(data)
    >>> pm.add_dataframe(history)
    >>> pm.check_outlier([-3, 3], window=3600, streaming=True)
		
    >>> # Save the cleaned data and test results to the database
    >>> pm.cleaned_data.to_sql('qc_data', engine, if_exists='append')
    >>> pm.test_results.to_sql('qc_summary', engine, if_exists='append')
	
    >>> # Create a monitoring report with test results and graphics
    >>> test_results_graphics = pecos.graphics.plot_test_results(data, pm.test_results)
    >>> filename = pecos.io.write_monitoring_report(pm.data, pm.test_results, test_results_graphics,
    ...             filename='monitoring_report_'+str(date)+'.html')

Configuration file
------------------------

A configuration file can be used to store information about the system, data, and  
quality control tests.  **The configuration file is not used directly within Pecos,
therefore there are no specific formatting requirements.**
Configuration files can be useful when using the same Python script 
to analyze several systems that have slightly different input requirements.

The `examples/simple <https://github.com/sandialabs/pecos/tree/master/examples/simple>`_ directory includes a configuration file, **simple_config.yml**, that defines 
system specifications, 
translation dictionary,
composite signals,
corrupt values,
and bounds for range and increment tests.
The script, **simple_example_using_config.py** uses this
configuration file to run the simple example.

.. literalinclude:: ../examples/simple/simple_config.yml

For some use cases, it is convenient to use strings of Python code in 
a configuration file to define time filters, 
quality control bounds, and composite signals.
These strings can be evaluated using :class:`~pecos.utils.evaluate_string`.
**WARNING this function calls** 
``eval`` 
**. Strings of Python code should be thoroughly tested by the user.**

For each {keyword} in the string, {keyword} is expanded in the following order:
    
* If keyword is ELAPSED_TIME, CLOCK_TIME or EPOCH_TIME then data.index is 
  converted to seconds (elapsed time, clock time, or epoch time) is used in the evaluation
* If keyword is used to select a column (or columns) of data, then data[keyword] 
  is used in the evaluation
* If a translation dictionary is used to select a column (or columns) of data, then 
  data[trans[keyword]] is used in the evaluation
* If the keyword is a key in a dictionary of constants (specs), then 
  specs[keyword] is used in the evaluation
      
For example, the time filter string is evaluated below.

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import numpy as np
    >>> import pecos
    >>> index = pd.date_range('1/1/2015', periods=96, freq='15Min')
    >>> data = {'A': np.random.rand(96), 'B': np.random.rand(96)}
    >>> df = pd.DataFrame(data, index=index)
    
.. doctest::

    >>> string_to_eval = "({CLOCK_TIME} > 3*3600) & ({CLOCK_TIME} < 21*3600)"
    >>> time_filter = pecos.utils.evaluate_string(string_to_eval, df)

.. _devicetoclient_config:

Data acquisition
--------------------

Pecos includes basic data acquisition methods to transfer data from sensors to an SQL database.  
These methods require the Python packages 
sqlalchemy (https://www.sqlalchemy.org/) and 
minimalmodbus (https://minimalmodbus.readthedocs.io). 

The :class:`~pecos.io.device_to_client` method collects data from a modbus device and stores it in a local 
MySQL database. 
The method requires several configuration options, which are stored as a nested dictionary.
pyyaml can be used to store configuration options in a file.
The options are stored in a **Client** block and a **Devices** block.  
The Devices block can define multiple devices and each device can have multiple data streams.
The configuration options are described below.

* **Client**: A dictionary that contains information about the client.  
  The dictionary has the following keys:

  * **IP**: IP address (string) 
  * **Database**: name of database (string) 
  * **Table**: name of table (string)
  * **Username**: name of user (string)
  * **Password**: password for user (string)
  * **Interval**: data collection frequency in seconds (integer)
  * **Retries**: number of retries for each channel (integer)

* **Devices**: A list of dictionaries that contain information about each device (one dictionary per device).  
  Each dictionary has the following keys:

  * **Name**: modbus device name (string)
  * **USB**: serial connection (string) e.g. /dev/ttyUSB0 for linux
  * **Address**: modbus slave address (string)       
  * **Baud**: data transfer rate in bits per second (integer)
  * **Parity**: parity of transmitted data for error checking (string). Possible values: N, E, O
  * **Bytes**: number of data bits (integer)
  * **Stopbits**: number of stop bits (integer)
  * **Timeout**: read timeout value in seconds (integer)  
  * **Data**: A list of dictionaries that contain information about each data stream (one dictionary per data stream). 
    Each dictionary has the following keys:
  
    * **Name**: data name (string)
    * **Type**: data type (string)
    * **Scale**: scaling factor (integer)
    * **Conversion**: conversion factor (float)
    * **Channel**: register number (integer)
    * **Signed**: define data as unsigned or signed (bool)
    * **Fcode**: modbus function code (integer). Possible values: 3,4

Example configuration options are shown below.

.. literalinclude:: ../pecos/templates/device_to_client.yml
