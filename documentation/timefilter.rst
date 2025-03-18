Time filter
=============

A time filter is an optional feature which allows the user to exclude 
specific timestamps from all quality control tests.  The time filter is 
a Boolean time series that can be defined using
elapsed time, clock time, or other custom algorithms. 

Pecos includes methods to get the elapsed and clock time of the DataFrame (in seconds).
The following example defines a time filter between 3 AM and 9 PM,

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import numpy as np
    >>> import pecos
    >>> pm = pecos.monitoring.PerformanceMonitoring()
    >>> index = pd.date_range('1/1/2017', periods=24, freq='h')
    >>> data = {'A': np.arange(24)}
    >>> df = pd.DataFrame(data, index=index)
    >>> pm.add_dataframe(df)
	
.. doctest::

    >>> clocktime = pecos.utils.datetime_to_clocktime(pm.data.index)
    >>> time_filter = pd.Series((clocktime > 3*3600) & (clocktime < 21*3600), 
    ...                         index=pm.data.index)

The time filter can also be defined based on properties of the DataFrame, for example,

.. doctest::

    >>> time_filter = pm.data['A'] > 0.5
	
For some applications, it is useful to define the time filter based on sun position, 
as demonstrated in **pv_example.py** in the 
`examples/pv <https://github.com/sandialabs/pecos/tree/main/examples/pv>`_ directory.

The time filter can then be added to the PerformanceMonitoring object as follows,

.. doctest::

    >>> pm.add_time_filter(time_filter)


