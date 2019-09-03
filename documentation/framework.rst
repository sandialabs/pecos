.. _software_framework:

Framework
======================================

Pecos contains the following modules

.. _table-modules:
   
   =======================================  =============================================================================================================================================
   Module                                   Description
   =======================================  =============================================================================================================================================
   :class:`~pecos.monitoring`	            Contains the PerformanceMonitoring class and individual quality control test functions that are used to run analysis
   :class:`~pecos.metrics`                  Contains metrics that describe the quality control analysis or compute quantities that might be of use in the analysis
   :class:`~pecos.io`		                Contains functions to load data, send email alerts, write results to files, and generate html reports
   :class:`~pecos.graphics`	                Contains functions to generate scatter, time series, and heatmap plots for reports
   :class:`~pecos.utils`	                Contains helper functions, including functions to convert timeseries indices from seconds to datetime
   =======================================  =============================================================================================================================================
   
In addition to the modules listed above, Pecos also includes a :class:`~pecos.pv`
module that contains metrics specific to photovoltaic analysis.

Object-oriented approach
-------------------------

Pecos includes a :class:`~pecos.monitoring.PerformanceMonitoring` class which is the base class used to define
the quality control analysis.  This class stores:

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
* Summary of the quality control test results

The object-oriented approach is convenient when running a series of 
quality control tests and can make use of the 
translation dictionary and time filter across all tests.  
The cleaned data, boolean mask, and 
test results summary reflect results from all quality control tests.

When using the object-oriented approach, a PerformanceMonitoring object is created and methods are
called using that object. The cleaned data, mask, and tests results can then be extracted
from the PerformanceMonitoring object.
These properties are updated each time a quality control test is run.

.. doctest::
    :hide:

    >>> import pecos
    >>> import pandas as pd
    >>> index = pd.date_range('1/1/2016', periods=3, freq='s')
    >>> data = [[1,2,3],[4,5,6],[7,8,9]]
    >>> data = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    
.. doctest::

    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> pm.add_dataframe(data)
    >>> pm.check_range([-3,3])
    
.. doctest::

    >>> cleaned_data = pm.cleaned_data
    >>> mask = pm.mask
    >>> test_results = pm.test_results

Functional approach
--------------------
The same quality control tests can also be run using individual functions.
These functions generate a PerformanceMonitoring object under the hood and return:

* Cleaned data
* Boolean mask 
* Summary of the quality control test results

The functional approach is a convenient way to quickly get results from a 
single quality control tests.

When using the functional approach, data is passed to the quality control test function. 
All other augments  match the object-oriented approach.
The cleaned data, mask, and tests results can then be extracted
from a resulting dictionary.

.. doctest::

    >>> results = pecos.monitoring.check_range(data, [-3,3])
    
.. doctest::

    >>> cleaned_data = results['cleaned_data']
    >>> mask = results['mask']
    >>> test_results = results['test_results']
 
Note, examples in the documentation use the object-oriented approach.