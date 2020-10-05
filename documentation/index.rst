.. figure:: figures/logo.png
   :scale: 75 %
   :alt: Logo
   
Performance Monitoring using Pecos
================================================================

Advances in sensor technology have rapidly increased our ability to monitor 
natural and human-made physical systems.  
In many cases, it is critical to process the resulting large volumes of data on a regular schedule
and alert system operators when the system has changed.
Automated quality control and performance monitoring can allow system 
operators to quickly detect performance issues.  

Pecos is an open source Python package designed to address this need.  
Pecos includes built-in functionality to monitor performance of time series data.  
The software can be used to automate a series of quality control 
tests and generate custom reports which include performance metrics, 
test results, and graphics.  The software was developed specifically to monitor 
solar photovoltaic systems, but is designed to be used for a 
wide range of applications. 
:numref:`fig-index` shows example graphics and dashboard created using Pecos.

.. _fig-index:
.. figure:: figures/index.png
   :width: 100 %
   :alt: Sample-graphics
   
   Example graphics and dashboard created using Pecos.
   
Citing Pecos
--------------
To cite Pecos, use one of the following references:

* K.A. Klise and J.S. Stein (2016), Performance Monitoring using Pecos, Technical Report SAND2016-3583, Sandia National Laboratories, Albuquerque, NM.
* K.A. Klise and J.S. Stein (2016), Automated Performance Monitoring for PV Systems using Pecos, 43rd IEEE Photovoltaic Specialists Conference (PVSC), Portland, OR, June 5-10. `pdf <http://www.pvsc-proceedings.org./download.php?year=2016&file=907>`_

Contents
------------
.. toctree::
   :maxdepth: 1
	
   overview
   installation
   framework
   example
   timeseries
   translation
   timefilter
   qc_tests
   metrics
   composite_signal
   results
   automation
   applications
   license
   whatsnew
   developers
   API documentation <apidoc/pecos>
   reference

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Sandia National Laboratories is a multimission laboratory managed and operated by National Technology and 
Engineering Solutions of Sandia, LLC., a wholly owned subsidiary of Honeywell International, Inc., for the 
U.S. Department of Energy's National Nuclear Security Administration under contract DE-NA-0003525.

