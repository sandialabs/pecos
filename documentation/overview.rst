Overview
================

Pecos is an open-source Python package designed to monitor performance of time series data, 
subject to a series of quality control tests.  
The software includes methods to 
run quality control tests defined by the user
and generate reports which include performance metrics, test results, and graphics.
The software can be customized for specific applications. 
Some high-level features include:

* Pecos uses Pandas DataFrames [Mcki13]_ to store and analyze time series data.  This dependency 
  facilitates a wide range of analysis options and date-time functionality.

* Data column names can be easily reassigned to common names through the use of a
  translation dictionary.  Translation dictionaries also allow data columns to
  be grouped for analysis.

* Time filters can be used to eliminate data at specific times from quality 
  control tests (i.e. early evening and late afternoon).  

* Predefined and custom quality control functions can be used to determine if data is anomalous.

* Application specific models can be incorporated into quality control tests 
  to compare measured to modeled data values.

* General and custom performance metrics can be saved to keep a  
  running history of system health. 

* Analysis can be set up to run on an automated schedule (i.e. Pecos can be 
  run each day to analyze data collected on the previous day). 
  
* HTML formatted reports can be sent via email or hosted on a website.  LaTeX formatted reports can also be generated.

* Data acquisition methods can be used to transfer data from sensors to an SQL database. 