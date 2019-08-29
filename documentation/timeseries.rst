Time series data
==================

Pandas DataFrames store 2D data with labeled columns.  Pecos uses Pandas DataFrames
to store and analyze data indexed by time.  Pandas includes a wide range of 
time series analysis and date-time functionality.  By using Pandas DataFrames, 
Pecos is able to take advantage of a wide range of timestamp strings, including
UTC offset. 

Pandas includes many built-in functions to read data from CSV, Excel, SQL, etc.
For example, data can be loaded from an excel file using the following code.

.. doctest::

    >>> import pandas as pd
    >>> df = pd.read_excel('data.xlsx') #doctest:+SKIP 

Data can also be gathered from the web using the Python package request, http://docs.python-requests.org.

The :class:`~pecos.monitoring.PerformanceMonitoring` class in Pecos is
the base class used to define the quality control analysis. Pecos functions 
are also individually wrapped and can be accessed as such. To get started 
using classes, create an instance of the PerformanceMonitoring class.

.. doctest::

    >>> import pecos
    >>> pm = pecos.monitoring.PerformanceMonitoring()

A DataFrame can then be added to the PerformanceMonitoring object.

.. doctest::
    :hide:

    >>> index = pd.date_range('1/1/2016', periods=3, freq='s')
    >>> data = [[1,2,3],[4,5,6],[7,8,9]]
    >>> df = pd.DataFrame(data=data, index=index, columns=['A', 'B', 'C'])

.. doctest::

    >>> pm.add_dataframe(df)

DataFrames are accessed using

.. doctest::

    >>> pm.df #doctest:+SKIP 

Multiple DataFrames can be added to the PerformanceMonitoring object.  
New data overrides existing data if DataFrames share indexes and columns.  
Missing indexes and columns are filled with NaN.  An example is shown below.

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import numpy as np
    >>> import pecos
    >>> index1 = pd.date_range('1/1/2018', periods=3, freq='D')
    >>> data1 = {'A': np.arange(3), 'B': np.arange(3)+5}
    >>> df1 = pd.DataFrame(data1, index=index1)
    >>> index2 = pd.date_range('1/2/2018', periods=3, freq='D')
    >>> data2 = {'B': np.arange(3), 'C': np.arange(3)+5}
    >>> df2 = pd.DataFrame(data2, index=index2)
    >>> pm = pecos.monitoring.PerformanceMonitoring()

.. doctest::

    >>> print(df1)
                A  B
    2018-01-01  0  5
    2018-01-02  1  6
    2018-01-03  2  7
	
    >>> print(df2)
                B  C
    2018-01-02  0  5
    2018-01-03  1  6
    2018-01-04  2  7
	
    >>> pm.add_dataframe(df1)
    >>> pm.add_dataframe(df2)
    >>> print(pm.df)
                  A    B    C
    2018-01-01  0.0  5.0  NaN
    2018-01-02  1.0  0.0  5.0
    2018-01-03  2.0  1.0  6.0
    2018-01-04  NaN  2.0  7.0
	
	
To use Pecos' functions suite, simply create or edit the data into a pandas dataframe. 
For some functions to work properly, the dataframe index will need to be converted
into the 'DateTime' format.
