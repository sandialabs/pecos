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
   :class:`~pecos.io`		                Contains functions to load data, send email alerts, write results to files, and generate HTML and LaTeX reports
   :class:`~pecos.graphics`	                Contains functions to generate scatter, time series, and heatmap plots for reports
   :class:`~pecos.utils`	                Contains helper functions, including functions to convert time series indices from seconds to datetime
   =======================================  =============================================================================================================================================
   
In addition to the modules listed above, Pecos also includes a :class:`~pecos.pv`
module that contains metrics specific to photovoltaic analysis.

Object-oriented and functional approach
-----------------------------------------
Pecos supports quality control tests that are called using both an object-oriented and functional approach.

Object-oriented approach
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Pecos includes a :class:`~pecos.monitoring.PerformanceMonitoring` class which is the base class used to define
the quality control analysis.  This class stores:

* Raw data
* Translation dictionary (maps raw data column names to common names)
* Time filter (excludes specific timestamps from analysis)

The class is used to call quality control tests, including:

* :class:`~pecos.monitoring.PerformanceMonitoring.check_timestamp`: Check timestamps for missing, duplicate, and non-monotonic indexes
* :class:`~pecos.monitoring.PerformanceMonitoring.check_missing`: Check for missing data
* :class:`~pecos.monitoring.PerformanceMonitoring.check_corrupt`: Check for corrupt data
* :class:`~pecos.monitoring.PerformanceMonitoring.check_range`: Check for data outside expected range
* :class:`~pecos.monitoring.PerformanceMonitoring.check_delta`: Check for stagnant of abrupt changes in the data
* :class:`~pecos.monitoring.PerformanceMonitoring.check_outlier`: Check for outliers
* :class:`~pecos.monitoring.PerformanceMonitoring.check_custom_static`: Custom static quality control test
* :class:`~pecos.monitoring.PerformanceMonitoring.check_custom_streaming`: Custom streaming quality control test

The class can return the following results:

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

.. _static_streaming:

Static and streaming analysis
------------------------------------
Pecos supports both static and streaming analysis. 

Static analysis
^^^^^^^^^^^^^^^^^^^^^^^
Most quality control tests in Pecos use static analysis.
Static analysis operates on the entire data set to determine if all data points are normal or anomalous. While this can include operations like moving window statistics, the quality control tests operates on the entire data set at once. 
This means that results from the quality control test are not dependent on results from a previous time step.
This approach is appropriate when data at different time steps can be analyzed independently, or moving window statistics used to analyze the data do not need to be updated based on test results.

The following quality control tests use static analysis:

* :class:`~pecos.monitoring.PerformanceMonitoring.check_missing`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_corrupt`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_range`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_delta`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_outlier` :superscript:`1`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_custom_static`

:superscript:`1` The outlier test can make use of both static and streaming analysis.  See :ref:`outlier` for more details.

Streaming analysis
^^^^^^^^^^^^^^^^^^^^^^^
The streaming analysis loops through each data point using a quality control tests that relies on information from "clean data" in a moving window.  If a data point is determined to be anomalous, it is not included in the window for subsequent analysis.
When using a streaming analysis, Pecos keeps track of the cleaned history that is used in the quality control test at each time step.
This approach is important to use when the underlying methods in the quality control test could be corrupted by historical data points that were deemed anomalous.  The streaming analysis also allows users to better analyze continuous datasets in a near real-time fashion. While Pecos could be used to analyze data at a single time step in a real-time fashion (creating a new instance of the PerformanceMonitoring class each time), the methods in Pecos are really designed to analyze data over a time period.  That time period can depend on several factors, including the size of the data and how often the test results and reports should be generated.  Cleaned history can be appended to new datasets as they come available to create a seamless analysis for continuous data. See :ref:`continuous` for more details. 

The streaming analysis includes an optional parameter which is used to **rebase data in the history window** if a certain fraction of that data has been deemed to be anomalous.  The ability to rebase the history is useful if data changes to a new normal condition that would otherwise continue to be flagged as anomalous. 

The following quality control tests use streaming analysis:

* :class:`~pecos.monitoring.PerformanceMonitoring.check_timestamp` :superscript:`2`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_outlier` :superscript:`3`
* :class:`~pecos.monitoring.PerformanceMonitoring.check_custom_streaming`

:superscript:`2` The timestamp test does not loop through data using a moving window, rather timestamp functionality in Pandas is used to determine anomalies in the time index. 

:superscript:`3` The outlier test can make use of both static and streaming analysis.  See :ref:`outlier` for more details.

Custom quality control tests
---------------------------------
Pecos supports custom quality control tests that can be static or streaming in form.  This feature allows the user to customize the analysis used to determine if data is anomalous and return custom metadata from the analysis.  

The custom function is defined outside of Pecos and handed to the custom quality control method as an input argument.  The allows the user to include analysis options that are not currently support in Pecos or are very specific to their application.

While there are no specifications on the information that metadata stores, the metadata commonly includes raw values that were used in the quality control test.  For example, while the outlier test returns a boolean value that indicates if data is normal or anomalous, the metadata can include the normalized data value that was used to make that determination.  See :ref:`custom` for more details.
