Custom applications
====================

While Pecos was initially developed to monitor photovoltaic systems, it is designed to be used for a wide range of applications. The ability to run the analysis within the Python environment enables the use of diverse analysis options that can be incorporated into Pecos, including application specific models.  The software has been used to monitor energy systems in support of several Department of Energy projects, as described below.

Photovoltaic systems
---------------------

Pecos was originally developed at Sandia National Laboratories in 2016 to monitor photovoltaic (PV) systems as part of the 
`Department of Energy Regional Test Centers <https://www.energy.gov/eere/solar/regional-test-centers-solar-technologies>`_.
Pecos is used to run daily analysis on data collected at several sites across the US.
For PV systems, the translation dictionary can be used to group data
according to the system architecture, which can include multiple strings and modules.
The time filter can be defined based on sun position and system location.
The data objects used in Pecos are compatible with `PVLIB <http://pvlib-python.readthedocs.io/>`_, which can be used to model PV 
systems [SHFH16]_.
Pecos also includes functions to compute PV specific metrics (i.e. insolation, 
performance ratio, clearness index) in the :class:`~pecos.pv` module.
The International Electrotechnical Commission (IEC) has developed guidance to measure 
and analyze energy production from PV systems. 
Klise et al. [KlSC17]_ describe an application of IEC 61724-3, using 
Pecos and PVLIB.
Pecos includes a PV system example in the `examples/pv <https://github.com/sandialabs/pecos/tree/master/examples/pv>`_ directory.  

Marine renewable energy systems
--------------------------------

In partnership with National Renewable Energy Laboratory (NREL) and Pacific Northwest National Laboratory (PNNL), Pecos was integrated into the `Marine and Hydrokinetic Toolkit (MHKiT) <https://mhkit-code-hub.github.io/MHKiT/>`_ to support research funded by the Department of Energy’s Water Power Technologies Office.  MHKiT provides provides the marine renewable energy (MRE) community with tools for data quality control, resource assessment, and device performance which adhere to the International Electrotechnical Commission (IEC) Technical Committee’s, IEC TC 114. Pecos provides a quality control analysis on data collected from
MRE systems including wave, tidal, and river systems.  

Fossil energy systems 
-----------------------

In partnership with National Energy Technology Laboratory (NETL), Pecos was extended to demonstrate real-time monitoring of coal-fired power plants in support of the Department of Energy's `Institute for the Design of Advanced Energy Systems (IDAES) <https://idaes.org/>`_.
As part of this demonstration, streaming algorithms were added to Pecos to facilitate near real-time analysis using continuous data streams. 


