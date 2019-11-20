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
* Delta
* Increment
* Outlier

.. note:: 
   Quality control tests can also be called using individual functions, see :ref:`software_framework` for more details.
   
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

For example,

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import pecos
    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> index = pd.date_range('1/1/2016', periods=3, freq='s')
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

* Data column (default = all columns)

* Minimum number of consecutive failures for reporting (default = 1 timestamp)

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

* Data column (default = all columns)

* Minimum number of consecutive failures for reporting (default = 1 timestamp)

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

* Data column (default = all columns)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_range([None, 1], 'A')

checks for values greater than 1 in the columns associated with the key 'A'

Delta test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_delta` method is used to check for stagnant data and abrupt changes in data.
The test checks if the difference between the minimum and maximum data value within a moving window is within expected bounds.

Input includes:

* Upper and lower bound

* Data column (default = all columns)

* Size of the moving window used to compute the difference between the minimum and maximum (default = 3600 seconds)

* Flag indicating if the test should check for positive delta (the min occurs before the max) or negative delta (the max occurs before the min) (default = both)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

	>>> pm.check_delta([0.0001, None], window=3600)

checks if data changes by less than 0.0001 in a 1 hour window.

.. doctest::

	>>> pm.check_delta([None, 800], window=1800, direction='negative')

checks if data decrease by more than 800 in a 30 minute window.

Increment test
--------------------
Similar to the check_delta method above, the :class:`~pecos.monitoring.PerformanceMonitoring.check_increment`
method can be used to check for stagnant data and abrupt changes in data.
The test checks if the difference between
consecutive data values (or other specified increment) is within expected bounds.
While this method is faster than the check_delta method, it does not consider changes within a moving window, making its ability to 
find stagnant data and abrupt changes less robust.

Input includes:

* Upper and lower bound

* Data column (default = all columns)

* Increment used for difference calculation (default = 1 timestamp)

* Flag indicating if the absolute value of the increment is used in the test (default = True)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

	>>> pm.check_increment([0.0001, None], min_failures=60)
	
checks if value increments are less than 0.0001 for 60 consecutive time steps.

.. doctest::

	>>> pm.check_increment([-800, None], absolute_value=False)

checks if value increments decrease by more than -800 in a single time step.

Outlier test
--------------------
The :class:`~pecos.monitoring.PerformanceMonitoring.check_outlier` method is used to check if normalized data
falls outside expected bounds.  Data is normalized using the mean and standard deviation, using either a
moving window or using the entire data set.  If multiple columns of data are used, each column is normalized separately.
Input includes:

* Upper and lower bound (in standard deviations)

* Data column (default = all columns)

* Size of the moving window used to normalize the data (default = 3600 seconds)

* Flag indicating if the absolute value of the normalize data is used in the test (default = True)

* Minimum number of consecutive failures for reporting (default = 1)

For example,

.. doctest::

    >>> pm.check_outlier([None, 3], window=12*3600)

checks if the normalized data changes by more than 3 standard deviations within a 12 hour moving window.
