.. _quality_control:

Quality control tests
======================

Pecos includes several built in quality control tests.
When a test fails, information is stored in a summary table.  This
information can be saved to a file, database, or included in reports.
Quality controls tests fall into eight categories:

* Timestamp
* Missing data
* Corrupt data
* Range
* Delta
* Increment
* Outlier
* Custom

.. note:: 
   Quality control tests can also be called using individual functions, see :ref:`software_framework` for more details.
   
Timestamp test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_timestamp` method is used to check the time index for missing,
duplicate, and non-monotonic indexes.  If a duplicate timestamp is found, Pecos keeps the first occurrence.
If timestamps are not monotonic, the timestamps are reordered.
For this reason, the timestamp should be corrected before other quality control
tests are run.
**The timestamp test is the only test that modifies the data stored in pm.data.**
Input includes:

* Expected frequency of the time series in seconds

* Expected start time (default = None, which uses the first index of the time series)

* Expected end time (default = None, which uses the last index of the time series)

* Minimum number of consecutive failures for reporting (default = 1)

* A flag indicating if exact timestamps are expected.  When set to False, irregular timestamps can be used in the Pecos analysis (default = True).

For example,

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import pecos
    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> index = pd.date_range('1/1/2016', periods=3, freq='60s')
    >>> data = [[1,2,3],[4,5,6],[7,8,9]]
    >>> df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    >>> pm.add_dataframe(df)

.. doctest::

    >>> pm.check_timestamp(60)

checks for missing, duplicate, and non-monotonic indexes assuming an expected
frequency of 60 seconds.

Missing data test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_missing` method is used to check for missing values.
Unlike missing timestamps, missing data only impacts a subset of data columns.
NaN is included as missing.
Input includes:

* Data column (default = None, which indicates that all columns are used)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_missing('A', min_failures=5)

checks for missing data in the columns associated with the column or group 'A'.  In this example, warnings
are only reported if there are 5 consecutive failures.

Corrupt data test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_corrupt` method is used to check for corrupt values.
Input includes:

* List of corrupt values

* Data column (default = None, which indicates that all columns are used)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_corrupt([-999, 999])

checks for data with values -999 or 999 in the entire dataset.

Range test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_range` method is used to check if data is within expected bounds.
Range tests are very flexible.  The test can be used to check for expected range on the raw data or using modified data.
For example, composite signals can be add to the analysis to check for expected range on modeled
vs. measured values (i.e. absolute error or relative error) or an expected
relationships between data columns (i.e. column A divided by column B).
An upper bound, lower bound, or both can be specified.
Input includes:

* Upper and lower bound

* Data column (default = None, which indicates that all columns are used)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_range([None, 1], 'A')

checks for values greater than 1 in the columns associated with the key 'A'.

Delta test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_delta` method is used to check for stagnant data and abrupt changes in data.
The test checks if the difference between the minimum and maximum data value within a moving window is within expected bounds.

Input includes:

* Upper and lower bound

* Size of the moving window used to compute the difference between the minimum and maximum

* Data column (default = None, which indicates that all columns are used)

* Flag indicating if the test should only check for positive delta (the min occurs before the max) or negative delta (the max occurs before the min) (default = False)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

	>>> pm.check_delta([0.0001, None], window=3600)

checks if data changes by less than 0.0001 in a 1 hour moving window.

.. doctest::

	>>> pm.check_delta([None, 800], window=1800, direction='negative')

checks if data decrease by more than 800 in a 30 minute moving window.

Increment test
--------------------
Similar to the check_delta method above, the :class:`~pecos.monitoring.PerformanceMonitoring.check_increment`
method can be used to check for stagnant data and abrupt changes in data.
The test checks if the difference between
consecutive data values (or other specified increment) is within expected bounds.
While this method is faster than the check_delta method, it does not consider 
the timestamp index or
changes within a moving window, making its ability to 
find stagnant data and abrupt changes less robust.

Input includes:

* Upper and lower bound

* Data column (default = None, which indicates that all columns are used)

* Increment used for difference calculation (default = 1 timestamp)

* Flag indicating if the absolute value of the increment is used in the test (default = True)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

	>>> pm.check_increment([0.0001, None], min_failures=60)
	
checks if increments are less than 0.0001 for 60 consecutive time steps.

.. doctest::

	>>> pm.check_increment([-800, None], absolute_value=False)

checks if increments decrease by more than 800 in a single time step.

.. _outlier:

Outlier test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_outlier` method is used to check if normalized data
falls outside expected bounds.  Data is normalized using the mean and standard deviation, using either a
moving window or using the entire data set.  If multiple columns of data are used, each column is normalized separately.
Input includes:

* Upper and lower bound (in standard deviations)

* Data column (default = None, which indicates that all columns are used)

* Size of the moving window used to normalize the data (default = None). Note that when the window is set to None, the mean and standard deviation of the entire data set is used to normalize the data.

* Flag indicating if the absolute value of the normalize data is used in the test (default = True)

* Minimum number of consecutive failures for reporting (default = 1)

* Flag indicating if the outlier test should use streaming analysis (default=False). 

Note that using a streaming analysis is different than merely defining a moving window. 
Streaming analysis omits anomalous values from subsequent normalization calculations, where as a static analysis with a moving window does not.

In a static analysis, the mean and standard deviation used to normalize the data are computed 
using a moving window (or using the entire data set if window=None) and upper and lower 
bounds are used to determine if data points are anomalous.  The results do not impact the 
moving window statistics. In a streaming analysis, the mean and standard deviation are 
computed using a moving window after each data points is determined to be normal or anomalous.  
Data points that are determined to be anomalous are not used in the normalization.

For example,

.. doctest::

    >>> pm.check_outlier([None, 3], window=12*3600)

checks if the normalized data changes by more than 3 standard deviations within a 12 hour moving window.

.. _custom:

Custom tests
--------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_custom_static` and :class:`~pecos.monitoring.PerformanceMonitoring.check_custom_streaming` methods
allow the user to supply a custom function that is used to determine if data is normal or anomalous. 
See :ref:`static_streaming` for more details.

This feature allows the user to customize the analysis and return custom metadata from the analysis.  
The custom function is defined outside of Pecos and handed to the custom quality control method as an input argument.  The allows the user to include analysis options that are not currently support in Pecos or are very specific to their application.
While there are no specifications on what this metadata stores, the metadata commonly includes the raw values that were included in a quality control test.  For example, while the outlier test returns a boolean value that indicates if data is normal or anomalous, the metadata can include the normalized data value that was used to make that determination.

The user can also create custom quality control tests by creating a class that inherits from the PerformanceMonitoring class.

Custom static analysis
^^^^^^^^^^^^^^^^^^^^^^^^

Static analysis operates on the entire data set to determine if all data points are normal or anomalous. Input for custom static analysis includes:

* Custom quality control function with the following general form::

      def custom_static_function(data): 
          """
          Parameters
          ----------
          data : pandas DataFrame
              Data to be analyzed.
		  
          Returns
          --------
          mask : pandas DataFrame
              Mask contains boolean values and is the same size as data.
              True = data passed the quality control test, 
              False = data failed the quality control test.
			  
          metadata : pandas DataFrame
              Metadata stores additional information about the test and is returned by 
              ''check_custom_static''.  Metadata is generally the same size as data.  
          """
		  
          # User defined custom algorithm
          ... 		
		  
          return mask, metadata      
	
* Data column (default = None, which indicates that all columns are used)
* Minimum number of consecutive failures for reporting (default = 1)
* Error message (default = None)

Custom static analysis can be run using the following example.  
The custom function below, ``sine_function``, determines if sin(data) is greater than 0.5 and returns the value of sin(data) as metadata.

.. doctest::

    >>> import numpy as np
	
    >>> def sine_function(data):
    ...     # Create metadata and mask using sin(data)
    ...     metadata = np.sin(data)
    ...     mask = metadata > 0.5
    ...     return mask, metadata

    >>> metadata = pm.check_custom_static(sine_function)

	
Custom streaming analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The streaming analysis loops through each data point using a quality control tests that relies on information from "clean data" in a moving window. Input for custom streaming analysis includes:
	
* Custom quality control function with the following general form::

      def custom_streaming_function(data_pt, history): 
          """
          Parameters
          ----------
          data_pt : pandas Series
              The current data point to be analyzed.
		  
          history : pandas DataFrame
              Historical data used in the analysis. The streaming analysis omits 
              data points that were previously flagged as anomalous in the history.
			  
          Returns
          --------
          mask : pandas Series
              Mask contains boolean values (one value for each row in data_pt).
              True = data passed the quality control test, 
              False = data failed the quality control test.
			  
          metadata : pandas Series
              Metadata stores additional information about the test for the current data point.
              Metadata generally contains one value for row in data_pt. Metadata is 
              collected into a pandas DataFrame with one row per time index that was included
              in the quality control test (omits the history window) and is returned 
              by ''check_custom_streaming''.
          """
		  
          # User defined custom algorithm
          ... 		
		  
          return mask, metadata  

* Size of the moving window used to define the cleaned history.
* Indicator used to rebase the history window. If the user defined fraction of the history window has been deemed anomalous, then the history is reset using raw data.  The ability to rebase the history is useful if data changes to a new normal condition that would otherwise continue to be flagged as anomalous. (default = None, which indicates that rebase is not used)
* Data column (default = None, which indicates that all columns are used)
* Error message (default = None)

Custom streaming analysis can be run using the following example.  
The custom function below, ``nearest_neighbor``, determines if the current data point is within 3 standard 
deviations of data in a 10 minute history window.  
In this case, metadata returns the distance from each column in the current data point to its nearest neighbor in the history.
This is similar to the multivariate nearest neighbor algorithm used in CANARY [HMKC07]_.

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import pecos
    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> index = pd.date_range('1/1/2016', periods=100, freq='60s')
    >>> data = np.random.normal(size=(100,3))
    >>> df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    >>> pm.add_dataframe(df)
	
.. doctest::

    >>> import numpy as np
    >>> import pandas as pd
    >>> from scipy.spatial.distance import cdist 
	
    >>> def nearest_neighbor(data_pt, history):
    ...     # Normalize the current data point and history using the history window
    ...     zt = (data_pt - history.mean())/history.std()
    ...     z = (history - history.mean())/history.std()
    ...     # Compute the distance from the current data point to data in the history window
    ...     zt_reshape = zt.to_frame().T
    ...     dist = cdist(zt_reshape, z)
    ...     # Extract the minimum distance
    ...     min_dist = np.nanmin(dist)
    ...     # Extract the index for the min distance and the distance components
    ...     idx = np.nanargmin(dist)
    ...     metadata = z.loc[idx,:] - zt
    ...     # Determine if the min distance is less than 3, assign value (T/F) to the mask
    ...     mask = pd.Series(min_dist <= 3, index=data_pt.index)
    ...     return mask, metadata
	
    >>> metadata = pm.check_custom_streaming(nearest_neighbor, window=600) 

