Quality control tests
======================

Pecos includes several built in quality control tests.
When a test fails, information is stored in a summary table.  This
information can be saved to a file, database, or included in reports.
Quality controls tests fall into seven categories:

* Timestamp
* Missing data
* Corrupt data
* Range
* Increment
* Delta
* Outlier

Timestamp test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_timestamp` method is used to check the time index for missing, 
duplicate, and non-monotonic indexes.  If a duplicate timestamp is found, Pecos keeps the first occurrence.  
If timestamps are not monotonic, the timestamps are reordered.
For this reason, the timestamp should be corrected before other quality control 
tests are run.
**The timestamp test is the only test that modifies the data stored in pm.df.** 
Input includes:

* Expected frequency of the time series in seconds

* Expected start time (default = first index of the time series)

* Expected end time (default = last index of the time series)

* Minimum number of consecutive failures for reporting (default = 1 timestamp)

* A flag indicating if exact timestamps are expected.  When set to False, irregular timestamps can be used in the Pecos analysis.

For example, using Pecos' PerformanceMonitoring object:

.. doctest::

    >>> import pandas as pd
    >>> import pecos
    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> index = pd.date_range('1/1/2016', periods=3, freq='s')
    >>> data = [[1,2,3],[4,5,6],[7,8,9]]
    >>> df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])
    >>> pm.add_dataframe(df)

    >>> pm.check_timestamp(60)

Or using solely Pecos' functions:

.. doctest::

	>>> pm.monitoring.check_timestamp_func(df, 60)

checks for missing, duplicate, and non-monotonic indexes assuming an expected 
frequency of 60 seconds.
	
Missing data test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_missing` method is used to check for missing values.  
Unlike missing timestamps, missing data only impacts a subset of data columns.
NaN is included as missing.
Input includes:

* Data column (default = all columns)

* Minimum number of consecutive failures for reporting (default = 1 timestamp)

For example,

.. doctest::

    >>> pm.check_missing('A', min_failures=5)
	
.. doctest::

	>>> pm.monitoring.check_missing_func(df['A'], min_failures=5)

checks for missing data in the columns associated with the column or group 'A'.  In this example, warnings 
are only reported if there are 5 consecutive failures.

Corrupt data test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_corrupt` method is used to check for corrupt values. 
Input includes:

* List of corrupt values

* Data column (default = all columns)

* Minimum number of consecutive failures for reporting (default = 1 timestamp)

For example,

.. doctest::

    >>> pm.check_corrupt([-999, 999])
	
.. doctest::

	>>> pm.check_corrupt_func(df, [-999, 999])

checks for data with values -999 or 999 in the entire DataFrame.

Range test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_range` method is used to check if data is within expected bounds.
Range tests are very flexible.  The test can be used to check for expected range on the raw data or using modified data.  
For example, composite signals can be add to the DataFrame to check for expected range on modeled
vs. measured values (i.e. absolute error or relative error) or an expected
relationships between data columns (i.e. column A divided by column B). 
An upper bound, lower bound or both can be specified.  
Additionally, the data can be smoothed using a rolling mean before the test is run.
Input includes:

* Upper and lower bound

* Data column (default = all columns)

* Rolling window used to smooth the data before test is run (default = 0)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_range([None, 1], 'A', rolling_mean=2)
	
.. doctest::

	>>> pm.monitoring.check_range_func(df['A'], [None, 1], rolling_mean=2)

checks for values greater than 1 in the columns associated with the key 'A', 
using a rolling average of 2 time steps.

Outlier test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_outlier` method is used to check if normalized data 
falls outside expected bounds.  Data is normalized using the mean and standard deviation, using either a 
moving window or using the entire data set.  If multiple columns of data are used, each column is normalized separately.
Like the check_range method, the user can specify if the data
should be smoothed using a rolling mean before the test is run.  
Input includes:

* Upper and lower bound (in standard deviations)

* Data column (default = all columns)

* Size of the moving window used to normalize the data (default = 3600 seconds)

* Flag indicating if the absolute value is taken (default = True)

* Rolling window used to smooth the data before test is run (default = 0)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_outlier([None, 3], window=12*3600)
	
.. doctest::

	>>> pm.monitoring.check_outlier_func(df, [None, 3], window=12*3600)

checks if the normalized data changes by more than 3 standard deviations within a 12 hour moving window.

Delta test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_delta` method is used to check for stagnant data and abrupt changes in data.
The test checks if the difference between the minimum and maximum data value within a moving window is within expected bounds.
**Currently, this method is not efficient for large data sets (> 100000 pts).** 
Like the check_range method, the user can specify if the data
should be smoothed using a rolling mean before the test is run.  
Input includes:

* Upper and lower bound

* Data column (default = all columns)

* Size of the moving window used to compute the difference between the minimum and maximum (default = 3600 seconds)

* Flag indicating if the absolute value is taken (default = True)

* Rolling window used to smooth the data before test is run (default = 0)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

	>>> pm.check_delta([None, 0.000001], window=3600)
	
	>>> pm.monitoring.check_delta_func(df, [None, 0.000001], window=3600)

checks if data changes by more than 0.000001 in 1 hour.

.. doctest::

	>>> pm.check_delta([-800, None], window=1800, absolute_value=False)
	
	>>> pm.monitoring.check_delta_func(df, [-800, None], window=1800, absolute_value=False)

checks if data decrease by more than -800 in 30 minutes.

Increment test
--------------------
Similar to the check_delta method above, the :class:`~pecos.monitoring.PerformanceMonitoring.check_increment` 
method can be used to check for stagnant data and abrupt changes in data.  
The test checks if the difference between 
consecutive data values (or other specified increment) is within expected bounds.
This method does not use timestamp indices to find the min and max value within a moving window, 
therefore it is less robust than the check_delta method.
Like the check_range method, the user can specify if the data
should be smoothed using a rolling mean before the test is run.  
Input includes:

* Upper and lower bound

* Data column (default = all columns)

* Increment used for difference calculation (default = 1 timestamp)

* Flag indicating if the absolute value is taken (default = True)

* Rolling window used to smooth the data before test is run (default = 0)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

	>>> pm.check_increment([None, 0.000001], min_failures=60)
	
	>>> pm.monitoring.check_increment_func(df, [None, 0.000001], min_failures=60)

checks if value increments are greater than 0.000001 for 60 consecutive time steps.

.. doctest::

	>>> pm.check_increment([-800, None], absolute_value=False)
	
	>>> pm.monitoring.check_increment_func(df, [-800, None], absolute_value=False)

checks if value increments decrease by more than -800 in a single time step.
