Translation dictionary
-----------------------
A translation dictionary is an optional feature which allows the user to map original 
column names into common names that can be more useful for analysis and reporting. 
A translation dictionary can also be used to group columns with similar 
properties into a single variable.  
Using grouped variables, Pecos can run a single set of quality control tests on the group.

Each entry in a translation dictionary is a key:value pair where 
'key' is the common name of the data and 'value' is a list of original column names in the DataFrame.  
For example, {temp: [temp1,temp2]} means that columns named 'temp1' and 'temp2' in the 
DataFrame are assigned to the common name 'temp' in Pecos.
In the :ref:`simple_example`, the following translation dictionary is used to 
group columns 'C' and 'D' to 'Wave'.

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

    >>> trans = {'Wave': ['C','D']}

The translation dictionary can then be added to the PerformanceMonitoring object.

.. doctest::

    >>> pm.add_translation_dictionary(trans)

As with DataFrames, multiple translation dictionaries can be added to the 
PerformanceMonitoring object. 
New dictionaries override existing keys in the translation dictionary.  

Keys defined in the translation dictionary can be used in quality control tests,
for example,

.. doctest::

    >>> pm.check_range([-1,1], 'Wave')

runs a check range test on columns 'C' and 'D'.

Inside Pecos, the translation dictionary is used to index into the DataFrame, for example,

.. doctest::

    >>> pm.data[pm.trans['Wave']] #doctest:+SKIP 

returns columns 'C' and 'D' from the DataFrame.

