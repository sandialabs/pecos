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

For some use cases, it is convenient to use strings of Python code in 
a configuration file to define time filters, 
quality control bounds, and composite signals.
These strings can be evaluated using :class:`~pecos.utils.evaluate_string`.
**WARNING this function calls ``eval``. Strings of Python code should be 
thoroughly tested by the user.**

For each {keyword} in the string, {keyword} is expanded in the following order:
    
* If keyword is ELAPSED_TIME, CLOCK_TIME or EPOCH_TIME then data.index is 
  converted to seconds (elapsed time, clock time, or epoch time) is used in the evaluation
* If keyword is used to select a column (or columns) of data, then data[keyword] 
  is used in the evaluation
* If a translation dictionary is used to select a column (or columns) of data, then 
  data[trans[keyword]] is used in the evaluation
* If the keyword is a key in a dictionary of constants (specs), then 
  specs[keyword] is used in the evaluation
      
For example, the time filter string is evaluated below.

.. doctest::
    :hide:

    >>> import pandas as pd
    >>> import numpy as np
    >>> import pecos
    >>> index = pd.date_range('1/1/2015', periods=96, freq='15Min')
    >>> data = {'A': np.random.rand(96), 'B': np.random.rand(96)}
    >>> df = pd.DataFrame(data, index=index)
    
.. doctest::

    >>> string_to_eval = "({CLOCK_TIME} > 3*3600) & ({CLOCK_TIME} < 21*3600)"
    >>> time_filter = pecos.utils.evaluate_string(string_to_eval, df)
