Installation
======================================

Pecos requires Python (tested on 3.9, 3.10, 3.11, and 3.12) along with several Python 
package dependencies.  Information on installing and using Python can be found at 
https://www.python.org/.  Python distributions, such as Anaconda,
are recommended to manage the Python interface.  
Anaconda Python distributions include the Python packages needed to run Pecos.

Users can install the latest release of Pecos from PyPI or Anaconda using one of the following commands.

* PyPI |pypi version|_ |pypi downloads|_ ::

	pip install pecos 

* Anaconda |anaconda version|_ |anaconda downloads|_ ::

	conda install -c conda-forge pecos
	
.. |pypi version| image:: https://img.shields.io/pypi/v/pecos.svg?maxAge=3600
.. _pypi version: https://pypi.org/project/pecos/
.. |pypi downloads| image:: https://pepy.tech/badge/pecos
.. _pypi downloads: https://pepy.tech/project/pecos
.. |anaconda version| image:: https://anaconda.org/conda-forge/pecos/badges/version.svg 
.. _anaconda version: https://anaconda.org/conda-forge/pecos
.. |anaconda downloads| image:: https://anaconda.org/conda-forge/pecos/badges/downloads.svg
.. _anaconda downloads: https://anaconda.org/conda-forge/pecos

Developers can install the main branch of Pecos from the GitHub repository using the following commands::

	git clone https://github.com/sandialabs/pecos
	cd pecos
	python setup.py install

To install Pecos using a downloaded zip file, go to https://github.com/sandialabs/pecos, 
select the "Clone or download" button and then select "Download ZIP".
This downloads a zip file called pecos-main.zip.
To download a specific release, go to https://github.com/sandialabs/pecos/releases and select a zip file.
The software can then be installed by unzipping the file and running setup.py::

	unzip pecos-main.zip
	cd pecos-main
	python setup.py install

To use Pecos, import the package from a Python console::

	import pecos	
	
Dependencies
------------

Required Python package dependencies include:

* Pandas :cite:p:`pandas`: used to analyze and store time series data, 
  http://pandas.pydata.org/
* Numpy :cite:p:`numpy`: used to support large, multi-dimensional arrays and matrices, 
  http://www.numpy.org/
* Jinja :cite:p:`jinja`: used to generate HTML templates, 
  https://jinja.palletsprojects.com/
* Matplotlib :cite:p:`matplotlib`: used to produce figures, 
  http://matplotlib.org/
* Setuptools :cite:p:`setuptools`: used to install the pecos package, https://setuptools.pypa.io/

Optional Python packages dependencies include:

* minimalmodbus :cite:p:`minimalmodbus`: used to collect data from a modbus device, 
  https://minimalmodbus.readthedocs.io
* sqlalchemy :cite:p:`sqlalchemy`: used to insert data into a MySQL database,
  https://www.sqlalchemy.org/
* pyyaml :cite:p:`pyyaml`: used to store configuration options in human readable data format,
  http://pyyaml.org/
* PVLIB :cite:p:`pvlib`: used to simulate the performance of photovoltaic energy systems,
  http://pvlib-python.readthedocs.io/
* Plotly :cite:p:`plotly`: used to produce interactive scalable figures, 
  https://plot.ly/

All other dependencies are part of the Python Standard Library.

