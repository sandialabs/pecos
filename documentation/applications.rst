Custom applications
====================

Pecos can be customized for specific applications.  Python scripts can be added 
to initialize data and add application specific models.  Additional quality control tests 
can be added by inheriting from the PerformanceMonitoring class.

PV system monitoring
---------------------
Pecos was originally developed to monitor photovoltaic (PV) systems as part of the 
`Department of Energy Regional Test Centers <https://www.energy.gov/eere/solar/regional-test-centers-solar-technologies>`_.
Pecos is used to run daily analysis on data collected at several sites across the US.
For PV systems, the translation dictionary can be used to group data
according to the system architecture, which can include multiple strings and modules.
The time filter can be defined based on sun position and system location.
The data objects used in Pecos are compatible with PVLIB, which can be used to model PV 
systems [SHFH16]_ (http://pvlib-python.readthedocs.io/).
Pecos also includes functions to compute PV specific metrics (i.e. insolation, 
performance ratio, clearness index) in the :class:`~pecos.pv` module.
The International Electrotechnical Commission (IEC) has developed guidance to measure 
and analyze energy production from PV systems. 
[KlSC17]_ describes an application of the standards outlined in IEC 61724-3, using 
Pecos and PVLIB.
Pecos includes a PV system example in the `examples/pv <https://github.com/sandialabs/pecos/tree/master/examples/pv>`_ directory.  

Performance metrics
---------------------
Pecos is typically used to run a series of quality control tests on data collected 
over a set time interval (i.e. hourly, daily, weekly).
The metrics that are generated from each analysis can be used in additional 
quality control analysis to track long term performance and system health (i.e. yearly summary reports).
Pecos includes a performance metrics example (based on one year of PV metrics)
in the `examples/metrics <https://github.com/sandialabs/pecos/tree/master/examples/metrics>`_ directory.
