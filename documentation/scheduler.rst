Task scheduler 
===============

To run Pecos on an automated schedule, create a task using your operating systems.  
On Windows, open the Control Panel and search for *Schedule Tasks*.
On Linux and OSX, use the *cron* utility.  

Tasks are defined by a trigger and an action.  
The trigger indicates when the task should be run (i.e. Daily at 1:00 pm).
The action can be set to run a batch file.
A batch file (.bat or .cmd filename extension) can be easily 
written to start a Python script which runs Pecos.  
For example, the following batch file runs driver.py::

	cd your_working_directory
	C:\Users\username\Anaconda3\python.exe driver.py
