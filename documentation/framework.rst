Framework
======================================

Pecos contains the following modules

.. _table-subpackage:
   
   =======================================  =============================================================================================================================================================================================================================================================================
   Subpackage                               Description
   =======================================  =============================================================================================================================================================================================================================================================================
   :class:`~pecos.monitoring`	            Contains the PerformanceMonitoring class and individual quality control test functions that are used to run analysis
   :class:`~pecos.metrics`                  Contains metrics that describe the quality control analysis or compute quantities that might be of use in the analysis
   :class:`~pecos.io`		                Contains functions to read/send data and write results to files/html reports
   :class:`~pecos.graphics`	                Contains functions to generate scatter, time series, and heatmap plots for reports
   :class:`~pecos.utils`	                Contains contains helper functions, including functions to convert timeseries indices from seconds to datetime
   =======================================  =============================================================================================================================================================================================================================================================================
   
In addition to the modules listed above, Pecos also includes a :class:`~pecos.pv`
module that contains metrics specific to photovoltaic analysis.

Object-oriented analysis
-------------------------

Pecos includes a PerformanceMonitoring class which is the base class used to define
the analysis.  This class stores:

* Raw data
* Translation dictionary (maps raw data column names to common names)
* Time filter (excludes specific timestamps from analysis)

The class can be used to call quality control tests, including:

* Check timestamps for missing, duplicate, and non-monotonic indexes
* Check for missing data
* Check for corupt data
* Check for data outside expected range
* Check for stagnant of abrupt changes in the data
* Check for outliers

The class can be used to return:

* Cleaned data (data that failed a test is replaced by NaN)
* Boolean mask (indicates if data failed a test)
* Summary of the test results

Functional analysis
--------------------
The quality control tests can also be run using individual functions.
These functions generate a PerformanceMonitoring class under the hood and return:

* Cleaned data
* Boolean mask 
* Summary of the test results

Note, most of the examples in the documetnation use the Object-oriented approach.
The indvidual functions can be run using the methods direclty, for example:

>> cleaned_data, mask, summary = pecos.monitoring.check_timestamp(data)
