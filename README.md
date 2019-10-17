# epparse
Python module for reading and visualization EnergyPlus SQL files for both tabular and time-series/hourly results.

Sifting through EnergyPlus output files to find specific reports can be a daunting and time-intensive task. By querying the SQLite Output of a simulation, it becomes much simpler to quickly obtain Hourly, Timestep, and Tabular reports.

This module provides a Python api to achieve this goal and relies heavily on Pandas DataFrames as well as Plotly's Python api for visualization.


Note: In order to use this module, the 'eplusout.sql' and 'eplusout.bnd' files should be located in the same folder. The bnd file is used mainly for converting SI volumetric flow rates to imperial units based on fluid type (water is gpm, air is cfm)

The SQLite file must be requested in the IDF file using the 'SimpleAndTabular' argument:

'Output:SQLite, SimpleAndTabular;'


Usage Example: 

Download or Clone from GitHub and place in a folder labeled 'epparse'

import sys
epparse_location = 'c:/epparse'
sys.path.append(epparse_location)

import epparse as ep


pathtosim = 'C:/simfiles/eplusout' # do not include extensions
mysim = ep.load.epLoad(pathtosim)


# Output Tables
to find tables: This returns a list of DataFrames that meet the search criteria.
mysim.search_tabular('Setpoint Not Met')

to find a list of all tables: 
available_tables = mysim.tables.avail_tabular()


to get a specific table in DataFrame format, pass a single row from the 'avail_tabular()'-generated DataFrame:
ref = available_tables[available_tables.TableName == 'Site and Source Energy']
siteandsource = mysim.tables.get_tabular(ref)


# Hourly / Timestep Reports

availseries = mysim.sql.availseries()
this returns a list of all available hourly reports, which can be filtered:


filtered = mysim[mysim.KeyValue.str.contains("BLOCK5:ZONE19"]

Now we have a DataFrame showing all reports for "BLOCK5:ZONE19". To pull the reports into a DataFrame:

mydf = mysim.sql.getseries(filtered) # units are 'IP' by default but can be specified as 'SI'

# Plotting Hourly Data:

epparse includes a convenience module called 'dfplot', which provides access to Plotly Multiline, Scatter, Heatmap, Surface, and other plots. These can be used inside a Jupyter Notebook or any other interface that supports Plotly. To use this, call 'ep.dfplot.charttype()':

ep.dfplot.line(mydf)
ep.dfplot.heatmap(mydf, 1) # 1 is the column index

There are a number of ways to customize these Plots; calling help(ep.dfplot.heatmap), for example, will show customizable options.














