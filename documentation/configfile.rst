Configuration file
==================

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

In the configuration file, composite signals and time filters can be defined 
using strings of Python code. 
Numpy (and other Python modules if needed) can be used for computation.  
**Strings of Python code should be thoroughly tested by the user.**  
A list of key:value pairs can be used to specify the order of evaluation.

When using a string of Python code, keywords in {} are expanded using the following rules in this order:

1. Keywords ELAPSED_TIME and CLOCK_TIME return time in seconds

2. Keywords that are a key in the translation dictionary return 'pm.df[pm.trans[Keyword]]'

3. Keywords that are a key in a user specified dictionary of constants, specs, return 'specs[Keyword]'.
   
The configuration file can also be used to store constants that are used to
generate a time filter, 
define upper and lower bounds in quality control tests, 
define system location, 
or other input needed in composite signals, for example,
	
.. doctest::

    >>> specs = {'Frequency': 900, 'Multiplier': 10, 'Latitude': 35.05, 'Longitude': -106.53}

Strings are evaluated and added to the DataFrame using the following code,

.. doctest::

    >>> signal = pm.evaluate_string('Signal', string, specs) #doctest:+SKIP 
    >>> pm.add_dataframe(signal) #doctest:+SKIP 
	
If the string evaluation fails, the error message is printed.  
See the :class:`~pecos.monitoring.PerformanceMonitoring.evaluate_string` 
for more details.
