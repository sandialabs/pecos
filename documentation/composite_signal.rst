Composite signals
==================

Composite signals are defined as data generated from existing data or from models.  
Composite signals can be used to add modeled data values or relationships between 
data columns to quality control tests.  

Python facilitates a wide range of analysis options that can be incorporated into 
Pecos using composite signals.  For example, composite signals can be created 
using the following methods available in open source Python packages 
(e.g., `numpy`, `scipy`, `pandas`, `scikit-learn`, `tensorflow`):

* Logic/comparison
* Interpolation
* Filtering
* Rolling window statistics
* Regression
* Classification
* Clustering
* Machine learning

Pecos can also interface with analysis run outside Python using the Python 
package `subprocess`.

Once a composite signal is created, it can be used directly within a quality control
test, or compared to existing data and the residual can be used in a quality control
test.

In the :ref:`simple_example`, a very simple 'Wave Model' composite signal is added to 
the PerformanceMonitoring object.

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
    >>> wave_model = pd.DataFrame(np.sin(10*(clocktime/86400)), 
    ...                           index=pm.data.index, columns=['Wave Model'])
    >>> pm.add_dataframe(wave_model)
